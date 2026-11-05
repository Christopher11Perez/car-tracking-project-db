from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.encoders import jsonable_encoder


from dao.vehicle import (
    VehicleCreate,
    VehicleUpdate
)
from handler.vehicle import VehicleHandler

from dao.road_segment import (
    RoadSegmentCreate,
    RoadSegmentUpdate
)
from handler.road_segment import RoadSegmentHandler

from dao.parking_area import (
    ParkingAreaCreate,
    ParkingAreaUpdate
)
from handler.parking_area import ParkingAreaHandler

from dao.location_ping import (
    LocationPingCreate,
    LocationPingUpdate
)
from handler.location_ping import LocationPingHandler

from dao.trip import (
    TripCreate,
    TripUpdate
)
from handler.trip import TripHandler

from dao.driver import (
    DriverCreate,
    DriverUpdate
)
from handler.driver import DriverHandler

from dao.vehicle_assignment import (
    VehicleAssignmentCreate,
    VehicleAssignmentUpdate
)
from handler.vehicle_assignment import VehicleAssignmentHandler


app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# VEHICLE
# --------------------------------------------------

@app.get("/api/v1/vehicles")
async def get_vehicles(
        limit: str = "20",
        offset: str = "0",
        status: str | None = None,
        plate_number: str | None = None
):
    return VehicleHandler().get_all_vehicles(
        limit,
        offset,
        status,
        plate_number
    )


@app.post(
    "/api/v1/vehicles",
    status_code=201
)
async def create_vehicle(
        new_vehicle: VehicleCreate
):
    return VehicleHandler().create_vehicle(
        new_vehicle
    )


@app.get("/api/v1/vehicles/{vehicle_id}")
async def get_vehicle(
        vehicle_id: int
):
    return VehicleHandler().get_vehicle_by_id(
        vehicle_id
    )


@app.put("/api/v1/vehicles/{vehicle_id}")
async def update_vehicle(
        vehicle_id: int,
        vehicle_data: VehicleUpdate
):
    return VehicleHandler().update_vehicle(
        vehicle_id,
        vehicle_data
    )


@app.delete("/api/v1/vehicles/{vehicle_id}")
async def delete_vehicle(
        vehicle_id: int
):
    return VehicleHandler().delete_vehicle(
        vehicle_id
    )


@app.get(
    "/api/v1/vehicles/{vehicle_id}/current-location"
)
async def get_vehicle_current_location(
        vehicle_id: str
):
    return VehicleHandler().get_current_location(
        vehicle_id
    )


# --------------------------------------------------
# ROAD SEGMENT
# --------------------------------------------------

@app.get("/api/v1/road-segments")
async def get_road_segments(
        limit: str = "20",
        offset: str = "0",
        name: str | None = None,
        min_speed_kph: str | None = None,
        max_speed_kph: str | None = None,
        bbox: str | None = None
):
    return RoadSegmentHandler().get_all_road_segments(
        limit,
        offset,
        name,
        min_speed_kph,
        max_speed_kph,
        bbox
    )


@app.post(
    "/api/v1/road-segments",
    status_code=201
)
async def create_road_segment(
        road_data: RoadSegmentCreate
):
    return RoadSegmentHandler().create_road_segment(
        road_data
    )


@app.get("/api/v1/road-segments/geojson")
async def get_road_segments_geojson(
        limit: str = "15000",
        offset: str = "0",
        name: str | None = None,
        min_speed_kph: str | None = None,
        max_speed_kph: str | None = None
):
    result = (
        RoadSegmentHandler()
        .get_road_segments_geojson(
            limit,
            offset,
            name,
            min_speed_kph,
            max_speed_kph
        )
    )

    return JSONResponse(
        content=result,
        media_type="application/geo+json"
    )


@app.get("/api/v1/road-segments/{road_id}")
async def get_road_segment(
        road_id: int
):
    return RoadSegmentHandler().get_road_segment_by_id(
        road_id
    )


@app.put("/api/v1/road-segments/{road_id}")
async def update_road_segment(
        road_id: int,
        road_data: RoadSegmentUpdate
):
    return RoadSegmentHandler().update_road_segment(
        road_id,
        road_data
    )


@app.delete("/api/v1/road-segments/{road_id}")
async def delete_road_segment(
        road_id: int
):
    return RoadSegmentHandler().delete_road_segment(
        road_id
    )


# --------------------------------------------------
# PARKING AREA
# --------------------------------------------------

@app.get("/api/v1/parking-areas")
async def get_parking_areas(
        limit: str = "20",
        offset: str = "0",
        name: str | None = None,
        bbox: str | None = None
):
    return ParkingAreaHandler().get_all_parking_areas(
        limit,
        offset,
        name,
        bbox
    )


@app.post(
    "/api/v1/parking-areas",
    status_code=201
)
async def create_parking_area(
        parking_data: ParkingAreaCreate
):
    return ParkingAreaHandler().create_parking_area(
        parking_data
    )


@app.get("/api/v1/parking-areas/{parking_area_id}")
async def get_parking_area(
        parking_area_id: int
):
    return ParkingAreaHandler().get_parking_area_by_id(
        parking_area_id
    )


