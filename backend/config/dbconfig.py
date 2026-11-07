import os

POOL_CONFIG = {
    "minconn": 1,
    "maxconn": 5,
}

# Docker
# PG_DB_CONFIG = {
#     "dbname": os.getenv("DB_NAME", "cartracking"),
#     "user": os.getenv("DB_USER", "postgres"),
#     "password": os.getenv("DB_PASSWORD", "postgres"),
#     "host": os.getenv("DB_HOST", "localhost"),
#     "port": int(os.getenv("DB_PORT", "5432")),
#     "sslmode": os.getenv("DB_SSLMODE", "prefer"),
# }

#  credenciales obtenidas por enviroment variables de render.
PG_DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "sslmode": os.getenv("DB_SSLMODE", "require"),
}