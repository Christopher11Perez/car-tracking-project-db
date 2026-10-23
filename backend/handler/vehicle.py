from fastapi import HTTPException
from dao.vehicle import VehicleDAO

class VehicleHandler:
    def _build_vehicle(self, row):
        created = row["created_at"]
        return {
            "vehicle_id": row["vehicle_id"],
            "vehicle_type_id": row["vehicle_type_id"],
            "vehicle_status_id": row["vehicle_status_id"],
            "plate_number": row["plate_number"],
            "make": row["make"],
            "model": row["model"],
            "year": row["year"],
            "created_at": created.strftime("%Y-%m-%dT%H:%M:%SZ") if created else None,
        }

    def get_vehicle_by_id(self, vehicle_id: int):
        row = VehicleDAO().get_vehicle_by_id(vehicle_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        return self._build_vehicle(row)