@app.put("/api/v1/parking-areas/{parking_area_id}")
async def update_parking_area(
        parking_area_id: int,
        parking_data: ParkingAreaUpdate
):
    return ParkingAreaHandler().update_parking_area(
        parking_area_id,
        parking_data
    )


@app.delete("/api/v1/parking-areas/{parking_area_id}")
async def delete_parking_area(
        parking_area_id: int
):
    return ParkingAreaHandler().delete_parking_area(
        parking_area_id
    )


# --------------------------------------------------
# LOCATION PING
# --------------------------------------------------

@app.get("/api/v1/location-pings")
async def get_location_pings(
        limit: str = "100",
        offset: str = "0",
        vehicle_id: str | None = None,
        from_ts: str | None = None,
        to_ts: str | None = None,
        bbox: str | None = None
):
    return LocationPingHandler().get_all_location_pings(
        limit,
        offset,
        vehicle_id,
        from_ts,
        to_ts,
        bbox
    )


@app.post(
    "/api/v1/location-pings",
    status_code=201
)
async def create_location_ping(
        ping_data: LocationPingCreate
):
    return LocationPingHandler().create_location_ping(
        ping_data
    )


@app.get("/api/v1/location-pings/{ping_id}")
async def get_location_ping(
        ping_id: int
):
    return LocationPingHandler().get_location_ping_by_id(
        ping_id
    )


@app.put("/api/v1/location-pings/{ping_id}")
async def update_location_ping(
        ping_id: int,
        ping_data: LocationPingUpdate
):
    return LocationPingHandler().update_location_ping(
        ping_id,
        ping_data
    )


@app.delete("/api/v1/location-pings/{ping_id}")
async def delete_location_ping(
        ping_id: int
):
    return LocationPingHandler().delete_location_ping(
        ping_id
    )


@app.get("/api/v1/vehicles/{vehicle_id}/pings")
async def get_vehicle_pings(
        vehicle_id: int,
        limit: str = "100",
        offset: str = "0",
        from_ts: str | None = None,
        to_ts: str | None = None
):
    return LocationPingHandler().get_vehicle_pings(
        vehicle_id,
        limit,
        offset,
        from_ts,
        to_ts
    )


# --------------------------------------------------
# TRIP
# --------------------------------------------------

@app.get("/api/v1/trips")
async def get_trips(
        limit: str = "50",
        offset: str = "0",
        vehicle_id: str | None = None,
        from_ts: str | None = None,
        to_ts: str | None = None
):
    return TripHandler().get_all_trips(
        limit,
        offset,
        vehicle_id,
        from_ts,
        to_ts
    )


@app.post(
    "/api/v1/trips",
    status_code=201
)
async def create_trip(
        trip_data: TripCreate
):
    return TripHandler().create_trip(
        trip_data
    )


@app.get("/api/v1/trips/{trip_id}")
async def get_trip(
        trip_id: int
):
    return TripHandler().get_trip_by_id(
        trip_id
    )


@app.put("/api/v1/trips/{trip_id}")
async def update_trip(
        trip_id: int,
        trip_data: TripUpdate
):
    return TripHandler().update_trip(
        trip_id,
        trip_data
    )


@app.delete("/api/v1/trips/{trip_id}")
async def delete_trip(
        trip_id: int
):
    return TripHandler().delete_trip(
        trip_id
    )


@app.get("/api/v1/vehicles/{vehicle_id}/trips")
async def get_vehicle_trips(
        vehicle_id: int,
        limit: str = "50",
        offset: str = "0",
        from_ts: str | None = None,
        to_ts: str | None = None
):
    return TripHandler().get_vehicle_trips(
        vehicle_id,
        limit,
        offset,
        from_ts,
        to_ts
    )


# --------------------------------------------------
# DRIVER
# --------------------------------------------------

@app.get("/api/v1/drivers")
async def get_drivers(
        limit: str = "20",
        offset: str = "0",
        name: str | None = None,
        license_number: str | None = None
):
    return DriverHandler().get_all_drivers(
        limit,
        offset,
        name,
        license_number
    )


@app.post(
    "/api/v1/drivers",
    status_code=201
)
async def create_driver(
        driver_data: DriverCreate
):
    return DriverHandler().create_driver(
        driver_data
    )


@app.get("/api/v1/drivers/{driver_id}")
async def get_driver(
        driver_id: int
):
    return DriverHandler().get_driver_by_id(
        driver_id
    )


@app.put("/api/v1/drivers/{driver_id}")
async def update_driver(
        driver_id: int,
        driver_data: DriverUpdate
):
    return DriverHandler().update_driver(
        driver_id,
        driver_data
    )


@app.delete("/api/v1/drivers/{driver_id}")
async def delete_driver(
        driver_id: int
):
    return DriverHandler().delete_driver(
        driver_id
    )


# --------------------------------------------------
# VEHICLE ASSIGNMENT
# --------------------------------------------------

