import logging
from os import environ as env
from typing import List

from dacite import from_dict
from django.core.management.base import BaseCommand, CommandError
from dotenv import find_dotenv, load_dotenv
from shapely.geometry import Point

from auth_helper.common import get_redis
from common.data_definitions import FLIGHT_OPINT_KEY, OPERATION_STATES
from common.database_operations import BlenderDatabaseReader
from conformance_monitoring_operations.data_definitions import PolygonAltitude
from flight_declaration_operations.utils import OperationalIntentsConverter
from flight_feed_operations import flight_stream_helper
from scd_operations.dss_scd_helper import (
    OperationalIntentReferenceHelper,
    SCDOperations,
)
from scd_operations.scd_data_definitions import Polygon, Volume4D

load_dotenv(find_dotenv())

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger("django")


class Command(BaseCommand):
    help = "This command clears the operation in the DSS after the state has been set to ended."

    def add_arguments(self, parser):
        parser.add_argument(
            "-o",
            "--flight_declaration_id",
            dest="flight_declaration_id",
            metavar="ID of the flight declaration",
            help="Specify the ID of Flight Declaration",
        )

        parser.add_argument(
            "-d",
            "--dry_run",
            dest="dry_run",
            metavar="Set if this is a dry run",
            default="1",
            help="Set if it is a dry run",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        blender_base_url = env.get("BLENDER_FQDN", 0)

        dry_run = 1 if dry_run == "1" else 0
        contingent_state = 4
        contingent_state_str = OPERATION_STATES[contingent_state][1]

        my_scd_dss_helper = SCDOperations()
        my_database_reader = BlenderDatabaseReader()
        my_operational_intent_parser = OperationalIntentReferenceHelper()
        stream_ops = flight_stream_helper.StreamHelperOps()
        obs_helper = flight_stream_helper.ObservationReadOperations()
        r = get_redis()

        flight_declaration_id = options["flight_declaration_id"]
        if not flight_declaration_id:
            raise CommandError("Incomplete command, Flight Declaration ID not provided")

        flight_opint = FLIGHT_OPINT_KEY + str(flight_declaration_id)
        flight_declaration = my_database_reader.get_flight_declaration_by_id(flight_declaration_id=flight_declaration_id)
        if not flight_declaration:
            raise CommandError(
                "Flight Declaration with ID: {flight_declaration_id} does not exist".format(flight_declaration_id=flight_declaration_id)
            )
        current_state = flight_declaration.state
        current_state_str = OPERATION_STATES[current_state][1]

        # Update the volume to create a new off-nominal volume
        if not r.exists(flight_opint):
            raise CommandError(
                "Flight Declaration with ID {flight_declaration_id} does not exist in the cached database".format(
                    flight_declaration_id=flight_declaration_id
                )
            )
        existing_op_int_details = my_operational_intent_parser.parse_stored_operational_intent_details(operation_id=flight_declaration_id)
        reference_full = existing_op_int_details.success_response.operational_intent_reference
        details_full = existing_op_int_details.operational_intent_details
        dss_response_subscribers = existing_op_int_details.success_response.subscribers

        stored_volumes = details_full.volumes

        if dry_run:
            logger.info(
                "Operator declares contingency for operation {flight_declaration_id} activated in dry_run mode".format(
                    flight_declaration_id=flight_declaration_id
                )
            )

        else:
            ## Update / expand volume
            push_cg = stream_ops.push_cg()
            all_flights_rid_data = obs_helper.get_observations(push_cg)
            # Get the last observation of the flight telemetry
            unique_flights = []
            relevant_observation = {}
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
                unique_flights.sort(key=lambda item: item["timestamp"], reverse=True)
                # Keep only the latest message
                distinct_messages = {i["address"]: i for i in reversed(unique_flights)}.values()
                for index, rid_observation in enumerate(distinct_messages):
                    if rid_observation.get("icao_address") == flight_declaration_id:
                        relevant_observation = rid_observation

                        break
            except KeyError as ke:
                logger.error("Error in sorting distinct messages, ICAO name not defined %s" % ke)
                distinct_messages = []

            lat_dd = relevant_observation["lat_dd"]
            lon_dd = relevant_observation["lon_dd"]
            rid_location = Point(lon_dd, lat_dd)
            # check if it is within declared bounds
            # TODO: This code is same as the C7check in the conformance / utils file. Need to refactor
            declared_volumes = flight_declaration.operational_intent["volumes"]
            all_polygon_altitudes: List[PolygonAltitude] = []

            rid_obs_within_all_volumes = []
            all_altitudes = []
            for v in declared_volumes:
                v4d = from_dict(data_class=Volume4D, data=v)
                altitude_lower = v4d.altitude_lower.value
                altitude_upper = v4d.altitude_upper.value
                all_altitudes.append(altitude_lower)
                all_altitudes.append(altitude_upper)
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
            if aircraft_bounds_conformant:  # Operator declares contingency, but the aircraft is within bounds, no need to update / change bounds
                nominal_or_off_nominal_volumes = stored_volumes

            else:
                max_altitude = max(all_altitudes)
                min_altitude = min(all_altitudes)
                # aircraft declares contingency when the aircraft is out of bounds
                my_op_int_converter = OperationalIntentsConverter()
                nominal_or_off_nominal_volumes = my_op_int_converter.buffer_point_to_volume4d(
                    lat=lat_dd,
                    lng=lon_dd,
                    start_datetime=flight_declaration.start_datetime,
                    end_datetime=flight_declaration.end_datetime,
                    min_altitude=min_altitude,
                    max_altitude=max_altitude,
                )
                logger.debug(nominal_or_off_nominal_volumes)

                if not dry_run:
                    blender_base_url = env.get("BLENDER_FQDN", 0)
                    for subscriber in dss_response_subscribers:
                        subscriptions = subscriber.subscriptions
                        uss_base_url = subscriber.uss_base_url
                        if blender_base_url == uss_base_url:
                            for s in subscriptions:
                                subscription_id = s.subscription_id
                                break

                    operational_update_response = my_scd_dss_helper.update_specified_operational_intent_reference(
                        subscription_id=subscription_id,
                        operational_intent_ref_id=reference_full.id,
                        extents=nominal_or_off_nominal_volumes,
                        current_state=current_state_str,
                        new_state=contingent_state_str,
                        ovn=reference_full.ovn,
                        deconfliction_check=True,
                    )

                    if operational_update_response.status == 200:
                        logger.info(
                            "Successfully updated operational intent status for {operational_intent_id} on the DSS".format(
                                operational_intent_id=flight_declaration_id
                            )
                        )
                        # TODO Notify subscribers
                    else:
                        logger.info("Error in updating operational intent on the DSS")

                else:
                    logger.info("Dry run, not submitting to the DSS")
