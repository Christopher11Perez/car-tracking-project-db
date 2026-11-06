from datetime import timezone

from fastapi import HTTPException

from dao.parking_area import (
    ParkingAreaDAO,
    ParkingAreaCreate,
    ParkingAreaUpdate
)


class ParkingAreaHandler:

    def _normalize_created_at(
            self,
            parking_area
    ):
        if parking_area.created_at is not None:
            parking_area.created_at = (
                parking_area.created_at.replace(
                    tzinfo=timezone.utc
                )
            )

        return parking_area

    def _validate_polygon(
            self,
            geom
    ):
        if not isinstance(geom, dict):
            raise HTTPException(
                status_code=400,
                detail="Invalid geometry"
            )

        if geom.get("type") != "Polygon":
            raise HTTPException(
                status_code=400,
                detail="Geometry must be a Polygon"
            )

        coordinates = geom.get(
            "coordinates"
        )

        if (
            not isinstance(coordinates, list)
            or len(coordinates) == 0
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid Polygon coordinates"
            )

        exterior_ring = coordinates[0]

        if (
            not isinstance(exterior_ring, list)
            or len(exterior_ring) < 4
        ):
            raise HTTPException(
                status_code=400,
                detail="Polygon must contain at least four coordinates"
            )

        for coordinate in exterior_ring:

            if (
                not isinstance(coordinate, list)
                or len(coordinate) < 2
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid coordinate"
                )

            lon = coordinate[0]
            lat = coordinate[1]

            if (
                not isinstance(
                    lon,
                    (int, float)
                )
                or not isinstance(
                    lat,
                    (int, float)
                )
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Coordinates must be numeric"
                )

            if (
                lon < -180
                or lon > 180
                or lat < -90
                or lat > 90
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Coordinates must be valid WGS84 values"
                )

        if exterior_ring[0] != exterior_ring[-1]:
            raise HTTPException(
                status_code=400,
                detail="Polygon must be closed"
            )

    def _validate_bbox(
            self,
            bbox
    ):
        if bbox is None:
            return None

        try:
            values = [
                float(value)
                for value
                in bbox.split(",")
            ]

        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid bbox"
            )

        if len(values) != 4:
            raise HTTPException(
                status_code=400,
                detail="Invalid bbox"
            )

        min_lon = values[0]
        min_lat = values[1]
        max_lon = values[2]
        max_lat = values[3]

        if (
            min_lon < -180
            or max_lon > 180
            or min_lat < -90
            or max_lat > 90
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid bbox"
            )

        if (
            min_lon >= max_lon
            or min_lat >= max_lat
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid bbox"
            )

        return (
            min_lon,
            min_lat,
            max_lon,
            max_lat
        )

    def get_all_parking_areas(
            self,
            limit,
            offset,
            name=None,
            bbox=None
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

        parsed_bbox = (
            self._validate_bbox(
                bbox
            )
        )

        dao = ParkingAreaDAO()

        parking_areas, count = (
            dao.get_all_parking_areas(
                limit,
                offset,
                name,
                parsed_bbox
            )
        )

        items = [
            self._normalize_created_at(
                parking_area
            )
            for parking_area
            in parking_areas
        ]

        return {
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": count
        }

    def get_parking_area_by_id(
            self,
            parking_area_id: int
    ):
        dao = ParkingAreaDAO()

        result = (
            dao.get_parking_area_by_id(
                parking_area_id
            )
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Parking area not found"
            )

        return self._normalize_created_at(
            result
        )

    def create_parking_area(
            self,
            new_parking_area: ParkingAreaCreate
    ):
        dao = ParkingAreaDAO()

        new_parking_area.name = (
            new_parking_area.name.strip()
        )

        if not new_parking_area.name:
            raise HTTPException(
                status_code=400,
                detail="Name cannot be empty"
            )

        if (
            new_parking_area.capacity
            is not None
            and new_parking_area.capacity < 0
        ):
            raise HTTPException(
                status_code=400,
                detail="Capacity cannot be negative"
            )

        self._validate_polygon(
            new_parking_area.geom
        )

        if not dao.geometry_is_valid(
            new_parking_area.geom
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid Polygon geometry"
            )

        result = (
            dao.create_parking_area(
                new_parking_area
            )
        )

        return self._normalize_created_at(
            result
        )

    def update_parking_area(
            self,
            parking_area_id: int,
            parking_update: ParkingAreaUpdate
    ):
        dao = ParkingAreaDAO()

        current_parking_area = (
            dao.get_parking_area_by_id(
                parking_area_id
            )
        )

        if current_parking_area is None:
            raise HTTPException(
                status_code=404,
                detail="Parking area not found"
            )

        parking_data = (
            parking_update.model_dump(
                exclude_unset=True
            )
        )

        if not parking_data:
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided"
            )

        if "name" in parking_data:

            if parking_data["name"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="Name cannot be null"
                )

            parking_data["name"] = (
                parking_data["name"].strip()
            )

            if not parking_data["name"]:
                raise HTTPException(
                    status_code=400,
                    detail="Name cannot be empty"
                )

        if "capacity" in parking_data:

            if (
                parking_data["capacity"]
                is not None
                and parking_data["capacity"] < 0
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Capacity cannot be negative"
                )

        if "geom" in parking_data:

            if parking_data["geom"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="Geometry cannot be null"
                )

            self._validate_polygon(
                parking_data["geom"]
            )

            if not dao.geometry_is_valid(
                parking_data["geom"]
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid Polygon geometry"
                )

        result = (
            dao.update_parking_area(
                parking_area_id,
                parking_data
            )
        )

        return self._normalize_created_at(
            result
        )

    def delete_parking_area(
            self,
            parking_area_id: int
    ):
        dao = ParkingAreaDAO()

        parking_area = (
            dao.get_parking_area_by_id(
                parking_area_id
            )
        )

        if parking_area is None:
            raise HTTPException(
                status_code=404,
                detail="Parking area not found"
            )

        dao.delete_parking_area(
            parking_area_id
        )

        return {
            "message": "Parking area deleted successfully.",
            "parking_area_id": parking_area_id
        }