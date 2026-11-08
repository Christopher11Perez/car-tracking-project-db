from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from psycopg2.extras import DictCursor

from config.pool import pool


class Driver(BaseModel):
    driver_id: Optional[int] = None
    first_name: str
    last_name: str
    license_number: str
    hired_at: datetime


class DriverCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str
    last_name: str
    license_number: str
    hired_at: str


class DriverUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    license_number: Optional[str] = None
    hired_at: Optional[str] = None


class DriverDAO:

    def get_all_drivers(
            self,
            limit: int,
            offset: int,
            name=None,
            license_number=None
    ) -> tuple[list[Driver], int]:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            conditions = []
            params = []

            if name is not None:
                conditions.append(
                    """
                    (
                        first_name ilike %s
                        or last_name ilike %s
                    )
                    """
                )

                params.extend([
                    f"%{name}%",
                    f"%{name}%"
                ])

            if license_number is not None:
                conditions.append(
                    "license_number ilike %s"
                )

                params.append(
                    f"%{license_number}%"
                )

            where_clause = ""

            if conditions:
                where_clause = (
                    "where " +
                    " and ".join(conditions)
                )

            count_query = f"""
            select count(*)
            from driver
            {where_clause}
            """

            cursor.execute(
                count_query,
                tuple(params)
            )

            count = cursor.fetchone()[0]

            query = f"""
            select driver_id,
                   first_name,
                   last_name,
                   license_number,
                   hired_at
            from driver
            {where_clause}
            order by driver_id
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

            result: list[Driver] = []

            for row in cursor:
                result.append(
                    Driver(**row)
                )

            cursor.close()

            return result, count

        finally:
            pool.putconn(conn)

    def get_driver_by_id(
            self,
            driver_id: int
    ) -> Optional[Driver]:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            query = """
            select driver_id,
                   first_name,
                   last_name,
                   license_number,
                   hired_at
            from driver
            where driver_id = %s
            """

            cursor.execute(
                query,
                (driver_id,)
            )

            row = cursor.fetchone()

            cursor.close()

            if row is None:
                return None

            return Driver(**row)

        finally:
            pool.putconn(conn)

    def license_number_exists(
            self,
            license_number: str,
            exclude_driver_id=None
    ) -> bool:

        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            if exclude_driver_id is None:
                query = """
                select 1
                from driver
                where lower(license_number) = lower(%s)
                """

                params = (
                    license_number,
                )

            else:
                query = """
                select 1
                from driver
                where lower(license_number) = lower(%s)
                  and driver_id <> %s
                """

                params = (
                    license_number,
                    exclude_driver_id
                )

            cursor.execute(
                query,
                params
            )

            result = cursor.fetchone()

            cursor.close()

            return result is not None

        finally:
            pool.putconn(conn)

    def create_driver(
            self,
            new_driver: DriverCreate,
            hired_at: datetime
    ) -> Driver:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            query = """
            insert into driver (
                first_name,
                last_name,
                license_number,
                hired_at
            )
            values (
                %s,
                %s,
                %s,
                %s
            )
            returning driver_id,
                      first_name,
                      last_name,
                      license_number,
                      hired_at
            """

            cursor.execute(
                query,
                (
                    new_driver.first_name,
                    new_driver.last_name,
                    new_driver.license_number,
                    hired_at
                )
            )

            row = cursor.fetchone()

            conn.commit()
            cursor.close()

            return Driver(**row)

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def update_driver(
            self,
            driver_id: int,
            driver_data: dict
    ) -> Driver:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            fields = []
            params = []

            for field, value in driver_data.items():
                fields.append(
                    f"{field} = %s"
                )
                params.append(value)

            params.append(driver_id)

            query = f"""
            update driver
            set {", ".join(fields)}
            where driver_id = %s
            returning driver_id,
                      first_name,
                      last_name,
                      license_number,
                      hired_at
            """

            cursor.execute(
                query,
                tuple(params)
            )

            row = cursor.fetchone()

            conn.commit()
            cursor.close()

            return Driver(**row)

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def driver_has_assignments(
            self,
            driver_id: int
    ) -> bool:

        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                select 1
                from vehicle_assignment
                where driver_id = %s
                limit 1
                """,
                (driver_id,)
            )

            result = cursor.fetchone()

            cursor.close()

            return result is not None

        finally:
            pool.putconn(conn)

    def delete_driver(
            self,
            driver_id: int
    ) -> bool:

        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                delete from driver
                where driver_id = %s
                """,
                (driver_id,)
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