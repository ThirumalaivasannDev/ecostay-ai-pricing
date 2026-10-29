CREATE DATABASE IF NOT EXISTS eco_pricing;
USE eco_pricing;

CREATE TABLE IF NOT EXISTS daily_bookings (
  stay_date    DATE PRIMARY KEY,
  rooms_booked INT NOT NULL CHECK (rooms_booked BETWEEN 0 AND 20),
  price        INT NOT NULL,                      -- price per room (Rs.)
  revenue      INT GENERATED ALWAYS AS (rooms_booked * price) STORED,
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS price_recommendations (
  stay_date         DATE PRIMARY KEY,
  recommended_price INT NOT NULL,
  occupancy_pct     DECIMAL(5,1) NOT NULL,
  expected_revenue  INT NOT NULL,
  generated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(50) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,           -- hashed, never plain text
  role          VARCHAR(20) NOT NULL DEFAULT 'owner'
);