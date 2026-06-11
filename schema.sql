-- Prologis Financial Assistant — Database Schema
-- Run this in PostgreSQL to recreate the database

CREATE DATABASE realestate_db;
\c realestate_db;

-- Properties table
CREATE TABLE IF NOT EXISTS properties (
    property_id   SERIAL PRIMARY KEY,
    address       VARCHAR(255),
    metro_area    VARCHAR(100),
    sq_footage    NUMERIC,
    property_type VARCHAR(50),
    property_name VARCHAR(255),
    occupancy_rate NUMERIC,
    annual_revenue NUMERIC,
    latitude      NUMERIC,
    longitude     NUMERIC
);

-- Financials table
CREATE TABLE IF NOT EXISTS financials (
    id          SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES properties(property_id),
    revenue     NUMERIC,
    net_income  NUMERIC,
    expenses    NUMERIC
);
