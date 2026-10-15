from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

FILES = [
    "driver.parquet",
    "fuel_type.parquet",
    "location_ping.parquet",
    "parking_area.parquet",
    "road_segment.parquet",
    "trip.parquet",
    "vehicle.parquet",
    "vehicle_assignment.parquet",
    "vehicle_kind.parquet",
    "vehicle_status.parquet",
    "vehicle_type.parquet",
]

def read_parquet_file(filename):
    path = DATA_DIR / filename
    return pd.read_parquet(path)

def extract_all():
    data = {}

    for filename in FILES:
        table_name = filename.replace(".parquet", "")
        data[table_name] = read_parquet_file(filename)

    return data


# if __name__ == "__main__":
#     all_data = extract_all()
#
#     for table_name, df in all_data.items():
#         print(f"\n--- {table_name} ---")
#         print("Rows:", len(df))
#         print("Columns:", list(df.columns))
#         print(df.dtypes)