@app.get("/api/v1/vehicle-assignments")
async def get_vehicle_assignments(
        limit: str = "20",
        offset: str = "0",
        vehicle_id: str | None = None,
        driver_id: str | None = None,
        active: str | None = None
):
    return VehicleAssignmentHandler().get_all_assignments(
        limit,
        offset,
        vehicle_id,
        driver_id,
        active
    )


@app.post(
    "/api/v1/vehicle-assignments",
    status_code=201
)
async def create_vehicle_assignment(
        assignment_data: VehicleAssignmentCreate
):
    return VehicleAssignmentHandler().create_assignment(
        assignment_data
    )


@app.get(
    "/api/v1/vehicle-assignments/{assignment_id}"
)
async def get_vehicle_assignment(
        assignment_id: int
):
    return VehicleAssignmentHandler().get_assignment_by_id(
        assignment_id
    )


@app.put(
    "/api/v1/vehicle-assignments/{assignment_id}"
)
async def update_vehicle_assignment(
        assignment_id: int,
        assignment_data: VehicleAssignmentUpdate
):
    return VehicleAssignmentHandler().update_assignment(
        assignment_id,
        assignment_data
    )


@app.delete(
    "/api/v1/vehicle-assignments/{assignment_id}"
)
async def delete_vehicle_assignment(
        assignment_id: int
):
    return VehicleAssignmentHandler().delete_assignment(
        assignment_id
    )

# --------------------------------------------------
# REQUEST VALIDATION STATUS CODE HANDLING
# --------------------------------------------------

# Endpoints where the SC specification requires
# request-body validation errors to return 400.
VALIDATION_400_ROUTES = {
    ("POST", "/api/v1/vehicles"),
    ("PUT", "/api/v1/vehicles/{vehicle_id}"),

    ("POST", "/api/v1/road-segments"),
    ("PUT", "/api/v1/road-segments/{road_id}"),

    ("POST", "/api/v1/parking-areas"),
    ("PUT", "/api/v1/parking-areas/{parking_area_id}"),

    ("POST", "/api/v1/location-pings"),
    ("PUT", "/api/v1/location-pings/{ping_id}"),

    ("POST", "/api/v1/trips"),

    ("POST", "/api/v1/vehicle-assignments"),
    ("PUT", "/api/v1/vehicle-assignments/{assignment_id}"),
}


# Endpoints where the SC specification distinguishes
# malformed JSON/payload errors (400) from validation
# failures (422).
MIXED_VALIDATION_ROUTES = {
    ("PUT", "/api/v1/trips/{trip_id}"),
    ("POST", "/api/v1/drivers"),
    ("PUT", "/api/v1/drivers/{driver_id}"),
}


def _get_route_path(request: Request):
    route = request.scope.get("route")

    if route is None:
        return request.url.path

    return route.path


def _is_payload_shape_error(errors):
    """
    Errors that represent malformed JSON or an invalid
    request-body shape rather than a semantic field error.
    """

    shape_error_types = {
        "json_invalid",
        "extra_forbidden",
        "model_attributes_type",
        "dict_type",
        "list_type",
    }

    for error in errors:
        if error.get("type") in shape_error_types:
            return True

    return False


def _is_missing_entire_body(errors):
    """
    Detect a request where the complete body itself
    was omitted.
    """

    for error in errors:

        if (
            error.get("type") == "missing"
            and error.get("loc") == ("body",)
        ):
            return True

    return False


@app.exception_handler(RequestValidationError)
async def custom_request_validation_handler(
        request: Request,
        exc: RequestValidationError
):
    route_path = _get_route_path(request)

    route_key = (
        request.method,
        route_path
    )

    errors = exc.errors()

    # --------------------------------------------------
    # SC endpoints that require 400 for body validation
    # --------------------------------------------------

    if route_key in VALIDATION_400_ROUTES:

        return JSONResponse(
            status_code=400,
            content={
                "detail": jsonable_encoder(
                    errors
                )
            }
        )

    # --------------------------------------------------
    # Endpoints where SC explicitly supports both
    # 400 and 422.
    # --------------------------------------------------

    if route_key in MIXED_VALIDATION_ROUTES:

        # Malformed JSON or invalid object structure
        # must be 400.
        if _is_payload_shape_error(errors):

            return JSONResponse(
                status_code=400,
                content={
                    "detail": jsonable_encoder(
                        errors
                    )
                }
            )

        # PUT endpoints require at least a request body.
        # A completely missing body is equivalent to
        # an empty/malformed patch -> 400.
        if (
            request.method == "PUT"
            and _is_missing_entire_body(errors)
        ):

            return JSONResponse(
                status_code=400,
                content={
                    "detail": jsonable_encoder(
                        errors
                    )
                }
            )

        # Everything else in these specifically mixed
        # endpoints remains 422 as required by SC.
        return JSONResponse(
            status_code=422,
            content={
                "detail": jsonable_encoder(
                    errors
                )
            }
        )

    # --------------------------------------------------
    # Any endpoint not explicitly listed above keeps
    # FastAPI's normal validation behavior.
    # --------------------------------------------------

    return await request_validation_exception_handler(
        request,
        exc
    )