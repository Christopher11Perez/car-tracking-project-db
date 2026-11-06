from datetime import timezone

from fastapi import HTTPException

from dao.road_segment import (
    RoadSegmentDAO,
    RoadSegmentCreate,
    RoadSegmentUpdate
)


class RoadSegmentHandler:

    def _normalize_created_at(
            self,
            road_segment
    ):
        if road_segment.created_at is not None:
            road_segment.created_at = (
                road_segment.created_at.replace(
                    tzinfo=timezone.utc
                )
            )

        return road_segment

    def _validate_geometry(
            self,
            geom
    ):
        if not isinstance(geom, dict):
            raise HTTPException(
                status_code=400,
                detail="Invalid geometry"
            )

        if geom.get("type") != "LineString":
            raise HTTPException(
                status_code=400,
                detail="Geometry must be a LineString"
            )

        coordinates = geom.get(
            "coordinates"
        )

        if (
            not isinstance(coordinates, list)
            or len(coordinates) < 2
        ):
            raise HTTPException(
                status_code=400,
                detail="LineString must contain at least two coordinates"
            )

        for coordinate in coordinates:

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

    def get_all_road_segments(
            self,
            limit,
            offset,
            name=None,
            min_speed_kph=None,
            max_speed_kph=None,
            bbox=None
    ):
        try:
            limit = int(limit)
            offset = int(offset)

        except (
                ValueError,
                TypeError
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid query parameter values"
            )

        if limit < 0 or offset < 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid query parameter values"
            )

        if name is not None:
            name = name.strip()

            if not name:
                name = None

        parsed_min_speed = None
        parsed_max_speed = None

        if min_speed_kph is not None:

            try:
                parsed_min_speed = float(
                    min_speed_kph
                )

            except (
                    ValueError,
                    TypeError
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid query parameter values"
                )

            if parsed_min_speed < 0:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid query parameter values"
                )

        if max_speed_kph is not None:

            try:
                parsed_max_speed = float(
                    max_speed_kph
                )

            except (
                    ValueError,
                    TypeError
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid query parameter values"
                )

            if parsed_max_speed < 0:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid query parameter values"
                )

        if (
                parsed_min_speed is not None
                and parsed_max_speed is not None
                and parsed_min_speed > parsed_max_speed
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid query parameter values"
            )

        parsed_bbox = (
            self._validate_bbox(bbox)
        )

        dao = RoadSegmentDAO()

        roads, count = (
            dao.get_all_road_segments(
                limit,
                offset,
                name,
                parsed_min_speed,
                parsed_max_speed,
                parsed_bbox
            )
        )

        items = [
            self._normalize_created_at(
                road
            )
            for road in roads
        ]

        return {
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": count
        }

    def get_road_segment_by_id(
            self,
            road_id: int
    ):
        dao = RoadSegmentDAO()

        result = (
            dao.get_road_segment_by_id(
                road_id
            )
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Road segment not found"
            )

        return self._normalize_created_at(
            result
        )

    def create_road_segment(
            self,
            new_road: RoadSegmentCreate
    ):
        dao = RoadSegmentDAO()

        new_road.name = (
            new_road.name.strip()
        )

        if not new_road.name:
            raise HTTPException(
                status_code=400,
                detail="Name cannot be empty"
            )

        if (
            new_road.speed_limit_kph
            is not None
            and new_road.speed_limit_kph < 0
        ):
            raise HTTPException(
                status_code=400,
                detail="Speed limit cannot be negative"
            )

        new_road.direction = (
            new_road.direction.strip().lower()
        )

        if new_road.direction not in (
            "both",
            "forward"
        ):
            raise HTTPException(
                status_code=400,
                detail="Direction must be both or forward"
            )

        self._validate_geometry(
            new_road.geom
        )

        result = (
            dao.create_road_segment(
                new_road
            )
        )

        return self._normalize_created_at(
            result
        )

    def update_road_segment(
            self,
            road_id: int,
            road_update: RoadSegmentUpdate
    ):
        dao = RoadSegmentDAO()

        current_road = (
            dao.get_road_segment_by_id(
                road_id
            )
        )

        if current_road is None:
            raise HTTPException(
                status_code=404,
                detail="Road segment not found"
            )

        road_data = (
            road_update.model_dump(
                exclude_unset=True
            )
        )

        if not road_data:
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided"
            )

        if "name" in road_data:

            if road_data["name"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="Name cannot be null"
                )

            road_data["name"] = (
                road_data["name"].strip()
            )

            if not road_data["name"]:
                raise HTTPException(
                    status_code=400,
                    detail="Name cannot be empty"
                )

        if "speed_limit_kph" in road_data:

            if (
                road_data["speed_limit_kph"]
                is not None
                and road_data[
                    "speed_limit_kph"
                ] < 0
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Speed limit cannot be negative"
                )

        if "direction" in road_data:

            if road_data["direction"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="Direction cannot be null"
                )

            road_data["direction"] = (
                road_data[
                    "direction"
                ].strip().lower()
            )

            if road_data[
                "direction"
            ] not in (
                "both",
                "forward"
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Direction must be both or forward"
                )

        if "geom" in road_data:

            if road_data["geom"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="Geometry cannot be null"
                )

            self._validate_geometry(
                road_data["geom"]
            )

        result = (
            dao.update_road_segment(
                road_id,
                road_data
            )
        )

        return self._normalize_created_at(
            result
        )

    def delete_road_segment(
            self,
            road_id: int
    ):
        dao = RoadSegmentDAO()

        road = (
            dao.get_road_segment_by_id(
                road_id
            )
        )

        if road is None:
            raise HTTPException(
                status_code=404,
                detail="Road segment not found"
            )

        dao.delete_road_segment(
            road_id
        )

        return {
            "message": "Road segment deleted successfully.",
            "road_id": road_id
        }

    def get_road_segments_geojson(
            self,
            limit,
            offset,
            name=None,
            min_speed_kph=None,
            max_speed_kph=None
    ):
        try:
            limit = int(limit)
            offset = int(offset)

        except (
            ValueError,
            TypeError
        ):
            raise HTTPException(
                status_code=422,
                detail="Invalid limit or offset"
            )

        if limit < 0 or offset < 0:
            raise HTTPException(
                status_code=422,
                detail="limit and offset must be non-negative"
            )

        parsed_min_speed = None
        parsed_max_speed = None

        if min_speed_kph is not None:

            try:
                parsed_min_speed = float(
                    min_speed_kph
                )

            except (
                ValueError,
                TypeError
            ):
                raise HTTPException(
                    status_code=422,
                    detail="Invalid min_speed_kph"
                )

            if parsed_min_speed < 0:
                raise HTTPException(
                    status_code=422,
                    detail="min_speed_kph must be non-negative"
                )

        if max_speed_kph is not None:

            try:
                parsed_max_speed = float(
                    max_speed_kph
                )

            except (
                ValueError,
                TypeError
            ):
                raise HTTPException(
                    status_code=422,
                    detail="Invalid max_speed_kph"
                )

            if parsed_max_speed < 0:
                raise HTTPException(
                    status_code=422,
                    detail="max_speed_kph must be non-negative"
                )

        if (
            parsed_min_speed is not None
            and parsed_max_speed is not None
            and parsed_min_speed
            > parsed_max_speed
        ):
            raise HTTPException(
                status_code=400,
                detail="min_speed_kph cannot exceed max_speed_kph"
            )

        if name is not None:
            name = name.strip()

            if not name:
                name = None

        dao = RoadSegmentDAO()

        roads, count = (
            dao.get_road_segments_geojson(
                limit,
                offset,
                name,
                parsed_min_speed,
                parsed_max_speed
            )
        )

        features = []

        for road in roads:

            created_at = road[
                "created_at"
            ]

            if created_at is not None:
                created_at = (
                    created_at.replace(
                        tzinfo=timezone.utc
                    )
                    .isoformat()
                    .replace(
                        "+00:00",
                        "Z"
                    )
                )

            features.append(
                {
                    "type": "Feature",
                    "geometry": road["geom"],
                    "properties": {
                        "road_id": road[
                            "road_id"
                        ],
                        "name": road[
                            "name"
                        ],
                        "speed_limit_kph": road[
                            "speed_limit_kph"
                        ],
                        "is_oneway": road[
                            "is_oneway"
                        ],
                        "direction": road[
                            "direction"
                        ],
                        "created_at": created_at
                    }
                }
            )

        return {
            "type": "FeatureCollection",
            "count": count,
            "limit": limit,
            "offset": offset,
            "features": features
        }