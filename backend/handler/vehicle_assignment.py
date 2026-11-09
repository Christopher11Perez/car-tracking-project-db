from datetime import datetime, timezone

from fastapi import HTTPException

from dao.vehicle_assignment import (
    VehicleAssignmentDAO,
    VehicleAssignmentCreate,
    VehicleAssignmentUpdate
)


class VehicleAssignmentHandler:

    def _normalize_timestamps(
            self,
            assignment
    ):
        if assignment.assigned_from is not None:
            assignment.assigned_from = (
                assignment.assigned_from.replace(
                    tzinfo=timezone.utc
                )
            )

        if assignment.assigned_to is not None:
            assignment.assigned_to = (
                assignment.assigned_to.replace(
                    tzinfo=timezone.utc
                )
            )

        return assignment

    def _parse_timestamp(
            self,
            value
    ):
        if value is None:
            return None

        try:
            clean_value = value.strip()

            if clean_value.endswith("Z"):
                clean_value = (
                    clean_value[:-1]
                    + "+00:00"
                )

            parsed = datetime.fromisoformat(
                clean_value
            )

            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError("Timestamp must include a timezone")

            parsed = (
                parsed.astimezone(
                    timezone.utc
                )
                .replace(
                    tzinfo=None
                )
            )

            return parsed

        except (
            ValueError,
            AttributeError
        ):
            raise HTTPException(
                status_code=422,
                detail="Invalid assignment timestamp"
            )

    def _parse_positive_id(
            self,
            value,
            field_name
    ):
        try:
            parsed = int(value)

        except (
            ValueError,
            TypeError
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {field_name}"
            )

        if parsed <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {field_name}"
            )

        return parsed

    def get_all_assignments(
            self,
            limit,
            offset,
            vehicle_id=None,
            driver_id=None,
            active=None
    ):
        try:
            limit = int(limit)
            offset = int(offset)

        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid query parameter values"
            )

        if limit < 0 or offset < 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid query parameter values"
            )

        parsed_vehicle_id = None
        parsed_driver_id = None
        parsed_active = None

        if vehicle_id is not None:
            parsed_vehicle_id = (
                self._parse_positive_id(
                    vehicle_id,
                    "vehicle_id"
                )
            )

        if driver_id is not None:
            parsed_driver_id = (
                self._parse_positive_id(
                    driver_id,
                    "driver_id"
                )
            )

        if active is not None:
            active_value = (
                active.strip().lower()
            )

            if active_value == "true":
                parsed_active = True

            elif active_value == "false":
                parsed_active = False

            else:
                raise HTTPException(
                    status_code=400,
                    detail="active must be true or false"
                )

        dao = VehicleAssignmentDAO()

        assignments, count = (
            dao.get_all_assignments(
                limit,
                offset,
                parsed_vehicle_id,
                parsed_driver_id,
                parsed_active
            )
        )

        items = [
            self._normalize_timestamps(
                assignment
            )
            for assignment
            in assignments
        ]

        return {
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": count
        }

    def get_assignment_by_id(
            self,
            assignment_id: int
    ):
        dao = VehicleAssignmentDAO()

        result = (
            dao.get_assignment_by_id(
                assignment_id
            )
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Vehicle assignment not found"
            )

        return self._normalize_timestamps(
            result
        )

    def create_assignment(
            self,
            new_assignment: VehicleAssignmentCreate
    ):
        dao = VehicleAssignmentDAO()

        if (
            new_assignment.vehicle_id <= 0
            or not dao.vehicle_exists(
                new_assignment.vehicle_id
            )
        ):
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found"
            )

        if (
            new_assignment.driver_id <= 0
            or not dao.driver_exists(
                new_assignment.driver_id
            )
        ):
            raise HTTPException(
                status_code=404,
                detail="Driver not found"
            )

        assigned_from = (
            self._parse_timestamp(
                new_assignment.assigned_from
            )
        )

        assigned_to = (
            self._parse_timestamp(
                new_assignment.assigned_to
            )
        )

        if (
            assigned_to is not None
            and assigned_to <= assigned_from
        ):
            raise HTTPException(
                status_code=422,
                detail="assigned_to must be later than assigned_from"
            )

        result = (
            dao.create_assignment(
                new_assignment,
                assigned_from,
                assigned_to
            )
        )

        return self._normalize_timestamps(
            result
        )

    def update_assignment(
            self,
            assignment_id: int,
            assignment_update: VehicleAssignmentUpdate
    ):
        dao = VehicleAssignmentDAO()

        current = (
            dao.get_assignment_by_id(
                assignment_id
            )
        )

        if current is None:
            raise HTTPException(
                status_code=404,
                detail="Vehicle assignment not found"
            )

        assignment_data = (
            assignment_update.model_dump(
                exclude_unset=True
            )
        )

        if not assignment_data:
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided"
            )

        if "vehicle_id" in assignment_data:

            if (
                assignment_data["vehicle_id"]
                is None
                or assignment_data[
                    "vehicle_id"
                ] <= 0
                or not dao.vehicle_exists(
                    assignment_data[
                        "vehicle_id"
                    ]
                )
            ):
                raise HTTPException(
                    status_code=404,
                    detail="Vehicle not found"
                )

        if "driver_id" in assignment_data:

            if (
                assignment_data["driver_id"]
                is None
                or assignment_data[
                    "driver_id"
                ] <= 0
                or not dao.driver_exists(
                    assignment_data[
                        "driver_id"
                    ]
                )
            ):
                raise HTTPException(
                    status_code=404,
                    detail="Driver not found"
                )

        final_assigned_from = (
            current.assigned_from
        )

        final_assigned_to = (
            current.assigned_to
        )

        if "assigned_from" in assignment_data:

            if (
                assignment_data[
                    "assigned_from"
                ] is None
            ):
                raise HTTPException(
                    status_code=422,
                    detail="assigned_from cannot be null"
                )

            final_assigned_from = (
                self._parse_timestamp(
                    assignment_data[
                        "assigned_from"
                    ]
                )
            )

            assignment_data[
                "assigned_from"
            ] = final_assigned_from

        if "assigned_to" in assignment_data:

            if (
                assignment_data[
                    "assigned_to"
                ] is None
            ):
                final_assigned_to = None

            else:
                final_assigned_to = (
                    self._parse_timestamp(
                        assignment_data[
                            "assigned_to"
                        ]
                    )
                )

            assignment_data[
                "assigned_to"
            ] = final_assigned_to

        if (
            final_assigned_to is not None
            and final_assigned_to
            <= final_assigned_from
        ):
            raise HTTPException(
                status_code=422,
                detail="assigned_to must be later than assigned_from"
            )

        result = (
            dao.update_assignment(
                assignment_id,
                assignment_data
            )
        )

        return self._normalize_timestamps(
            result
        )

    def delete_assignment(
            self,
            assignment_id: int
    ):
        dao = VehicleAssignmentDAO()

        assignment = (
            dao.get_assignment_by_id(
                assignment_id
            )
        )

        if assignment is None:
            raise HTTPException(
                status_code=404,
                detail="Vehicle assignment not found"
            )

        dao.delete_assignment(
            assignment_id
        )

        return {
            "message": "Vehicle assignment deleted successfully.",
            "assignment_id": assignment_id
        }