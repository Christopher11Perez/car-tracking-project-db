from datetime import datetime, timezone

from fastapi import HTTPException

from dao.trip import (
    TripDAO,
    TripCreate,
    TripUpdate
)


class TripHandler:

    def _normalize_trip_timestamps(
            self,
            trip
    ):
        if trip.start_ts is not None:
            trip.start_ts = (
                trip.start_ts.replace(
                    tzinfo=timezone.utc
                )
            )

        if trip.end_ts is not None:
            trip.end_ts = (
                trip.end_ts.replace(
                    tzinfo=timezone.utc
                )
            )

        return trip

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
                status_code=400,
                detail="Invalid timestamp"
            )

    def _validate_point(
            self,
            geom
    ):
        if not isinstance(geom, dict):
            raise HTTPException(
                status_code=400,
                detail="Invalid geometry"
            )

        if geom.get("type") != "Point":
            raise HTTPException(
                status_code=400,
                detail="Geometry must be a Point"
            )

        coordinates = geom.get(
            "coordinates"
        )

        if (
            not isinstance(coordinates, list)
            or len(coordinates) != 2
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid Point coordinates"
            )

        lon = coordinates[0]
        lat = coordinates[1]

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

    def get_all_trips(
            self,
            limit,
            offset,
            vehicle_id=None,
            from_ts=None,
            to_ts=None
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

        if vehicle_id is not None:
            try:
                parsed_vehicle_id = int(
                    vehicle_id
                )

            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid vehicle_id"
                )

            if parsed_vehicle_id <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid vehicle_id"
                )

        parsed_from_ts = (
            self._parse_timestamp(
                from_ts
            )
        )

        parsed_to_ts = (
            self._parse_timestamp(
                to_ts
            )
        )

        if (
            parsed_from_ts is not None
            and parsed_to_ts is not None
            and parsed_from_ts > parsed_to_ts
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid time range"
            )

        dao = TripDAO()

        trips, count = (
            dao.get_all_trips(
                limit,
                offset,
                parsed_vehicle_id,
                parsed_from_ts,
                parsed_to_ts
            )
        )

        items = [
            self._normalize_trip_timestamps(
                trip
            )
            for trip in trips
        ]

        return {
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": count
        }

    def get_trip_by_id(
            self,
            trip_id: int
    ):
        dao = TripDAO()

        result = (
            dao.get_trip_by_id(
                trip_id
            )
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Trip not found"
            )

        return self._normalize_trip_timestamps(
            result
        )

    def create_trip(
            self,
            new_trip: TripCreate
    ):
        dao = TripDAO()

        if (
            new_trip.vehicle_id <= 0
            or not dao.vehicle_exists(
                new_trip.vehicle_id
            )
        ):
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found"
            )

        start_ts = (
            self._parse_timestamp(
                new_trip.start_ts
            )
        )

        end_ts = (
            self._parse_timestamp(
                new_trip.end_ts
            )
        )

        if end_ts <= start_ts:
            raise HTTPException(
                status_code=400,
                detail="end_ts must be later than start_ts"
            )

        if new_trip.start_geom is not None:
            self._validate_point(
                new_trip.start_geom
            )

        if new_trip.end_geom is not None:
            self._validate_point(
                new_trip.end_geom
            )

        if (
            new_trip.distance_km is not None
            and new_trip.distance_km < 0
        ):
            raise HTTPException(
                status_code=400,
                detail="Distance cannot be negative"
            )

        result = dao.create_trip(
            new_trip,
            start_ts,
            end_ts
        )

        return self._normalize_trip_timestamps(
            result
        )

    def update_trip(
            self,
            trip_id: int,
            trip_update: TripUpdate
    ):
        dao = TripDAO()

        current_trip = (
            dao.get_trip_by_id(
                trip_id
            )
        )

        if current_trip is None:
            raise HTTPException(
                status_code=404,
                detail="Trip not found"
            )

        trip_data = (
            trip_update.model_dump(
                exclude_unset=True
            )
        )

        if not trip_data:
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided"
            )

        if "vehicle_id" in trip_data:

            if (
                trip_data["vehicle_id"] is None
                or trip_data["vehicle_id"] <= 0
                or not dao.vehicle_exists(
                    trip_data["vehicle_id"]
                )
            ):
                raise HTTPException(
                    status_code=404,
                    detail="Vehicle not found"
                )

        if "start_geom" in trip_data:

            if trip_data["start_geom"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="start_geom cannot be null when updated"
                )

            self._validate_point(
                trip_data["start_geom"]
            )

        if "end_geom" in trip_data:

            if trip_data["end_geom"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="end_geom cannot be null when updated"
                )

            self._validate_point(
                trip_data["end_geom"]
            )

        if "distance_km" in trip_data:

            if (
                trip_data["distance_km"] is not None
                and trip_data["distance_km"] < 0
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Distance cannot be negative"
                )

        final_start_ts = (
            current_trip.start_ts
        )

        final_end_ts = (
            current_trip.end_ts
        )

        if "start_ts" in trip_data:

            if trip_data["start_ts"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="start_ts cannot be null"
                )

            final_start_ts = (
                self._parse_timestamp(
                    trip_data["start_ts"]
                )
            )

            trip_data["start_ts"] = (
                final_start_ts
            )

        if "end_ts" in trip_data:

            if trip_data["end_ts"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="end_ts cannot be null"
                )

            final_end_ts = (
                self._parse_timestamp(
                    trip_data["end_ts"]
                )
            )

            trip_data["end_ts"] = (
                final_end_ts
            )

        if final_end_ts <= final_start_ts:
            raise HTTPException(
                status_code=400,
                detail="end_ts must be later than start_ts"
            )

        result = (
            dao.update_trip(
                trip_id,
                trip_data
            )
        )

        return self._normalize_trip_timestamps(
            result
        )

    def delete_trip(
            self,
            trip_id: int
    ):
        dao = TripDAO()

        trip = (
            dao.get_trip_by_id(
                trip_id
            )
        )

        if trip is None:
            raise HTTPException(
                status_code=404,
                detail="Trip not found"
            )

        dao.delete_trip(
            trip_id
        )

        return {
            "message": "Trip deleted successfully.",
            "trip_id": trip_id
        }

    def get_vehicle_trips(
            self,
            vehicle_id: int,
            limit,
            offset,
            from_ts=None,
            to_ts=None
    ):
        dao = TripDAO()

        if (
            vehicle_id <= 0
            or not dao.vehicle_exists(
                vehicle_id
            )
        ):
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found"
            )

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

        parsed_from_ts = (
            self._parse_timestamp(
                from_ts
            )
        )

        parsed_to_ts = (
            self._parse_timestamp(
                to_ts
            )
        )

        if (
            parsed_from_ts is not None
            and parsed_to_ts is not None
            and parsed_from_ts > parsed_to_ts
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid time range"
            )

        trips, count = (
            dao.get_vehicle_trips(
                vehicle_id,
                limit,
                offset,
                parsed_from_ts,
                parsed_to_ts
            )
        )

        items = [
            self._normalize_trip_timestamps(
                trip
            )
            for trip in trips
        ]

        return {
            "vehicle_id": vehicle_id,
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": count
        }