from datetime import datetime, timezone

from fastapi import HTTPException

from dao.location_ping import (
    LocationPingDAO,
    LocationPingCreate,
    LocationPingUpdate
)


class LocationPingHandler:

    def _normalize_timestamp(
            self,
            ping
    ):
        if ping.ts is not None:
            ping.ts = ping.ts.replace(
                tzinfo=timezone.utc
            )

        return ping

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
                    clean_value[:-1] +
                    "+00:00"
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

    def get_all_location_pings(
            self,
            limit,
            offset,
            vehicle_id=None,
            from_ts=None,
            to_ts=None,
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

        parsed_bbox = (
            self._validate_bbox(
                bbox
            )
        )

        dao = LocationPingDAO()

        pings, count = (
            dao.get_all_location_pings(
                limit,
                offset,
                parsed_vehicle_id,
                parsed_from_ts,
                parsed_to_ts,
                parsed_bbox
            )
        )

        items = [
            self._normalize_timestamp(
                ping
            )
            for ping in pings
        ]

        return {
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": count
        }

    def get_location_ping_by_id(
            self,
            ping_id: int
    ):
        dao = LocationPingDAO()

        result = (
            dao.get_location_ping_by_id(
                ping_id
            )
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Location ping not found"
            )

        return self._normalize_timestamp(
            result
        )

    def create_location_ping(
            self,
            new_ping: LocationPingCreate
    ):
        dao = LocationPingDAO()

        if new_ping.vehicle_id <= 0:
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found"
            )

        if not dao.vehicle_exists(
            new_ping.vehicle_id
        ):
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found"
            )

        parsed_ts = (
            self._parse_timestamp(
                new_ping.ts
            )
        )

        self._validate_point(
            new_ping.geom
        )

        if (
            new_ping.speed_kph is not None
            and new_ping.speed_kph < 0
        ):
            raise HTTPException(
                status_code=400,
                detail="Speed cannot be negative"
            )

        if (
            new_ping.heading_deg is not None
            and (
                new_ping.heading_deg < 0
                or new_ping.heading_deg >= 360
            )
        ):
            raise HTTPException(
                status_code=400,
                detail="Heading must be between 0 and 360"
            )

        result = (
            dao.create_location_ping(
                new_ping,
                parsed_ts
            )
        )

        return self._normalize_timestamp(
            result
        )

    def update_location_ping(
            self,
            ping_id: int,
            ping_update: LocationPingUpdate
    ):
        dao = LocationPingDAO()

        current_ping = (
            dao.get_location_ping_by_id(
                ping_id
            )
        )

        if current_ping is None:
            raise HTTPException(
                status_code=404,
                detail="Location ping not found"
            )

        ping_data = (
            ping_update.model_dump(
                exclude_unset=True
            )
        )

        if not ping_data:
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided"
            )

        if "vehicle_id" in ping_data:

            if (
                ping_data["vehicle_id"] is None
                or not dao.vehicle_exists(
                    ping_data["vehicle_id"]
                )
            ):
                raise HTTPException(
                    status_code=404,
                    detail="Vehicle not found"
                )

        if "ts" in ping_data:

            if ping_data["ts"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="Timestamp cannot be null"
                )

            ping_data["ts"] = (
                self._parse_timestamp(
                    ping_data["ts"]
                )
            )

        if "geom" in ping_data:

            if ping_data["geom"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="Geometry cannot be null"
                )

            self._validate_point(
                ping_data["geom"]
            )

        if "speed_kph" in ping_data:

            if (
                ping_data["speed_kph"]
                is not None
                and ping_data[
                    "speed_kph"
                ] < 0
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Speed cannot be negative"
                )

        if "heading_deg" in ping_data:

            if (
                ping_data["heading_deg"]
                is not None
                and (
                    ping_data[
                        "heading_deg"
                    ] < 0
                    or ping_data[
                        "heading_deg"
                    ] >= 360
                )
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Heading must be between 0 and 360"
                )

        result = (
            dao.update_location_ping(
                ping_id,
                ping_data
            )
        )

        return self._normalize_timestamp(
            result
        )

    def delete_location_ping(
            self,
            ping_id: int
    ):
        dao = LocationPingDAO()

        ping = (
            dao.get_location_ping_by_id(
                ping_id
            )
        )

        if ping is None:
            raise HTTPException(
                status_code=404,
                detail="Location ping not found"
            )

        dao.delete_location_ping(
            ping_id
        )

        return {
            "message": "Location ping deleted successfully.",
            "ping_id": ping_id
        }

    def get_vehicle_pings(
            self,
            vehicle_id: int,
            limit,
            offset,
            from_ts=None,
            to_ts=None
    ):
        dao = LocationPingDAO()

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

        pings, count = (
            dao.get_vehicle_pings(
                vehicle_id,
                limit,
                offset,
                parsed_from_ts,
                parsed_to_ts
            )
        )

        items = [
            self._normalize_timestamp(
                ping
            )
            for ping in pings
        ]

        return {
            "vehicle_id": vehicle_id,
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": count
        }