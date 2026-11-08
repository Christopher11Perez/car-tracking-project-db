from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from psycopg2.extras import DictCursor

from config.pool import pool


class VehicleAssignment(BaseModel):
    assignment_id: Optional[int] = None
    vehicle_id: int
    driver_id: int
    assigned_from: datetime
    assigned_to: Optional[datetime] = None


class VehicleAssignmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: int
    driver_id: int
    assigned_from: str
    assigned_to: Optional[str] = None


class VehicleAssignmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    assigned_from: Optional[str] = None
    assigned_to: Optional[str] = None


class VehicleAssignmentDAO:

    def vehicle_exists(self, vehicle_id: int) -> bool:
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

    def driver_exists(self, driver_id: int) -> bool:
        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                select 1
                from driver
                where driver_id = %s
                """,
                (driver_id,)
            )

            result = cursor.fetchone()
            cursor.close()

            return result is not None

        finally:
            pool.putconn(conn)

    def get_all_assignments(
            self,
            limit: int,
            offset: int,
            vehicle_id=None,
            driver_id=None,
            active=None
    ) -> tuple[list[VehicleAssignment], int]:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            conditions = []
            params = []

            if vehicle_id is not None:
                conditions.append(
                    "vehicle_id = %s"
                )
                params.append(vehicle_id)

            if driver_id is not None:
                conditions.append(
                    "driver_id = %s"
                )
                params.append(driver_id)

            if active is True:
                conditions.append(
                    "assigned_to is null"
                )

            elif active is False:
                conditions.append(
                    "assigned_to is not null"
                )

            where_clause = ""

            if conditions:
                where_clause = (
                    "where " +
                    " and ".join(conditions)
                )

            count_query = f"""
            select count(*)
            from vehicle_assignment
            {where_clause}
            """

            cursor.execute(
                count_query,
                tuple(params)
            )

            count = cursor.fetchone()[0]

            query = f"""
            select assignment_id,
                   vehicle_id,
                   driver_id,
                   assigned_from,
                   assigned_to
            from vehicle_assignment
            {where_clause}
            order by assignment_id
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

            result = []

            for row in cursor:
                result.append(
                    VehicleAssignment(**row)
                )

            cursor.close()

            return result, count

        finally:
            pool.putconn(conn)

    def get_assignment_by_id(
            self,
            assignment_id: int
    ) -> Optional[VehicleAssignment]:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            cursor.execute(
                """
                select assignment_id,
                       vehicle_id,
                       driver_id,
                       assigned_from,
                       assigned_to
                from vehicle_assignment
                where assignment_id = %s
                """,
                (assignment_id,)
            )

            row = cursor.fetchone()

            cursor.close()

            if row is None:
                return None

            return VehicleAssignment(**row)

        finally:
            pool.putconn(conn)

    def create_assignment(
            self,
            new_assignment: VehicleAssignmentCreate,
            assigned_from: datetime,
            assigned_to: Optional[datetime]
    ) -> VehicleAssignment:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            query = """
            insert into vehicle_assignment (
                vehicle_id,
                driver_id,
                assigned_from,
                assigned_to
            )
            values (
                %s,
                %s,
                %s,
                %s
            )
            returning assignment_id,
                      vehicle_id,
                      driver_id,
                      assigned_from,
                      assigned_to
            """

            cursor.execute(
                query,
                (
                    new_assignment.vehicle_id,
                    new_assignment.driver_id,
                    assigned_from,
                    assigned_to
                )
            )

            row = cursor.fetchone()

            conn.commit()
            cursor.close()

            return VehicleAssignment(**row)

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def update_assignment(
            self,
            assignment_id: int,
            assignment_data: dict
    ) -> VehicleAssignment:

        conn = pool.getconn()

        try:
            cursor = conn.cursor(
                cursor_factory=DictCursor
            )

            fields = []
            params = []

            for field, value in assignment_data.items():
                fields.append(
                    f"{field} = %s"
                )
                params.append(value)

            params.append(
                assignment_id
            )

            query = f"""
            update vehicle_assignment
            set {", ".join(fields)}
            where assignment_id = %s
            returning assignment_id,
                      vehicle_id,
                      driver_id,
                      assigned_from,
                      assigned_to
            """

            cursor.execute(
                query,
                tuple(params)
            )

            row = cursor.fetchone()

            conn.commit()
            cursor.close()

            return VehicleAssignment(**row)

        except Exception:
            conn.rollback()
            raise

        finally:
            pool.putconn(conn)

    def delete_assignment(
            self,
            assignment_id: int
    ) -> bool:

        conn = pool.getconn()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                delete from vehicle_assignment
                where assignment_id = %s
                """,
                (assignment_id,)
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