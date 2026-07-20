-- Run this once as the postgres superuser to set up the app database.
-- Example: psql -U postgres -f scripts/create_db.sql
CREATE USER storymiles WITH PASSWORD 'storymiles';
CREATE DATABASE storymiles OWNER storymiles;
GRANT ALL PRIVILEGES ON DATABASE storymiles TO storymiles;
