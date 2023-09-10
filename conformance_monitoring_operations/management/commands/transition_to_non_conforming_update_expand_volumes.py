from django.core.management.base import BaseCommand, CommandError
from os import environ as env
from common.database_operations import BlenderDatabaseReader
from common.data_definitions import OPERATION_STATES
import arrow
from scd_operations.scd_data_definitions import (
    Time,
    OperationalIntentReferenceDSSResponse,
)
from auth_helper.common import get_redis
import json
from datetime import timedelta
from dotenv import load_dotenv, find_dotenv
import logging
from scd_operations.dss_scd_helper import SCDOperations

load_dotenv(find_dotenv())
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger("django")


class Command(BaseCommand):
    help = "This command takes in a flight declaration: and A) declares it as non-conforming, B) creates off-nominal volumes C) Updates the DSS with the new status D) Notifies Peer USS "

    def add_arguments(self, parser):
        parser.add_argument(
            "-d",
            "--flight_declaration_id",
            dest="flight_declaration_id",
            metavar="ID of the flight declaration",
            help="Specify the ID of Flight Declaration",
        )

        parser.add_argument(
            "-d",
            "--dryrun",
            dest="dryrun",
            metavar="Set if this is a dry run",
            default="1",
            help="Set if it is a dry run",
        )

    def handle(self, *args, **options):
        # This command declares an operation as non-conforming and updates the state to the DSS (and notifies subscribers)
        my_database_reader = BlenderDatabaseReader()
        dry_run = options["dry_run"]

        dry_run = 1 if dry_run == "1" else 0

        # Set new state as non-conforming
        new_state = OPERATION_STATES[3][1]
        try:
            flight_declaration_id = options["flight_declaration_id"]
        except Exception as e:
            raise CommandError(
                "Incomplete command, Flight Declaration ID not provided %s" % e
            )
        # Get the flight declaration
        flight_declaration = my_database_reader.get_flight_declaration_by_id(
            flight_declaration_id=flight_declaration_id
        )
        if not flight_declaration:
            raise CommandError(
                "Flight Declaration with ID {flight_declaration_id} does not exist".format(
                    flight_declaration_id=flight_declaration_id
                )
            )

        my_scd_dss_helper = SCDOperations()
        my_database_reader = BlenderDatabaseReader()
        now = arrow.now().isoformat()

        try:
            flight_declaration_id = options["flight_declaration_id"]
        except Exception as e:
            raise CommandError(
                "Incomplete command, Flight Declaration ID not provided %s" % e
            )

        flight_declaration = my_database_reader.get_flight_declaration_by_id(
            flight_declaration_id=flight_declaration_id
        )
        if not flight_declaration:
            raise CommandError(
                "Flight Declaration with ID {flight_declaration_id} does not exist".format(
                    flight_declaration_id=flight_declaration_id
                )
            )
        flight_authorization = (
            my_database_reader.get_flight_authorization_by_flight_declaration_obj(
                flight_declaration=flight_declaration
            )
        )
        dss_operational_intent_ref_id = flight_authorization.dss_operational_intent_id

        r = get_redis()

        flight_opint = "flight_opint." + str(flight_declaration_id)
        # Update the volume to create a new volume

        if r.exists(flight_opint):
            op_int_details_raw = r.get(flight_opint)
            op_int_details = json.loads(op_int_details_raw)

            reference_full = op_int_details["success_response"][
                "operational_intent_reference"
            ]
            dss_response_subscribers = op_int_details["success_response"]["subscribers"]
            details_full = op_int_details["operational_intent_details"]
            # Load existing opint details

            stored_operational_intent_id = reference_full["id"]
            stored_manager = reference_full["manager"]
            stored_uss_availability = reference_full["uss_availability"]
            stored_version = reference_full["version"]
            stored_state = reference_full["state"]
            stored_ovn = reference_full["ovn"]
            stored_uss_base_url = reference_full["uss_base_url"]
            stored_subscription_id = reference_full["subscription_id"]

            stored_time_start = Time(
                format=reference_full["time_start"]["format"],
                value=reference_full["time_start"]["value"],
            )
            stored_time_end = Time(
                format=reference_full["time_end"]["format"],
                value=reference_full["time_end"]["value"],
            )

            stored_volumes = details_full["volumes"]
            stored_priority = details_full["priority"]
            stored_off_nominal_volumes = details_full["off_nominal_volumes"]

            reference = OperationalIntentReferenceDSSResponse(
                id=stored_operational_intent_id,
                manager=stored_manager,
                uss_availability=stored_uss_availability,
                version=stored_version,
                state=stored_state,
                ovn=stored_ovn,
                time_start=stored_time_start,
                time_end=stored_time_end,
                uss_base_url=stored_uss_base_url,
                subscription_id=stored_subscription_id,
            )

            if not dry_run:
                blender_base_url = env.get("BLENDER_FQDN", 0)
                for subscriber in dss_response_subscribers:
                    subscriptions = subscriber["subscriptions"]
                    uss_base_url = subscriber["uss_base_url"]
                    if blender_base_url == uss_base_url:
                        for s in subscriptions:
                            subscription_id = s["subscription_id"]
                            break
                # Create a new subscription to the airspace
                operational_update_response = (
                    my_scd_dss_helper.update_specified_operational_intent_reference(
                        subscription_id=subscription_id,
                        operational_intent_ref_id=reference.id,
                        extents=stored_volumes,
                        new_state=str(new_state),
                        ovn=reference.ovn,
                        deconfliction_check=False,
                    )
                )

                ## Update / expand volume
                stream_ops = flight_stream_helper.StreamHelperOps()
                push_cg = stream_ops.push_cg()
                obs_helper = flight_stream_helper.ObservationReadOperations()
                all_flights_rid_data = obs_helper.get_observations(push_cg)
                # Get the last observation of the flight telemetry
                unique_flights = []
                # Keep only the latest message
                try:
                    for message in all_flights_rid_data:
                        unique_flights.append(
                            {
                                "timestamp": message.timestamp,
                                "seq": message.sequence,
                                "msg_data": message.data,
                                "address": message.data["icao_address"],
                            }
                        )
                    # sort by date
                    unique_flights.sort(
                        key=lambda item: item["timestamp"], reverse=True
                    )
                    # Keep only the latest message
                    distinct_messages = {
                        i["address"]: i for i in reversed(unique_flights)
                    }.values()
                    relevant_observation = {}
                    for index, rid_observation in enumerate(distinct_messages):
                        if rid_observation.get("icao_address") == flight_declaration_id:
                            relevant_observation = rid_observation

                            break
                except KeyError as ke:
                    logger.error(
                        "Error in sorting distinct messages, ICAO name not defined %s"
                        % ke
                    )
                    distinct_messages = []

                lat_dd = rid_observation["lat_dd"]
                lon_dd = rid_observation["lon_dd"]
                rid_location = Point(lon_dd, lat_dd)
                # check if it is within declared bounds
                # TODO: This code is same as the C7check in the conformance / utils file. Need to refactor
                all_volumes = flight_declaration.operational_intent["volumes"]

                all_polygon_altitudes: List[PolygonAltitude] = []

                rid_obs_within_all_volumes = []
                for v in all_volumes:
                    v4d = from_dict(data_class=Volume4D, data=v)
                    altitude_lower = v4d.altitude_lower.value
                    altitude_upper = v4d.altitude_upper.value
                    outline_polygon = v4d.volume.outline_polygon
                    point_list = []
                    for vertex in outline_polygon["vertices"]:
                        p = Point(vertex["lng"], vertex["lat"])
                        point_list.append(p)
                    outline_polygon = Polygon([[p.x, p.y] for p in point_list])
                    pa = PolygonAltitude(
                        polygon=outline_polygon,
                        altitude_upper=altitude_upper,
                        altitude_lower=altitude_lower,
                    )
                    all_polygon_altitudes.append(pa)

                for p in all_polygon_altitudes:
                    is_within = rid_location.within(p.polygon)
                    rid_obs_within_all_volumes.append(is_within)

                aircraft_bounds_conformant = any(rid_obs_within_all_volumes)

                if (
                    aircraft_bounds_conformant
                ):  # Operator declares contingency, but the aircraft is within bounds, no need to update / change bounds
                    pass

                else:
                    # aircraft declares contingency when the aircraft is out of bounds

                    my_op_int_converter = OperationalIntentsConverter()
                    newv4D = my_op_int_converter.buffer_point_to_volume4d(
                        lat=lat_dd,
                        lon_dd=lon_dd,
                        start_datetime=flight_declaration.start_datetime,
                        end_datetime=flight_declaration.end_datetime,
                    )

                    r = get_redis()

                    flight_opint = "flight_opint." + str(flight_declaration_id)

                    if r.exists(flight_opint):
                        op_int_details_raw = r.get(flight_opint)
                        op_int_details = json.loads(op_int_details_raw)

                        reference_full = op_int_details["success_response"][
                            "operational_intent_reference"
                        ]
                        dss_response_subscribers = op_int_details["success_response"][
                            "subscribers"
                        ]
                        details_full = op_int_details["operational_intent_details"]
                        # Load existing opint details

                        stored_operational_intent_id = reference_full["id"]
                        stored_manager = reference_full["manager"]
                        stored_uss_availability = reference_full["uss_availability"]
                        stored_version = reference_full["version"]
                        stored_state = reference_full["state"]
                        stored_ovn = reference_full["ovn"]
                        stored_uss_base_url = reference_full["uss_base_url"]
                        stored_subscription_id = reference_full["subscription_id"]

                        stored_time_start = Time(
                            format=reference_full["time_start"]["format"],
                            value=reference_full["time_start"]["value"],
                        )
                        stored_time_end = Time(
                            format=reference_full["time_end"]["format"],
                            value=reference_full["time_end"]["value"],
                        )

                        stored_volumes = details_full["volumes"]
                        stored_priority = details_full["priority"]
                        stored_off_nominal_volumes = details_full["off_nominal_volumes"]

                        reference = OperationalIntentReferenceDSSResponse(
                            id=stored_operational_intent_id,
                            manager=stored_manager,
                            uss_availability=stored_uss_availability,
                            version=stored_version,
                            state=stored_state,
                            ovn=stored_ovn,
                            time_start=stored_time_start,
                            time_end=stored_time_end,
                            uss_base_url=stored_uss_base_url,
                            subscription_id=stored_subscription_id,
                        )

                    if not dry_run:
                        blender_base_url = env.get("BLENDER_FQDN", 0)
                        for subscriber in dss_response_subscribers:
                            subscriptions = subscriber["subscriptions"]
                            uss_base_url = subscriber["uss_base_url"]
                            if blender_base_url == uss_base_url:
                                for s in subscriptions:
                                    subscription_id = s["subscription_id"]
                                    break
                        # Create a new subscription to the airspace

                        operational_update_response = my_scd_dss_helper.update_specified_operational_intent_reference(
                            subscription_id=subscription_id,
                            operational_intent_ref_id=reference.id,
                            extents=stored_volumes,
                            new_state="Contingent",
                            ovn=reference.ovn,
                            deconfliction_check=True,
                        )

                        if operational_update_response.status == 200:
                            logger.info(
                                "Successfully updated operational intent status for {operational_intent_id} on the DSS".format(
                                    operational_intent_id=stored_operational_intent_id
                                )
                            )
                        else:
                            logger.info(
                                "Error in updating operational intent on the DSS"
                            )

                    else:
                        logger.info("Dry run, not submitting to the DSS")

                # Update the volume

                ## Send the new volume to DSS

                # Notify others
