from psycopg2.pool import SimpleConnectionPool
from config.dbconfig import PG_DB_CONFIG, POOL_CONFIG

pool = SimpleConnectionPool(POOL_CONFIG["minconn"], POOL_CONFIG["maxconn"], **PG_DB_CONFIG)