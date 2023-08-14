import hashlib
from typing import List, Union

import arrow
from django.db.models import QuerySet
from rtree import index

from auth_helper.common import get_redis

from .models import FlightDeclaration


class FlightDeclarationRTreeIndexFactory:
    def __init__(self, index_name: str):
        self.r = get_redis()
        self.idx = index.Index(index_name)

    def add_box_to_index(
        self,
        id: int,
        flight_declaration_id: str,
        view: List[float],
        start_date: str,
        end_date: str,
    ):
        metadata = {
            "start_date": start_date,
            "end_date": end_date,
            "flight_declaration_id": flight_declaration_id,
        }
        self.idx.insert(
            id=id, coordinates=(view[0], view[1], view[2], view[3]), obj=metadata
        )

    def delete_from_index(self, enumerated_id: int, view: List[float]):
        self.idx.delete(
            id=enumerated_id, coordinates=(view[0], view[1], view[2], view[3])
        )

    def generate_flight_declaration_index(
        self, all_flight_declarations: Union[QuerySet, List[FlightDeclaration]]
    ) -> None:
        """This method generates a rTree index of currently active operational indexes"""

        present = arrow.now()
        start_date = present.shift(days=-1)
        end_date = present.shift(days=1)
        for fence_idx, flight_declaration in enumerate(all_flight_declarations):
            declaration_idx_str = str(flight_declaration.id)
            flight_declaration_id = (
                int(hashlib.sha256(declaration_idx_str.encode("utf-8")).hexdigest(), 16)
                % 10**8
            )
            view = [float(i) for i in flight_declaration.bounds.split(",")]
            self.add_box_to_index(
                id=flight_declaration_id,
                flight_declaration_id=declaration_idx_str,
                view=view,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

    def clear_rtree_index(self):
        """Method to delete all boxes from the index"""
        all_declarations = FlightDeclaration.objects.all()
        for declaration_idx, declaration in enumerate(all_declarations):
            declaration_idx_str = str(declaration.id)
            declaration_id = (
                int(hashlib.sha256(declaration_idx_str.encode("utf-8")).hexdigest(), 16)
                % 10**8
            )
            view = [float(i) for i in declaration.bounds.split(",")]

            self.delete_from_index(enumerated_id=declaration_id, view=view)

    def check_box_intersection(self, view_box: List[float]):
        intersections = [
            n.object
            for n in self.idx.intersection(
                (view_box[0], view_box[1], view_box[2], view_box[3]), objects=True
            )
        ]
        return intersections
