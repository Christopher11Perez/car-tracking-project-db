import psycopg

def get_connection():
    return psycopg.connect(
        host="localhost",
        port=5432,
        dbname="car_tracking",
        user="postgres",
        password="postgres"
    )