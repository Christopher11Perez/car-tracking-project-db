from psycopg2.extras import DictCursor
from config.pool import pool

class VehicleDAO:
    def get_vehicle_by_id(self, vehicle_id: int):
        conn = pool.getconn()
        try:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(
                    """
                    select vehicle_id, vehicle_type_id, vehicle_status_id,
                           plate_number, make, model, year, created_at
                    from vehicle
                    where vehicle_id = %s
                    """,
                    (vehicle_id,),
                )
                return cursor.fetchone()
        finally:
            pool.putconn(conn)