# car-tracking-project-db
Database project for CIIC 4060 / ICOM 5016.

## Technologies

- Python
- PostgreSQL
- PostGIS
- Docker
- pandas
- pyarrow
- psycopg

## Project Structure

- `data/` - Parquet source files
- `ETL/` - Python ETL code
- `requirements.txt` - Python dependencies

## Requirements

- Python 3
- PostgreSQL 17
- PostGIS
- Docker

Install Python dependencies with:

```bash
pip install -r requirements.txt
```

## Database Setup

1. Create a PostgreSQL 17 database.
2. Enable PostGIS:

```sql
CREATE EXTENSION postgis;
```

3. Run `database/schema.sql` to create the project tables.

## Running the ETL

After installing the dependencies, run:

```bash
python ETL/main.py
```

The ETL reads the Parquet files from `data/` and loads them into the PostgreSQL database.

## Database Connection

The final Phase I database is hosted on Render.

Host: dpg-db42s3qj9qps73fv6dn0-a.virginia-postgres.render.com  
Port: 5432  
Database: proj_db_tzwy  
Username: proj_db_tzwy_user  
Password: <password>  
SSL Mode: require
