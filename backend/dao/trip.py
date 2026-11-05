import json

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from psycopg2.extras import DictCursor

from config.pool import pool


class Trip(BaseModel):
    trip_id: Optional[int] = None
    vehicle_id: int
    start_ts: datetime
    end_ts: datetime
    start_geom: Optional[dict] = None
    end_geom: Optional[dict] = None
    distance_km: Optional[float] = None


class TripSummary(BaseModel):
    trip_id: int
    vehicle_id: int
    start_ts: datetime
    end_ts: datetime
    distance_km: Optional[float] = None


class VehicleTripSummary(BaseModel):
    trip_id: int
    start_ts: datetime
    end_ts: datetime
    distance_km: Optional[float] = None


class TripCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: int
    start_ts: str
    end_ts: str
    start_geom: Optional[dict] = None
    end_geom: Optional[dict] = None
    distance_km: Optional[float] = None


class TripUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: Optional[int] = None
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None
    start_geom: Optional[dict] = None
    end_geom: Optional[dict] = None
    distance_km: Optional[float] = None


class TripDAO:

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

    def get_all_trips(
            self,
            limit: int,
            offset: int,
            vehicle_id=None,
            from_ts=None,
            to_ts=None
    ) -> tuple[list[TripSummary], int]:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            conditions = []
            params = []

            if vehicle_id is not None:
                conditions.append(
                    "t.vehicle_id = %s"
                )
                params.append(vehicle_id)

            if from_ts is not None:
                conditions.append(
                    "t.start_ts >= %s"
                )
                params.append(from_ts)

            if to_ts is not None:
                conditions.append(
                    "t.end_ts <= %s"
                )
                params.append(to_ts)

            where_clause = ""

            if conditions:
                where_clause = (
                    "where " +
                    " and ".join(conditions)
                )

            count_query = f"""
            select count(*)
            from trip t
            {where_clause}
            """

            cursor.execute(
                count_query,
                tuple(params)
            )

            count = cursor.fetchone()[0]

            query = f"""
            select t.trip_id,
                   t.vehicle_id,
                   t.start_ts,
                   t.end_ts,
                   t.distance_km
            from trip t
            {where_clause}
            order by t.trip_id
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

            result: list[TripSummary] = []

            for row in cursor:
                result.append(
                    TripSummary(**row)
                )

            cursor.close()

            return result, count

        finally:
            pool.putconn(conn)

    def get_trip_by_id(
            self,
            trip_id: int
    ) -> Optional[Trip]:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            query = """
            select trip_id,
                   vehicle_id,
                   start_ts,
                   end_ts,
                   ST_AsGeoJSON(start_geom)::json as start_geom,
                   ST_AsGeoJSON(end_geom)::json as end_geom,
                   distance_km
            from trip
            where trip_id = %s
            """

            cursor.execute(
                query,
                (trip_id,)
            )

            row = cursor.fetchone()

            cursor.close()

            if row is None:
                return None

            return Trip(**row)

        finally:
            pool.putconn(conn)

    def create_trip(
            self,
            new_trip: TripCreate,
            start_ts: datetime,
            end_ts: datetime
    ) -> Trip:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            query = """
            insert into trip (
                trip_id,
                vehicle_id,
                start_ts,
                end_ts,
                start_geom,
                end_geom,
                distance_km
            )
            values (
                (
                    select coalesce(
                        max(trip_id),
                        0
                    ) + 1
                    from trip
                ),
                %s,
                %s,
                %s,
                case
                    when %s is null then null
                    else ST_SetSRID(
                        ST_GeomFromGeoJSON(%s),
                        4326
                    )
                end,
                case
                    when %s is null then null
                    else ST_SetSRID(
                        ST_GeomFromGeoJSON(%s),
                        4326
                    )
                end,
                %s
            )
            returning trip_id,
                      vehicle_id,
                      start_ts,
                      end_ts,
                      ST_AsGeoJSON(start_geom)::json as start_geom,
                      ST_AsGeoJSON(end_geom)::json as end_geom,
                      distance_km
            """

            start_geom_json = (
                json.dumps(new_trip.start_geom)
                if new_trip.start_geom is not None
                else None
            )

            end_geom_json = (
                json.dumps(new_trip.end_geom)
                if new_trip.end_geom is not None
                else None
            )

            cursor.execute(
                query,
                (
                    new_trip.vehicle_id,
                    start_ts,
                    end_ts,
                    start_geom_json,
                    start_geom_json,
                    end_geom_json,
                    end_geom_json,
                    new_trip.distance_km
                )
            )

            row = cursor.fetchone()

            conn.commit()
            cursor.close()

            return Trip(**row)

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def update_trip(
            self,
            trip_id: int,
            trip_data: dict
    ) -> Trip:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            fields = []
            params = []

            for field, value in trip_data.items():

                if field in (
                    "start_geom",
                    "end_geom"
                ):
                    fields.append(
                        f"""
                        {field} = ST_SetSRID(
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

            params.append(trip_id)

            query = f"""
            update trip
            set {", ".join(fields)}
            where trip_id = %s
            returning trip_id,
                      vehicle_id,
                      start_ts,
                      end_ts,
                      ST_AsGeoJSON(start_geom)::json as start_geom,
                      ST_AsGeoJSON(end_geom)::json as end_geom,
                      distance_km
            """

            cursor.execute(
                query,
                tuple(params)
            )

            row = cursor.fetchone()

            conn.commit()
            cursor.close()

            return Trip(**row)

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def delete_trip(
            self,
            trip_id: int
    ) -> bool:

        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                delete from trip
                where trip_id = %s
                """,
                (trip_id,)
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

    def get_vehicle_trips(
            self,
            vehicle_id: int,
            limit: int,
            offset: int,
            from_ts=None,
            to_ts=None
    ) -> tuple[list[VehicleTripSummary], int]:

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
                    "start_ts >= %s"
                )
                params.append(from_ts)

            if to_ts is not None:
                conditions.append(
                    "end_ts <= %s"
                )
                params.append(to_ts)

            where_clause = (
                "where " +
                " and ".join(conditions)
            )

            count_query = f"""
            select count(*)
            from trip
            {where_clause}
            """

            cursor.execute(
                count_query,
                tuple(params)
            )

            count = cursor.fetchone()[0]

            query = f"""
            select trip_id,
                   start_ts,
                   end_ts,
                   distance_km
            from trip
            {where_clause}
            order by start_ts
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

            result: list[VehicleTripSummary] = []

            for row in cursor:
                result.append(
                    VehicleTripSummary(**row)
                )

            cursor.close()

            return result, count

        finally:
            pool.putconn(conn)