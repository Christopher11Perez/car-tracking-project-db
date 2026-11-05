import json

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from psycopg2.extras import DictCursor

from config.pool import pool


class LocationPing(BaseModel):
    ping_id: Optional[int] = None
    vehicle_id: int
    ts: datetime
    geom: dict
    speed_kph: Optional[float] = None
    heading_deg: Optional[float] = None


class LocationPingSummary(BaseModel):
    ping_id: int
    vehicle_id: int
    ts: datetime
    speed_kph: Optional[float] = None
    heading_deg: Optional[float] = None


class VehiclePingSummary(BaseModel):
    ping_id: int
    ts: datetime
    geom: dict
    speed_kph: Optional[float] = None
    heading_deg: Optional[float] = None


class LocationPingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: int
    ts: str
    geom: dict
    speed_kph: Optional[float] = None
    heading_deg: Optional[float] = None


class LocationPingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: Optional[int] = None
    ts: Optional[str] = None
    geom: Optional[dict] = None
    speed_kph: Optional[float] = None
    heading_deg: Optional[float] = None


class LocationPingDAO:

    def vehicle_exists(
            self,
            vehicle_id: int
    ) -> bool:

        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                select 1
                from vehicle
                where vehicle_id = %s
                """,
                (vehicle_id,)
            )

            result = cursor.fetchone()
            cursor.close()

            return result is not None

        finally:
            pool.putconn(conn)

    def get_all_location_pings(
            self,
            limit: int,
            offset: int,
            vehicle_id=None,
            from_ts=None,
            to_ts=None,
            bbox=None
    ) -> tuple[list[LocationPingSummary], int]:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            conditions = []
            params = []

            if vehicle_id is not None:
                conditions.append(
                    "lp.vehicle_id = %s"
                )
                params.append(vehicle_id)

            if from_ts is not None:
                conditions.append(
                    "lp.ts >= %s"
                )
                params.append(from_ts)

            if to_ts is not None:
                conditions.append(
                    "lp.ts <= %s"
                )
                params.append(to_ts)

            if bbox is not None:
                min_lon, min_lat, max_lon, max_lat = bbox

                conditions.append(
                    """
                    ST_Intersects(
                        lp.geom,
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
                    "where " +
                    " and ".join(conditions)
                )

            count_query = f"""
            select count(*)
            from location_ping lp
            {where_clause}
            """

            cursor.execute(
                count_query,
                tuple(params)
            )

            count = cursor.fetchone()[0]

            query = f"""
            select lp.ping_id,
                   lp.vehicle_id,
                   lp.ts,
                   lp.speed_kph,
                   lp.heading_deg
            from location_ping lp
            {where_clause}
            order by lp.ping_id
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

            result: list[LocationPingSummary] = []

            for row in cursor:
                result.append(
                    LocationPingSummary(**row)
                )

            cursor.close()

            return result, count

        finally:
            pool.putconn(conn)

    def get_location_ping_by_id(
            self,
            ping_id: int
    ) -> Optional[LocationPing]:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            query = """
            select ping_id,
                   vehicle_id,
                   ts,
                   ST_AsGeoJSON(geom)::json as geom,
                   speed_kph,
                   heading_deg
            from location_ping
            where ping_id = %s
            """

            cursor.execute(
                query,
                (ping_id,)
            )

            row = cursor.fetchone()

            cursor.close()

            if row is None:
                return None

            return LocationPing(**row)

        finally:
            pool.putconn(conn)

    def create_location_ping(
            self,
            new_ping: LocationPingCreate,
            parsed_ts: datetime
    ) -> LocationPing:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            query = """
            insert into location_ping (
                ping_id,
                vehicle_id,
                ts,
                geom,
                speed_kph,
                heading_deg
            )
            values (
                (
                    select coalesce(
                        max(ping_id),
                        0
                    ) + 1
                    from location_ping
                ),
                %s,
                %s,
                ST_SetSRID(
                    ST_GeomFromGeoJSON(%s),
                    4326
                ),
                %s,
                %s
            )
            returning ping_id,
                      vehicle_id,
                      ts,
                      ST_AsGeoJSON(geom)::json as geom,
                      speed_kph,
                      heading_deg
            """

            cursor.execute(
                query,
                (
                    new_ping.vehicle_id,
                    parsed_ts,
                    json.dumps(
                        new_ping.geom
                    ),
                    new_ping.speed_kph,
                    new_ping.heading_deg
                )
            )

            row = cursor.fetchone()

            conn.commit()
            cursor.close()

            return LocationPing(**row)

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def update_location_ping(
            self,
            ping_id: int,
            ping_data: dict
    ) -> LocationPing:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            fields = []
            params = []

            for field, value in ping_data.items():

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

            params.append(ping_id)

            query = f"""
            update location_ping
            set {", ".join(fields)}
            where ping_id = %s
            returning ping_id,
                      vehicle_id,
                      ts,
                      ST_AsGeoJSON(geom)::json as geom,
                      speed_kph,
                      heading_deg
            """

            cursor.execute(
                query,
                tuple(params)
            )

            row = cursor.fetchone()

            conn.commit()
            cursor.close()

            return LocationPing(**row)

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def delete_location_ping(
            self,
            ping_id: int
    ) -> bool:

        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                delete from location_ping
                where ping_id = %s
                """,
                (ping_id,)
            )

            deleted = (
                cursor.rowcount > 0
            )

            conn.commit()
            cursor.close()

            return deleted

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def get_vehicle_pings(
            self,
            vehicle_id: int,
            limit: int,
            offset: int,
            from_ts=None,
            to_ts=None
    ) -> tuple[list[VehiclePingSummary], int]:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            conditions = [
                "vehicle_id = %s"
            ]

            params = [
                vehicle_id
            ]

            if from_ts is not None:
                conditions.append(
                    "ts >= %s"
                )
                params.append(from_ts)

            if to_ts is not None:
                conditions.append(
                    "ts <= %s"
                )
                params.append(to_ts)

            where_clause = (
                "where " +
                " and ".join(conditions)
            )

            count_query = f"""
            select count(*)
            from location_ping
            {where_clause}
            """

            cursor.execute(
                count_query,
                tuple(params)
            )

            count = cursor.fetchone()[0]

            query = f"""
            select ping_id,
                   ts,
                   ST_AsGeoJSON(geom)::json as geom,
                   speed_kph,
                   heading_deg
            from location_ping
            {where_clause}
            order by ts
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

            result: list[VehiclePingSummary] = []

            for row in cursor:
                result.append(
                    VehiclePingSummary(**row)
                )

            cursor.close()

            return result, count

        finally:
            pool.putconn(conn)