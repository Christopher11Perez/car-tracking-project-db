-- Correr despues de ETL para sincronizar autoincrement de ids.

SELECT setval(pg_get_serial_sequence('driver', 'driver_id'), COALESCE(MAX(driver_id), 0) + 1, false)
FROM driver;


SELECT setval(pg_get_serial_sequence('parking_area', 'parking_area_id'), COALESCE(MAX(parking_area_id), 0) + 1, false)
FROM parking_area;


SELECT setval(pg_get_serial_sequence('road_segment', 'road_id'), COALESCE(MAX(road_id), 0) + 1, false)
FROM road_segment;


SELECT setval(pg_get_serial_sequence('vehicle', 'vehicle_id'), COALESCE(MAX(vehicle_id), 0) + 1, false)
FROM vehicle;


SELECT setval(pg_get_serial_sequence('vehicle_assignment', 'assignment_id'), COALESCE(MAX(assignment_id), 0) + 1, false)
FROM vehicle_assignment;


SELECT setval(pg_get_serial_sequence('location_ping', 'ping_id'), COALESCE(MAX(ping_id), 0) + 1, false)
FROM location_ping;


SELECT setval(pg_get_serial_sequence('trip', 'trip_id'), COALESCE(MAX(trip_id), 0) + 1, false)
FROM trip;