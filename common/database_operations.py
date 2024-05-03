import json
import logging
import os
from dataclasses import asdict
from typing import List, Tuple, Union
from uuid import uuid4

import arrow
from django.db.utils import IntegrityError
from dotenv import find_dotenv, load_dotenv

from conformance_monitoring_operations.models import TaskScheduler
from flight_declaration_operations.models import FlightAuthorization, FlightDeclaration
from scd_operations.data_definitions import FlightDeclarationCreationPayload
from scd_operations.scd_data_definitions import PartialCreateOperationalIntentReference

logger = logging.getLogger("django")

load_dotenv(find_dotenv())

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)


class BlenderDatabaseReader:
    """
    A file to unify read and write operations to the database. Eventually caching etc. can be added via this file
    """

    def get_all_flight_declarations(self) -> Union[None, List[FlightDeclaration]]:
        flight_declarations = FlightDeclaration.objects.all()
        return flight_declarations

    def check_flight_declaration_exists(self, flight_declaration_id: str) -> bool:
        return FlightDeclaration.objects.filter(id=flight_declaration_id).exists()

    def get_flight_declaration_by_id(self, flight_declaration_id: str) -> Tuple[None, FlightDeclaration]:
        try:
            flight_declaration = FlightDeclaration.objects.get(id=flight_declaration_id)
            return flight_declaration
        except FlightDeclaration.DoesNotExist:
            return None

    def get_flight_authorization_by_flight_declaration_obj(self, flight_declaration: FlightDeclaration) -> Union[None, FlightAuthorization]:
        try:
            flight_authorization = FlightAuthorization.objects.get(declaration=flight_declaration)
            return flight_authorization
        except FlightDeclaration.DoesNotExist:
            return None
        except FlightAuthorization.DoesNotExist:
            return None

    def get_flight_authorization_by_flight_declaration(self, flight_declaration_id: str) -> Union[None, FlightAuthorization]:
        try:
            flight_declaration = FlightDeclaration.objects.get(id=flight_declaration_id)
            flight_authorization = FlightAuthorization.objects.get(declaration=flight_declaration)
            return flight_authorization
        except FlightDeclaration.DoesNotExist:
            return None
        except FlightAuthorization.DoesNotExist:
            return None

    def get_current_flight_declaration_ids(self) -> Union[None, uuid4]:
        """This method gets flight operation ids that are active in the system within near the time interval"""
        now = arrow.now().isoformat()
        relevant_ids = FlightDeclaration.objects.filter(
            start_datetime__lte=now,
            end_datetime__gte=now,
        ).values_list("id", flat=True)
        return relevant_ids

    def get_current_flight_accepted_activated_declaration_ids(self, now: str) -> Union[None, uuid4]:
        """This method gets flight operation ids that are active in the system"""
        n = arrow.get(now)

        two_minutes_before_now = n.shift(seconds=-120).isoformat()
        five_hours_from_now = n.shift(minutes=300).isoformat()
        relevant_ids = (
            FlightDeclaration.objects.filter(
                start_datetime__gte=two_minutes_before_now,
                end_datetime__lte=five_hours_from_now,
            )
            .filter(state__in=[1, 2])
            .values_list("id", flat=True)
        )
        return relevant_ids

    def get_conformance_monitoring_task(self, flight_declaration: FlightDeclaration) -> Union[None, TaskScheduler]:
        try:
            return TaskScheduler.objects.get(flight_declaration=flight_declaration)
        except TaskScheduler.DoesNotExist:
            return None


