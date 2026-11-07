import psycopg

# # Docker
# def get_connection():
#     return psycopg.connect(
#         host="localhost",
#         port=5432,
#         dbname="cartracking",
#         user="postgres",
#         password="postgres"
#     )

# Render
def get_connection():
    return psycopg.connect(
        host="dpg-dbnh1obrjlhs738psum0-a.virginia-postgres.render.com",
        port=5432,
        dbname="proj_db_tzwy_saw8",
        user="proj_db_tzwy_user",
        password="CmLLUC25YKUjMCh8fdmjIwG1PMRwe5vF",
        sslmode="require"
    )