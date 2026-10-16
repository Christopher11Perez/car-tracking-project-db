CREATE TABLE vehicle_kind (
    vehicle_kind_id BIGINT PRIMARY KEY,
    name TEXT
);

CREATE TABLE fuel_type (
    fuel_type_id BIGINT PRIMARY KEY,
    name TEXT
);

CREATE TABLE vehicle_status (
    vehicle_status_id BIGINT PRIMARY KEY,
    name TEXT
);

CREATE TABLE driver (
    driver_id BIGINT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    license_number TEXT,
    hired_at TIMESTAMP
);

CREATE TABLE parking_area (
    parking_area_id BIGINT PRIMARY KEY,
    name TEXT,
    capacity BIGINT,
    geom geometry(POLYGON, 4326),
    created_at TIMESTAMP
);

CREATE TABLE road_segment (
    road_id BIGINT PRIMARY KEY,
    name TEXT,
    speed_limit_kph BIGINT,
    geom geometry(LINESTRING, 4326),
    created_at TIMESTAMP,
    is_oneway BOOLEAN,
    direction TEXT
);

CREATE TABLE vehicle_type (
    vehicle_type_id BIGINT PRIMARY KEY,
    vehicle_kind_id BIGINT,
    fuel_type_id BIGINT,
    emissions_rating DOUBLE PRECISION,
    created_at TIMESTAMP,

    FOREIGN KEY (vehicle_kind_id)
        REFERENCES vehicle_kind(vehicle_kind_id),

    FOREIGN KEY (fuel_type_id)
        REFERENCES fuel_type(fuel_type_id)
);

CREATE TABLE vehicle (
    vehicle_id BIGINT PRIMARY KEY,
    vehicle_type_id BIGINT,
    vehicle_status_id BIGINT,
    plate_number TEXT,
    make TEXT,
    model TEXT,
    year BIGINT,
    created_at TIMESTAMP,

    FOREIGN KEY (vehicle_type_id)
        REFERENCES vehicle_type(vehicle_type_id),

    FOREIGN KEY (vehicle_status_id)
        REFERENCES vehicle_status(vehicle_status_id)
);

CREATE TABLE vehicle_assignment (
    assignment_id BIGINT PRIMARY KEY,
    vehicle_id BIGINT,
    driver_id BIGINT,
    assigned_from TIMESTAMP,
    assigned_to TIMESTAMP,

    FOREIGN KEY (vehicle_id)
        REFERENCES vehicle(vehicle_id),

    FOREIGN KEY (driver_id)
        REFERENCES driver(driver_id)
);

CREATE TABLE location_ping (
    ping_id BIGINT PRIMARY KEY,
    vehicle_id BIGINT,
    ts TIMESTAMP,
    geom geometry(POINT, 4326),
    speed_kph DOUBLE PRECISION,
    heading_deg DOUBLE PRECISION,

    FOREIGN KEY (vehicle_id)
        REFERENCES vehicle(vehicle_id)
);

CREATE TABLE trip (
    trip_id BIGINT PRIMARY KEY,
    vehicle_id BIGINT,
    start_ts TIMESTAMP,
    end_ts TIMESTAMP,
    start_geom geometry(POINT, 4326),
    end_geom geometry(POINT, 4326),
    distance_km DOUBLE PRECISION,

    FOREIGN KEY (vehicle_id)
        REFERENCES vehicle(vehicle_id)
);