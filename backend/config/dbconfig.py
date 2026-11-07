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

# Render
PG_DB_CONFIG = {
    "dbname": "proj_db_tzwy_saw8",
    "user": "proj_db_tzwy_user",
    "password": "CmLLUC25YKUjMCh8fdmjIwG1PMRwe5vF",
    "host": "dpg-dbnh1obrjlhs738psum0-a.virginia-postgres.render.com",
    "port": 5432,
    "sslmode": "require",
}