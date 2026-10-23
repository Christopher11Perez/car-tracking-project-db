
from config.dbconfig import PG_DB_CONFIG, POOL_CONFIG
import psycopg2
from pydantic import BaseModel
from typing import Optional
from psycopg2.extras import DictCursor
from psycopg2.pool import SimpleConnectionPool

class Part(BaseModel):
    pid : Optional[int] | None = None
    pname : str
    pcolor : str
    pprice : float
    pmaterial: str
    pweight : float

class PartDAO:
    def __init__(self):
        #Connection pools serve to create several connections to the DB
        #This makes the app faster because creating connections is
        #expensive. With the pool, you recycle existing connections
        self.pool  = SimpleConnectionPool(POOL_CONFIG["minconn"],
                                          POOL_CONFIG["maxconn"],
                                          **PG_DB_CONFIG)

    def get_all_parts(self) -> list[Part]:
        # Get connection from pool
        conn = self.pool.getconn()
        # now get the cursor
        cursor = conn.cursor(cursor_factory=DictCursor)
        query  = """
        select pid, pname, pcolor, pprice, pmaterial, pweight
        from parts
        """
        cursor.execute(query)
        result : list[Part] = []
        for row in cursor:
            result.append(Part(**row))
        # Always close cursor
        cursor.close()
        # Return the connection to the pool
        self.pool.putconn(conn)
        return result

    def get_part_by_id(self, pid: int) -> Optional[Part]:
        # Get connection from pool
        conn = self.pool.getconn()
        # now get the cursor
        cursor = conn.cursor(cursor_factory=DictCursor)
        query = """
        select pid, pname, pcolor, pprice, pmaterial, pweight
        from parts
        where pid = %s"""
        cursor.execute(query, (pid,))
        result : Optional[Part] = None
        result = cursor.fetchone()
        # Always close cursor
        cursor.close()
        # Return the connection to the pool
        self.pool.putconn(conn)
        return result

    def create_part(self, new_part: Part) -> int:
        # Get connection from pool
        conn = self.pool.getconn()
        # now get the cursor
        cursor = conn.cursor(cursor_factory=DictCursor)
        query = """
        insert into 
        parts (pname, pcolor, pprice, pmaterial, pweight)
        values (%(pname)s, %(pcolor)s, %(pprice)s, %(pmaterial)s, %(pweight)s)
        returning pid;
        """
        cursor.execute(query, new_part.model_dump(exclude_none=True))
        pid = cursor.fetchone()[0]
        # Commit change to DB
        conn.commit()
        # Always close cursor
        cursor.close()
        # Return the connection to the pool
        self.pool.putconn(conn)
        return pid

    def get_parts_by_color(self, color) -> list[Part]:
        # Get connection from pool
        conn = self.pool.getconn()
        # now get the cursor
        cursor = conn.cursor(cursor_factory=DictCursor)
        query = """
            select pid, pname, pcolor, pprice, pmaterial, pweight
            from parts
            where pcolor = %s"""
        cursor.execute(query, (color,))
        result : list[Part] = []
        for row in cursor:
            result.append(Part(**row))
        # Always close cursor
        cursor.close()
        # Return the connection to the pool
        self.pool.putconn(conn)
        return result

    def update_part(self, pid, part):
        # Get connection from pool
        conn = self.pool.getconn()
        # now get the cursor
        cursor = conn.cursor(cursor_factory=DictCursor)
        query = """
        update parts
        set pname = %(pname)s, pcolor = %(pcolor)s, pprice = %(pprice)s, pweight = %(pweight)s, pmaterial = %(pmaterial)s
        where pid = %(pid)s
        """
        cursor.execute(query, part.model_dump())
        conn.commit()
        # Always close cursor
        cursor.close()
        # Return the connection to the pool
        self.pool.putconn(conn)
        return part

    def delete_part(self, part):
        # Get connection from pool
        conn = self.pool.getconn()
        # now get the cursor
        cursor = conn.cursor(cursor_factory=DictCursor)
        query = """
                delete from parts
                where pid = %s
                """
        cursor.execute(query, (part,))
        rows = cursor.rowcount
        conn.commit()
        # Always close cursor
        cursor.close()
        # Return the connection to the pool
        self.pool.putconn(conn)
        return rows == 1