from dao.parts import PartDAO, Part
from fastapi import HTTPException

class PartHandler:
    def get_all_parts(self):
        dao = PartDAO()
        return dao.get_all_parts()

    def get_part_by_id(self, id):
        dao = PartDAO()
        result = dao.get_part_by_id(id)
        if result is None:
            raise HTTPException(status_code=404, detail="Part not found")
        return Part(**result)

    def create_part(self, new_part : Part):
        dao = PartDAO()
        pid = dao.create_part(new_part)
        new_part.pid = pid
        return new_part

    def get_parts_by_color(self, color: str):
        dao = PartDAO()
        return dao.get_parts_by_color(color)

    def update_part(self, pid, part):
        dao = PartDAO()
        temp = dao.get_part_by_id(pid)
        if temp is None:
            raise HTTPException(status_code=404, detail="Part not found")
        else:
            result = dao.update_part(pid, part)
            return result

    def delete_part(self, part):
        dao = PartDAO()
        result = dao.delete_part(part)
        if not result:
            raise HTTPException(status_code=404, detail="Part not found")
        else:
            return {"message": "Part deleted "}