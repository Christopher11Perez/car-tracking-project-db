from datetime import datetime, timezone

from fastapi import HTTPException

from dao.driver import (
    DriverDAO,
    DriverCreate,
    DriverUpdate
)


class DriverHandler:

    def _normalize_hired_at(
            self,
            driver
    ):
        if driver.hired_at is not None:
            driver.hired_at = (
                driver.hired_at.replace(
                    tzinfo=timezone.utc
                )
            )

        return driver

    def _parse_timestamp(
            self,
            value
    ):
        try:
            clean_value = value.strip()

            if clean_value.endswith("Z"):
                clean_value = (
                    clean_value[:-1]
                    + "+00:00"
                )

            parsed = datetime.fromisoformat(
                clean_value
            )

            if parsed.tzinfo is not None:
                parsed = (
                    parsed.astimezone(
                        timezone.utc
                    )
                    .replace(
                        tzinfo=None
                    )
                )

            return parsed

        except (
            ValueError,
            AttributeError
        ):
            raise HTTPException(
                status_code=422,
                detail="Invalid hired_at timestamp"
            )

    def get_all_drivers(
            self,
            limit,
            offset,
            name=None,
            license_number=None
    ):
        try:
            limit = int(limit)
            offset = int(offset)

        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid query parameter values"
            )

        if limit < 0 or offset < 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid query parameter values"
            )

        dao = DriverDAO()

        drivers, count = (
            dao.get_all_drivers(
                limit,
                offset,
                name,
                license_number
            )
        )

        items = [
            self._normalize_hired_at(
                driver
            )
            for driver in drivers
        ]

        return {
            "items": items,
            "limit": limit,
            "offset": offset,
            "count": count
        }

    def get_driver_by_id(
            self,
            driver_id: int
    ):
        dao = DriverDAO()

        result = (
            dao.get_driver_by_id(
                driver_id
            )
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Driver not found"
            )

        return self._normalize_hired_at(
            result
        )

    def create_driver(
            self,
            new_driver: DriverCreate
    ):
        dao = DriverDAO()

        new_driver.first_name = (
            new_driver.first_name.strip()
        )

        new_driver.last_name = (
            new_driver.last_name.strip()
        )

        new_driver.license_number = (
            new_driver.license_number.strip()
        )

        if not new_driver.first_name:
            raise HTTPException(
                status_code=422,
                detail="first_name cannot be empty"
            )

        if not new_driver.last_name:
            raise HTTPException(
                status_code=422,
                detail="last_name cannot be empty"
            )

        if not new_driver.license_number:
            raise HTTPException(
                status_code=422,
                detail="license_number cannot be empty"
            )

        if dao.license_number_exists(
            new_driver.license_number
        ):
            raise HTTPException(
                status_code=409,
                detail="License number already exists"
            )

        hired_at = (
            self._parse_timestamp(
                new_driver.hired_at
            )
        )

        result = dao.create_driver(
            new_driver,
            hired_at
        )

        return self._normalize_hired_at(
            result
        )

    def update_driver(
            self,
            driver_id: int,
            driver_update: DriverUpdate
    ):
        dao = DriverDAO()

        current_driver = (
            dao.get_driver_by_id(
                driver_id
            )
        )

        if current_driver is None:
            raise HTTPException(
                status_code=404,
                detail="Driver not found"
            )

        driver_data = (
            driver_update.model_dump(
                exclude_unset=True
            )
        )

        if not driver_data:
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided"
            )

        text_fields = [
            "first_name",
            "last_name",
            "license_number"
        ]

        for field in text_fields:

            if field in driver_data:

                if driver_data[field] is None:
                    raise HTTPException(
                        status_code=422,
                        detail=f"{field} cannot be null"
                    )

                driver_data[field] = (
                    driver_data[field].strip()
                )

                if not driver_data[field]:
                    raise HTTPException(
                        status_code=422,
                        detail=f"{field} cannot be empty"
                    )

        if "license_number" in driver_data:

            if dao.license_number_exists(
                driver_data[
                    "license_number"
                ],
                driver_id
            ):
                raise HTTPException(
                    status_code=409,
                    detail="License number already exists"
                )

        if "hired_at" in driver_data:

            if driver_data["hired_at"] is None:
                raise HTTPException(
                    status_code=422,
                    detail="hired_at cannot be null"
                )

            driver_data["hired_at"] = (
                self._parse_timestamp(
                    driver_data[
                        "hired_at"
                    ]
                )
            )

        result = dao.update_driver(
            driver_id,
            driver_data
        )

        return self._normalize_hired_at(
            result
        )

    def delete_driver(
            self,
            driver_id: int
    ):
        dao = DriverDAO()

        driver = (
            dao.get_driver_by_id(
                driver_id
            )
        )

        if driver is None:
            raise HTTPException(
                status_code=404,
                detail="Driver not found"
            )

        if dao.driver_has_assignments(
            driver_id
        ):
            raise HTTPException(
                status_code=409,
                detail="Driver cannot be deleted because it is referenced by a vehicle assignment"
            )

        dao.delete_driver(
            driver_id
        )

        return {
            "message": "Driver deleted successfully.",
            "driver_id": driver_id
        }