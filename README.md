# car-tracking-project-db

Database project for CIIC 4060 / ICOM 5016.

## Technologies

- Python
- FastAPI
- PostgreSQL 17
- PostGIS
- Docker
- pandas
- pyarrow
- psycopg / psycopg2
- Render

## Project Structure

- `data/` - Parquet source files
- `ETL/` - Python ETL code
- `database/` - Database schema and sequence synchronization scripts
- `backend/` - FastAPI REST API
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

After running the ETL, run:

```text
database/sync_sequences.sql
```

to synchronize the PostgreSQL identity sequences with the imported IDs.

## Running the API

From the `backend/` directory, run:

```bash
uvicorn main:app --reload
```

The API uses the base path:

```text
/api/v1
```

## API Deployment

The Phase II FastAPI application is hosted on Render.

API URL:

```text
https://car-tracking-project-db.onrender.com
```

Swagger documentation:

```text
https://car-tracking-project-db.onrender.com/docs
```

## Database Connection

The production database is hosted on Render.

Host: dpg-dbnh1obrjlhs738psum0-a.virginia-postgres.render.com  
Port: 5432  
Database: proj_db_tzwy_saw8 
Username: proj_db_tzwy_user  
Password: <password>  
SSL Mode: require