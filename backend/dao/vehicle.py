from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from psycopg2.extras import DictCursor

from config.pool import pool


class Vehicle(BaseModel):
    vehicle_id: Optional[int] = None
    vehicle_type_id: int
    vehicle_status_id: int
    plate_number: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: int
    created_at: Optional[datetime] = None


class VehicleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_type_id: int
    vehicle_status_id: int
    plate_number: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: int


class VehicleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_type_id: Optional[int] = None
    vehicle_status_id: Optional[int] = None
    plate_number: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None


class VehicleDAO:

    def get_all_vehicles(
            self,
            limit: int,
            offset: int,
            status=None,
            plate_number=None
    ) -> tuple[list[Vehicle], int]:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(cursor_factory=DictCursor)

            conditions = []
            params = []

            if status is not None:
                if status.isdigit():
                    conditions.append("v.vehicle_status_id = %s")
                    params.append(int(status))
                else:
                    conditions.append("lower(vs.name) = lower(%s)")
                    params.append(status)

            if plate_number is not None:
                conditions.append("v.plate_number ilike %s")
                params.append(f"%{plate_number}%")

            where_clause = ""

            if conditions:
                where_clause = "where " + " and ".join(conditions)

            count_query = f"""
            select count(*)
            from vehicle v
            join vehicle_status vs
                on v.vehicle_status_id = vs.vehicle_status_id
            {where_clause}
            """

            cursor.execute(count_query, tuple(params))
            count = cursor.fetchone()[0]

            query = f"""
            select v.vehicle_id,
                   v.vehicle_type_id,
                   v.vehicle_status_id,
                   v.plate_number,
                   v.make,
                   v.model,
                   v.year,
                   v.created_at
            from vehicle v
            join vehicle_status vs
                on v.vehicle_status_id = vs.vehicle_status_id
            {where_clause}
            order by v.vehicle_id
            limit %s offset %s
            """

            query_params = params + [limit, offset]

            cursor.execute(query, tuple(query_params))

            result: list[Vehicle] = []

            for row in cursor:
                result.append(Vehicle(**row))

            cursor.close()

            return result, count

        finally:
            pool.putconn(conn)

    def get_vehicle_by_id(
            self,
            vehicle_id: int
    ) -> Optional[Vehicle]:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(cursor_factory=DictCursor)

            query = """
            select vehicle_id,
                   vehicle_type_id,
                   vehicle_status_id,
                   plate_number,
                   make,
                   model,
                   year,
                   created_at
            from vehicle
            where vehicle_id = %s
            """

            cursor.execute(query, (vehicle_id,))
            row = cursor.fetchone()

            cursor.close()

            if row is None:
                return None

            return Vehicle(**row)

        finally:
            pool.putconn(conn)

    def get_current_location(
            self,
            vehicle_id: int
    ):

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            query = """
            select
                v.vehicle_id,
                v.plate_number,
                vs.name as status,
                vk.name as vehicle_kind,
                ft.name as fuel_type,
                vt.emissions_rating,
                lp.ts as last_ts,
                ST_AsGeoJSON(lp.geom)::json as last_geom,
                lp.speed_kph,
                lp.heading_deg
            from vehicle v
            join vehicle_status vs
                on v.vehicle_status_id = vs.vehicle_status_id
            join vehicle_type vt
                on v.vehicle_type_id = vt.vehicle_type_id
            join vehicle_kind vk
                on vt.vehicle_kind_id = vk.vehicle_kind_id
            join fuel_type ft
                on vt.fuel_type_id = ft.fuel_type_id
            join location_ping lp
                on v.vehicle_id = lp.vehicle_id
            where v.vehicle_id = %s
            order by lp.ts desc, lp.ping_id desc
            limit 1
            """

            cursor.execute(
                query,
                (vehicle_id,)
            )

            row = cursor.fetchone()

            cursor.close()

            if row is None:
                return None

            return dict(row)

        finally:
            pool.putconn(conn)

    def vehicle_type_exists(
            self,
            vehicle_type_id: int
    ) -> bool:

        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                select 1
                from vehicle_type
                where vehicle_type_id = %s
                """,
                (vehicle_type_id,)
            )

            result = cursor.fetchone()
            cursor.close()

            return result is not None

        finally:
            pool.putconn(conn)

    def vehicle_status_exists(
            self,
            vehicle_status_id: int
    ) -> bool:

        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                select 1
                from vehicle_status
                where vehicle_status_id = %s
                """,
                (vehicle_status_id,)
            )

            result = cursor.fetchone()
            cursor.close()

            return result is not None

        finally:
            pool.putconn(conn)

    def plate_number_exists(
            self,
            plate_number: str,
            exclude_vehicle_id=None
    ) -> bool:

        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            if exclude_vehicle_id is None:
                query = """
                select 1
                from vehicle
                where lower(plate_number) = lower(%s)
                """
                params = (plate_number,)

            else:
                query = """
                select 1
                from vehicle
                where lower(plate_number) = lower(%s)
                  and vehicle_id <> %s
                """
                params = (
                    plate_number,
                    exclude_vehicle_id
                )

            cursor.execute(query, params)

            result = cursor.fetchone()
            cursor.close()

            return result is not None

        finally:
            pool.putconn(conn)

    def create_vehicle(
            self,
            new_vehicle: VehicleCreate
    ) -> Vehicle:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            query = """
            insert into vehicle (
                vehicle_type_id,
                vehicle_status_id,
                plate_number,
                make,
                model,
                year,
                created_at
            )
            values (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                current_timestamp
            )
            returning vehicle_id,
                      vehicle_type_id,
                      vehicle_status_id,
                      plate_number,
                      make,
                      model,
                      year,
                      created_at
            """

            cursor.execute(
                query,
                (
                    new_vehicle.vehicle_type_id,
                    new_vehicle.vehicle_status_id,
                    new_vehicle.plate_number,
                    new_vehicle.make,
                    new_vehicle.model,
                    new_vehicle.year
                )
            )

            row = cursor.fetchone()

            conn.commit()
            cursor.close()

            return Vehicle(**row)

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def update_vehicle(
            self,
            vehicle_id: int,
            vehicle_data: dict
    ) -> Vehicle:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            fields = []
            params = []

            for field, value in vehicle_data.items():
                fields.append(f"{field} = %s")
                params.append(value)

            params.append(vehicle_id)

            query = f"""
            update vehicle
            set {", ".join(fields)}
            where vehicle_id = %s
            returning vehicle_id,
                      vehicle_type_id,
                      vehicle_status_id,
                      plate_number,
                      make,
                      model,
                      year,
                      created_at
            """

            cursor.execute(
                query,
                tuple(params)
            )

            row = cursor.fetchone()

            conn.commit()
            cursor.close()

            return Vehicle(**row)

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def vehicle_has_references(
            self,
            vehicle_id: int
    ) -> bool:

        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            query = """
            select
                exists(
                    select 1
                    from location_ping
                    where vehicle_id = %s
                )
                or exists(
                    select 1
                    from trip
                    where vehicle_id = %s
                )
                or exists(
                    select 1
                    from vehicle_assignment
                    where vehicle_id = %s
                )
            """

            cursor.execute(
                query,
                (
                    vehicle_id,
                    vehicle_id,
                    vehicle_id
                )
            )

            result = cursor.fetchone()[0]

            cursor.close()

            return result

        finally:
            pool.putconn(conn)

    def delete_vehicle(
            self,
            vehicle_id: int
    ) -> bool:

        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                delete from vehicle
                where vehicle_id = %s
                """,
                (vehicle_id,)
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