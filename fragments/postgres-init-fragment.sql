-- Creates database for use by the app
CREATE DATABASE dps;
-- Creates user that the app will use under normal day to day running.
-- It has no permissions by default; they will have to be specifically
-- granted in the alembic files when tables are created.
CREATE ROLE dps WITH LOGIN PASSWORD 'dps';
