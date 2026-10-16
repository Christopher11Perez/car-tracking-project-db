from extract import read_parquet_file
from load import load_driver, load_fuel_type, load_vehicle_status, load_location_ping, load_parking_area, load_vehicle_kind, load_vehicle_type, load_vehicle, load_trip, load_vehicle_assignment, load_road_segment


def main():
    driver_df = read_parquet_file("driver.parquet")
    fuel_type_df = read_parquet_file("fuel_type.parquet")
    location_ping_df = read_parquet_file("location_ping.parquet")
    parking_area_df = read_parquet_file("parking_area.parquet")
    road_segment_df = read_parquet_file("road_segment.parquet")
    trip_df = read_parquet_file("trip.parquet")
    vehicle_assignment_df = read_parquet_file("vehicle_assignment.parquet")
    vehicle_kind_df = read_parquet_file("vehicle_kind.parquet")
    vehicle_status_df = read_parquet_file("vehicle_status.parquet")
    vehicle_type_df = read_parquet_file("vehicle_type.parquet")
    vehicle_df = read_parquet_file("vehicle.parquet")

    # No foreign keys
    load_driver(driver_df)
    load_fuel_type(fuel_type_df)
    load_vehicle_kind(vehicle_kind_df)
    load_vehicle_status(vehicle_status_df)
    load_parking_area(parking_area_df)
    load_road_segment(road_segment_df)

    # With foreign keys
    load_vehicle_type(vehicle_type_df)
    load_vehicle(vehicle_df)
    load_location_ping(location_ping_df)
    load_trip(trip_df)
    load_vehicle_assignment(vehicle_assignment_df)


if __name__ == "__main__":
    main()