import json

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from psycopg2.extras import DictCursor

from config.pool import pool


class ParkingArea(BaseModel):
    parking_area_id: Optional[int] = None
    name: str
    capacity: Optional[int] = None
    geom: dict
    created_at: Optional[datetime] = None


class ParkingAreaSummary(BaseModel):
    parking_area_id: int
    name: str
    capacity: Optional[int] = None
    created_at: Optional[datetime] = None


class ParkingAreaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    capacity: Optional[int] = None
    geom: dict


class ParkingAreaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    capacity: Optional[int] = None
    geom: Optional[dict] = None


class ParkingAreaDAO:

    def get_all_parking_areas(
            self,
            limit: int,
            offset: int,
            name=None,
            bbox=None
    ) -> tuple[list[ParkingAreaSummary], int]:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            conditions = []
            params = []

            if name is not None:
                conditions.append(
                    "pa.name ilike %s"
                )
                params.append(
                    f"%{name}%"
                )

            if bbox is not None:
                min_lon, min_lat, max_lon, max_lat = bbox

                conditions.append(
                    """
                    ST_Intersects(
                        pa.geom,
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
            from parking_area pa
            {where_clause}
            """

            cursor.execute(
                count_query,
                tuple(params)
            )

            count = cursor.fetchone()[0]

            query = f"""
            select pa.parking_area_id,
                   pa.name,
                   pa.capacity,
                   pa.created_at
            from parking_area pa
            {where_clause}
            order by pa.parking_area_id
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

            result: list[ParkingAreaSummary] = []

            for row in cursor:
                result.append(
                    ParkingAreaSummary(**row)
                )

            cursor.close()

            return result, count

        finally:
            pool.putconn(conn)

    def get_parking_area_by_id(
            self,
            parking_area_id: int
    ) -> Optional[ParkingArea]:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            query = """
            select parking_area_id,
                   name,
                   capacity,
                   ST_AsGeoJSON(geom)::json as geom,
                   created_at
            from parking_area
            where parking_area_id = %s
            """

            cursor.execute(
                query,
                (parking_area_id,)
            )

            row = cursor.fetchone()

            cursor.close()

            if row is None:
                return None

            return ParkingArea(**row)

        finally:
            pool.putconn(conn)

    def geometry_is_valid(
            self,
            geom: dict
    ) -> bool:

        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            query = """
            select ST_IsValid(
                ST_SetSRID(
                    ST_GeomFromGeoJSON(%s),
                    4326
                )
            )
            """

            cursor.execute(
                query,
                (
                    json.dumps(geom),
                )
            )

            result = cursor.fetchone()[0]

            cursor.close()

            return result

        except Exception:
            conn.rollback()
            return False

        finally:
            pool.putconn(conn)

    def create_parking_area(
            self,
            parking_area: ParkingAreaCreate
    ) -> ParkingArea:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            query = """
            insert into parking_area (
                parking_area_id,
                name,
                capacity,
                geom,
                created_at
            )
            values (
                (
                    select coalesce(
                        max(parking_area_id),
                        0
                    ) + 1
                    from parking_area
                ),
                %s,
                %s,
                ST_SetSRID(
                    ST_GeomFromGeoJSON(%s),
                    4326
                ),
                current_timestamp
            )
            returning parking_area_id,
                      name,
                      capacity,
                      ST_AsGeoJSON(geom)::json as geom,
                      created_at
            """

            cursor.execute(
                query,
                (
                    parking_area.name,
                    parking_area.capacity,
                    json.dumps(
                        parking_area.geom
                    )
                )
            )

            row = cursor.fetchone()

            conn.commit()
            cursor.close()

            return ParkingArea(**row)

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def update_parking_area(
            self,
            parking_area_id: int,
            parking_data: dict
    ) -> ParkingArea:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            fields = []
            params = []

            for field, value in parking_data.items():

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

            params.append(
                parking_area_id
            )

            query = f"""
            update parking_area
            set {", ".join(fields)}
            where parking_area_id = %s
            returning parking_area_id,
                      name,
                      capacity,
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

            return ParkingArea(**row)

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def delete_parking_area(
            self,
            parking_area_id: int
    ) -> bool:

        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                delete from parking_area
                where parking_area_id = %s
                """,
                (parking_area_id,)
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