class BlenderDatabaseWriter:
    def delete_flight_declaration(self, flight_declaration_id: str) -> bool:
        try:
            flight_declaration = FlightDeclaration.objects.get(id=flight_declaration_id)
            flight_declaration.delete()
            return True
        except FlightDeclaration.DoesNotExist:
            return False
        except IntegrityError:
            return False

    def create_flight_declaration(self, flight_declaration_creation: FlightDeclarationCreationPayload) -> bool:
        try:
            flight_declaration = FlightDeclaration(
                id=flight_declaration_creation.id,
                operational_intent=flight_declaration_creation.operational_intent,
                flight_declaration_raw_geojson=flight_declaration_creation.flight_declaration_raw_geojson,
                bounds=flight_declaration_creation.bounds,
                aircraft_id=flight_declaration_creation.aircraft_id,
                state=flight_declaration_creation.state,
            )
            flight_declaration.save()
            return True

        except IntegrityError:
            return False

    def set_flight_declaration_non_conforming(self, flight_declaration: FlightDeclaration):
        flight_declaration.state = 3
        flight_declaration.save()

    def create_flight_authorization_with_submitted_operational_intent(
        self, flight_declaration: FlightDeclaration, dss_operational_intent_id: str
    ) -> bool:
        try:
            flight_authorization = FlightAuthorization(
                declaration=flight_declaration,
                dss_operational_intent_id=dss_operational_intent_id,
            )
            flight_authorization.save()
            return True

        except IntegrityError:
            return False

    def create_flight_authorization_from_flight_declaration_obj(self, flight_declaration: FlightDeclaration) -> bool:
        try:
            flight_authorization = FlightAuthorization(declaration=flight_declaration)
            flight_authorization.save()
            return True
        except FlightDeclaration.DoesNotExist:
            return False
        except IntegrityError:
            return False

    def create_flight_authorization(self, flight_declaration_id: str) -> bool:
        try:
            flight_declaration = FlightDeclaration.objects.get(id=flight_declaration_id)
            flight_authorization = FlightAuthorization(declaration=flight_declaration)
            flight_authorization.save()
            return True
        except FlightDeclaration.DoesNotExist:
            return False
        except IntegrityError:
            return False

    def update_telemetry_timestamp(self, flight_declaration_id: str) -> bool:
        now = arrow.now().isoformat()
        try:
            flight_declaration = FlightDeclaration.objects.get(id=flight_declaration_id)
            flight_declaration.latest_telemetry_datetime = now
            flight_declaration.save()
            return True
        except FlightDeclaration.DoesNotExist:
            return False

    def update_flight_authorization_op_int(self, flight_authorization: FlightAuthorization, dss_operational_intent_id) -> bool:
        try:
            flight_authorization.dss_operational_intent_id = dss_operational_intent_id
            flight_authorization.save()
            return True
        except Exception:
            return False

    def update_flight_operation_operational_intent(
        self,
        flight_declaration_id: str,
        operational_intent: PartialCreateOperationalIntentReference,
    ) -> bool:
        try:
            flight_declaration = FlightDeclaration.objects.get(id=flight_declaration_id)
            flight_declaration.operational_intent = json.dumps(asdict(operational_intent))
            # TODO: Convert the updated operational intent to GeoJSON
            flight_declaration.save()
            return True
        except Exception:
            return False

    def update_flight_operation_state(self, flight_declaration_id: str, state: int) -> bool:
        try:
            flight_declaration = FlightDeclaration.objects.get(id=flight_declaration_id)
            flight_declaration.state = state
            flight_declaration.save()
            return True
        except Exception:
            return False

    def create_conformance_monitoring_periodic_task(self, flight_declaration: FlightDeclaration) -> bool:
        conformance_monitoring_job = TaskScheduler()
        every = int(os.getenv("HEARTBEAT_RATE_SECS", default=5))
        now = arrow.now()
        fd_end = arrow.get(flight_declaration.end_datetime)
        delta = fd_end - now
        delta_seconds = delta.total_seconds()
        expires = now.shift(seconds=delta_seconds)
        task_name = "check_flight_conformance"

        try:
            p_task = conformance_monitoring_job.schedule_every(
                task_name=task_name,
                period="seconds",
                every=every,
                expires=expires,
                flight_declaration=flight_declaration,
            )
            p_task.start()
            return True
        except Exception:
            logger.error("Could not create periodic task")
            return False

    def remove_conformance_monitoring_periodic_task(self, conformance_monitoring_task: TaskScheduler):
        conformance_monitoring_task.terminate()
