from db import get_connection
import pandas as pd

def load_driver(df):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute(
                    """
                    INSERT INTO driver
                        (driver_id, first_name, last_name, license_number, hired_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (driver_id) DO NOTHING;
                    """,
                    (
                        int(row["driver_id"]),
                        row["first_name"],
                        row["last_name"],
                        row["license_number"],
                        None if pd.isna(row["hired_at"]) else row["hired_at"].to_pydatetime(),
                    )
                )
        conn.commit()
        print("driver loaded successfully.")
    finally:
        conn.close()

def load_fuel_type(df):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute(
                    """
                    INSERT INTO fuel_type (fuel_type_id, name)
                    VALUES (%s, %s)
                    ON CONFLICT (fuel_type_id) DO NOTHING;
                    """,
                    (
                        int(row["fuel_type_id"]),
                        row["name"]
                    )
                )

        conn.commit()
        print("fuel_type loaded successfully.")

    finally:
        conn.close()

def load_vehicle_kind(df):
    conn = get_connection()
    
    try:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute(
                    """
                    INSERT INTO vehicle_kind (vehicle_kind_id, name)
                    VALUES (%s, %s)
                    ON CONFLICT (vehicle_kind_id) DO NOTHING;
                    """,
                    (
                        int(row["vehicle_kind_id"]),
                        row["name"]
                    )
                )

        conn.commit()
        print("vehicle_kind loaded successfully.")

    finally:
        conn.close()

def load_parking_area(df):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute(
                    """
                    INSERT INTO parking_area
                        (parking_area_id, name, capacity, geom, created_at)
                    VALUES (%s, %s, %s, ST_GeomFromEWKB(decode(%s, 'hex')), %s)
                    ON CONFLICT (parking_area_id) DO NOTHING;
                    """,
                    (
                        int(row["parking_area_id"]),
                        row["name"],
                        int(row["capacity"]),
                        row["geom"],
                        None if pd.isna(row["created_at"]) else row["created_at"].to_pydatetime(),
                    )
                )
        conn.commit()
        print("parking_area loaded successfully.")
    finally:
        conn.close()    

def load_vehicle_type(df):
    conn = get_connection()
    
    try:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute(
                    """
                    INSERT INTO vehicle_type (vehicle_type_id, vehicle_kind_id, fuel_type_id, emissions_rating, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (vehicle_type_id) DO NOTHING;
                    """,
                    (
                        int(row["vehicle_type_id"]),
                        int(row["vehicle_kind_id"]),
                        int(row["fuel_type_id"]),
                        None if pd.isna(row["emissions_rating"]) else float(row["emissions_rating"]),
                        None if pd.isna(row["created_at"]) else row["created_at"].to_pydatetime(),
                    )
                )

        conn.commit()
        print("vehicle_type loaded successfully.")

    finally:
        conn.close()

def load_vehicle(df):
    conn = get_connection()
    
    try:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute(
                    """
                    INSERT INTO vehicle (vehicle_id, vehicle_type_id, vehicle_status_id, plate_number, make, model, year, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (vehicle_id) DO NOTHING;
                    """,
                    (
                        int(row["vehicle_id"]),
                        int(row["vehicle_type_id"]),
                        int(row["vehicle_status_id"]),
                        row["plate_number"],
                        row["make"],
                        row["model"],
                        int(row["year"]),
                        None if pd.isna(row["created_at"]) else row["created_at"].to_pydatetime(),
                    )
                )

        conn.commit()
        print("vehicle loaded successfully.")

    finally:
        conn.close()

def load_location_ping(df):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute(
                    """
                    INSERT INTO location_ping
                        (ping_id, vehicle_id, ts, geom, speed_kph, heading_deg)
                    VALUES (%s, %s, %s, ST_GeomFromEWKB(decode(%s, 'hex')), %s, %s)
                    ON CONFLICT (ping_id) DO NOTHING;
                    """,
                    (
                        int(row["ping_id"]),
                        int(row["vehicle_id"]),
                        None if pd.isna(row["ts"]) else row["ts"].to_pydatetime(),
                        row["geom"],
                        None if pd.isna(row["speed_kph"]) else float(row["speed_kph"]),
                        None if pd.isna(row["heading_deg"]) else float(row["heading_deg"])
                    )
                )
        conn.commit()
        print("location_ping loaded successfully.")
    finally:
        conn.close()

def load_trip(df):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute(
                    """
                    INSERT INTO trip
                        (trip_id, vehicle_id, start_ts, end_ts, start_geom, end_geom, distance_km)
                    VALUES (%s, %s, %s, %s, ST_GeomFromEWKB(decode(%s, 'hex')), ST_GeomFromEWKB(decode(%s, 'hex')), %s)
                    ON CONFLICT (trip_id) DO NOTHING;
                    """,
                    (
                        int(row["trip_id"]),
                        int(row["vehicle_id"]),
                        None if pd.isna(row["start_ts"]) else row["start_ts"].to_pydatetime(),
                        None if pd.isna(row["end_ts"]) else row["end_ts"].to_pydatetime(),
                        row["start_geom"],
                        row["end_geom"],
                        None if pd.isna(row["distance_km"]) else float(row["distance_km"])
                    )
                )
        conn.commit()
        print("trip loaded successfully.")
    finally:
        conn.close()

def load_vehicle_assignment(df):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute(
                    """
                    INSERT INTO vehicle_assignment
                        (assignment_id, vehicle_id, driver_id, assigned_from, assigned_to)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (assignment_id) DO NOTHING;
                    """,
                    (
                        int(row["assignment_id"]),
                        int(row["vehicle_id"]),
                        int(row["driver_id"]),
                        None if pd.isna(row["assigned_from"]) else row["assigned_from"].to_pydatetime(),
                        None if pd.isna(row["assigned_to"]) else row["assigned_to"].to_pydatetime(),
                    )
                )
        conn.commit()
        print("vehicle_assignment loaded successfully.")
    finally:
        conn.close()

def load_road_segment(df):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute(
                    """
                    INSERT INTO road_segment
                        (road_id, name, speed_limit_kph, geom, created_at, is_oneway, direction)
                    VALUES (%s, %s, %s, ST_GeomFromEWKB(decode(%s, 'hex')), %s, %s, %s)
                    ON CONFLICT (road_id) DO NOTHING;
                    """,
                    (
                        int(row["road_id"]),
                        row["name"],
                        int(row["speed_limit_kph"]),
                        row["geom"],
                        None if pd.isna(row["created_at"]) else row["created_at"].to_pydatetime(),
                        None if pd.isna(row["is_oneway"]) else bool(row["is_oneway"]),
                        row["direction"]
                    )
                )
        conn.commit()
        print("road_segment loaded successfully.")
    finally:
        conn.close()

def load_vehicle_status(df):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute(
                    """
                    INSERT INTO vehicle_status (vehicle_status_id, name)
                    VALUES (%s, %s)
                    ON CONFLICT (vehicle_status_id) DO NOTHING;
                    """,
                    (
                        int(row["vehicle_status_id"]),
                        row["name"]
                    )
                )

        conn.commit()
        print("vehicle_status loaded successfully.")

    finally:
        conn.close()