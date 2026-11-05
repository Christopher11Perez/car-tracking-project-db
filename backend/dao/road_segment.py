import json

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from psycopg2.extras import DictCursor

from config.pool import pool


class RoadSegment(BaseModel):
    road_id: Optional[int] = None
    name: str
    speed_limit_kph: Optional[float] = None
    is_oneway: bool
    direction: str
    geom: dict
    created_at: Optional[datetime] = None


class RoadSegmentSummary(BaseModel):
    road_id: int
    name: str
    speed_limit_kph: Optional[float] = None
    created_at: Optional[datetime] = None


class RoadSegmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    speed_limit_kph: Optional[float] = None
    is_oneway: bool
    direction: str
    geom: dict


class RoadSegmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    speed_limit_kph: Optional[float] = None
    is_oneway: Optional[bool] = None
    direction: Optional[str] = None
    geom: Optional[dict] = None


class RoadSegmentDAO:

    def get_all_road_segments(
            self,
            limit: int,
            offset: int,
            name=None,
            min_speed_kph=None,
            max_speed_kph=None,
            bbox=None
    ) -> tuple[list[RoadSegmentSummary], int]:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            conditions = []
            params = []

            if name is not None:
                conditions.append(
                    "rs.name ilike %s"
                )
                params.append(
                    f"%{name}%"
                )

            if min_speed_kph is not None:
                conditions.append(
                    "rs.speed_limit_kph >= %s"
                )
                params.append(
                    min_speed_kph
                )

            if max_speed_kph is not None:
                conditions.append(
                    "rs.speed_limit_kph <= %s"
                )
                params.append(
                    max_speed_kph
                )

            if bbox is not None:
                min_lon, min_lat, max_lon, max_lat = bbox

                conditions.append(
                    """
                    ST_Intersects(
                        rs.geom,
                        ST_MakeEnvelope(
                            %s,
                            %s,
                            %s,
                            %s,
                            4326
                        )
                    )
                    """
                )

                params.extend([
                    min_lon,
                    min_lat,
                    max_lon,
                    max_lat
                ])

            where_clause = ""

            if conditions:
                where_clause = (
                        "where "
                        + " and ".join(conditions)
                )

            count_query = f"""
            select count(*)
            from road_segment rs
            {where_clause}
            """

            cursor.execute(
                count_query,
                tuple(params)
            )

            count = cursor.fetchone()[0]

            query = f"""
            select rs.road_id,
                   rs.name,
                   rs.speed_limit_kph,
                   rs.created_at
            from road_segment rs
            {where_clause}
            order by rs.road_id
            limit %s offset %s
            """

            query_params = params + [
                limit,
                offset
            ]

            cursor.execute(
                query,
                tuple(query_params)
            )

            result: list[RoadSegmentSummary] = []

            for row in cursor:
                result.append(
                    RoadSegmentSummary(**row)
                )

            cursor.close()

            return result, count

        finally:
            pool.putconn(conn)

    def get_road_segment_by_id(
            self,
            road_id: int
    ) -> Optional[RoadSegment]:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            query = """
            select road_id,
                   name,
                   speed_limit_kph,
                   is_oneway,
                   direction,
                   ST_AsGeoJSON(geom)::json as geom,
                   created_at
            from road_segment
            where road_id = %s
            """

            cursor.execute(
                query,
                (road_id,)
            )

            row = cursor.fetchone()

            cursor.close()

            if row is None:
                return None

            return RoadSegment(**row)

        finally:
            pool.putconn(conn)

    def create_road_segment(
            self,
            road_segment: RoadSegmentCreate
    ) -> RoadSegment:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            query = """
            insert into road_segment (
                road_id,
                name,
                speed_limit_kph,
                is_oneway,
                direction,
                geom,
                created_at
            )
            values (
                (
                    select coalesce(
                        max(road_id),
                        0
                    ) + 1
                    from road_segment
                ),
                %s,
                %s,
                %s,
                %s,
                ST_SetSRID(
                    ST_GeomFromGeoJSON(%s),
                    4326
                ),
                current_timestamp
            )
            returning road_id,
                      name,
                      speed_limit_kph,
                      is_oneway,
                      direction,
                      ST_AsGeoJSON(geom)::json as geom,
                      created_at
            """

            cursor.execute(
                query,
                (
                    road_segment.name,
                    road_segment.speed_limit_kph,
                    road_segment.is_oneway,
                    road_segment.direction,
                    json.dumps(
                        road_segment.geom
                    )
                )
            )

            row = cursor.fetchone()

            conn.commit()
            cursor.close()

            return RoadSegment(**row)

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def update_road_segment(
            self,
            road_id: int,
            road_data: dict
    ) -> RoadSegment:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            fields = []
            params = []

            for field, value in road_data.items():

                if field == "geom":
                    fields.append(
                        """
                        geom = ST_SetSRID(
                            ST_GeomFromGeoJSON(%s),
                            4326
                        )
                        """
                    )

                    params.append(
                        json.dumps(value)
                    )

                else:
                    fields.append(
                        f"{field} = %s"
                    )

                    params.append(value)

            params.append(road_id)

            query = f"""
            update road_segment
            set {", ".join(fields)}
            where road_id = %s
            returning road_id,
                      name,
                      speed_limit_kph,
                      is_oneway,
                      direction,
                      ST_AsGeoJSON(geom)::json as geom,
                      created_at
            """

            cursor.execute(
                query,
                tuple(params)
            )

            row = cursor.fetchone()

            conn.commit()
            cursor.close()

            return RoadSegment(**row)

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def delete_road_segment(
            self,
            road_id: int
    ) -> bool:

        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                delete from road_segment
                where road_id = %s
                """,
                (road_id,)
            )

            deleted = cursor.rowcount > 0

            conn.commit()
            cursor.close()

            return deleted

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def get_road_segments_geojson(
            self,
            limit: int,
            offset: int,
            name=None,
            min_speed_kph=None,
            max_speed_kph=None
    ):

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            conditions = []
            params = []

            if name is not None:
                conditions.append(
                    "name ilike %s"
                )

                params.append(
                    f"%{name}%"
                )

            if min_speed_kph is not None:
                conditions.append(
                    "speed_limit_kph >= %s"
                )

                params.append(
                    min_speed_kph
                )

            if max_speed_kph is not None:
                conditions.append(
                    "speed_limit_kph <= %s"
                )

                params.append(
                    max_speed_kph
                )

            where_clause = ""

            if conditions:
                where_clause = (
                    "where "
                    + " and ".join(conditions)
                )

            count_query = f"""
            select count(*)
            from road_segment
            {where_clause}
            """

            cursor.execute(
                count_query,
                tuple(params)
            )

            count = cursor.fetchone()[0]

            query = f"""
            select road_id,
                   name,
                   speed_limit_kph,
                   is_oneway,
                   direction,
                   ST_AsGeoJSON(geom)::json as geom,
                   created_at
            from road_segment
            {where_clause}
            order by road_id
            limit %s offset %s
            """

            query_params = params + [
                limit,
                offset
            ]

            cursor.execute(
                query,
                tuple(query_params)
            )

            rows = []

            for row in cursor:
                rows.append(
                    dict(row)
                )

            cursor.close()

            return rows, count

        finally:
            pool.putconn(conn)