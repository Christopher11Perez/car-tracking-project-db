from datetime import timezone

from fastapi import HTTPException, Response

from dao.vehicle import (
    VehicleDAO,
    VehicleCreate,
    VehicleUpdate
)


class VehicleHandler:

    def _normalize_created_at(self, vehicle):
        if vehicle.created_at is not None:
            vehicle.created_at = vehicle.created_at.replace(
                tzinfo=timezone.utc
            )

        return vehicle

    def get_all_vehicles(
            self,
            limit,
            offset,
            status=None,
            plate_number=None
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

        dao = VehicleDAO()

        vehicles, count = dao.get_all_vehicles(
            limit,
            offset,
            status,
            plate_number
        )

        items = [
            self._normalize_created_at(vehicle)
            for vehicle in vehicles
        ]

        return {
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": count
        }

    def get_vehicle_by_id(
            self,
            vehicle_id: int
    ):
        dao = VehicleDAO()

        result = dao.get_vehicle_by_id(
            vehicle_id
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found"
            )

        return self._normalize_created_at(
            result
        )

    def get_current_location(
            self,
            vehicle_id
    ):
        try:
            vehicle_id = int(vehicle_id)

        except (
            ValueError,
            TypeError
        ):
            raise HTTPException(
                status_code=400,
                detail="vehicle_id must be a positive integer"
            )

        if vehicle_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="vehicle_id must be a positive integer"
            )

        dao = VehicleDAO()

        vehicle = dao.get_vehicle_by_id(
            vehicle_id
        )

        if vehicle is None:
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found"
            )

        result = dao.get_current_location(
            vehicle_id
        )

        if result is None:
            return Response(
                status_code=204
            )

        if result["last_ts"] is not None:
            result["last_ts"] = (
                result["last_ts"]
                .replace(tzinfo=timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            )

        return result

    def create_vehicle(
            self,
            new_vehicle: VehicleCreate
    ):
        dao = VehicleDAO()

        new_vehicle.plate_number = (
            new_vehicle.plate_number.strip()
        )

        if not new_vehicle.plate_number:
            raise HTTPException(
                status_code=400,
                detail="Plate number cannot be empty"
            )

        if new_vehicle.make is not None:
            new_vehicle.make = (
                new_vehicle.make.strip()
            )

        if new_vehicle.model is not None:
            new_vehicle.model = (
                new_vehicle.model.strip()
            )

        if (
            new_vehicle.year < 1950
            or new_vehicle.year > 2100
        ):
            raise HTTPException(
                status_code=400,
                detail="Year must be between 1950 and 2100"
            )

        if not dao.vehicle_type_exists(
            new_vehicle.vehicle_type_id
        ):
            raise HTTPException(
                status_code=404,
                detail="Vehicle type not found"
            )

        if not dao.vehicle_status_exists(
            new_vehicle.vehicle_status_id
        ):
            raise HTTPException(
                status_code=404,
                detail="Vehicle status not found"
            )

        if dao.plate_number_exists(
            new_vehicle.plate_number
        ):
            raise HTTPException(
                status_code=409,
                detail="Plate number already exists"
            )

        result = dao.create_vehicle(
            new_vehicle
        )

        return self._normalize_created_at(
            result
        )

    def update_vehicle(
            self,
            vehicle_id: int,
            vehicle_update: VehicleUpdate
    ):
        dao = VehicleDAO()

        current_vehicle = (
            dao.get_vehicle_by_id(vehicle_id)
        )

        if current_vehicle is None:
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found"
            )

        vehicle_data = (
            vehicle_update.model_dump(
                exclude_unset=True
            )
        )

        if not vehicle_data:
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided"
            )

        if "plate_number" in vehicle_data:
            if vehicle_data["plate_number"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="Plate number cannot be null"
                )

            vehicle_data["plate_number"] = (
                vehicle_data["plate_number"].strip()
            )

            if not vehicle_data["plate_number"]:
                raise HTTPException(
                    status_code=400,
                    detail="Plate number cannot be empty"
                )

            if dao.plate_number_exists(
                vehicle_data["plate_number"],
                vehicle_id
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Plate number already exists"
                )

        if "make" in vehicle_data:
            if vehicle_data["make"] is not None:
                vehicle_data["make"] = (
                    vehicle_data["make"].strip()
                )

        if "model" in vehicle_data:
            if vehicle_data["model"] is not None:
                vehicle_data["model"] = (
                    vehicle_data["model"].strip()
                )

        if "year" in vehicle_data:
            if vehicle_data["year"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="Year cannot be null"
                )

            if (
                vehicle_data["year"] < 1950
                or vehicle_data["year"] > 2100
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Year must be between 1950 and 2100"
                )

        if "vehicle_type_id" in vehicle_data:
            if vehicle_data["vehicle_type_id"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="Vehicle type cannot be null"
                )

            if not dao.vehicle_type_exists(
                vehicle_data["vehicle_type_id"]
            ):
                raise HTTPException(
                    status_code=404,
                    detail="Vehicle type not found"
                )

        if "vehicle_status_id" in vehicle_data:
            if vehicle_data["vehicle_status_id"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="Vehicle status cannot be null"
                )

            if not dao.vehicle_status_exists(
                vehicle_data["vehicle_status_id"]
            ):
                raise HTTPException(
                    status_code=404,
                    detail="Vehicle status not found"
                )

        result = dao.update_vehicle(
            vehicle_id,
            vehicle_data
        )

        return self._normalize_created_at(
            result
        )

    def delete_vehicle(
            self,
            vehicle_id: int
    ):
        dao = VehicleDAO()

        vehicle = dao.get_vehicle_by_id(
            vehicle_id
        )

        if vehicle is None:
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found"
            )

        if dao.vehicle_has_references(
            vehicle_id
        ):
            raise HTTPException(
                status_code=409,
                detail="Vehicle cannot be deleted because it is referenced by other records"
            )

        dao.delete_vehicle(
            vehicle_id
        )

        return {
            "message": "Vehicle deleted successfully.",
            "vehicle_id": vehicle_id
        }