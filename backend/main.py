from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from handler.vehicle import VehicleHandler

app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: int):
    return VehicleHandler().get_vehicle_by_id(vehicle_id)