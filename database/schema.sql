-- Business Listings Dashboard - MySQL schema
-- Usage:  mysql -u root -p < database/schema.sql

CREATE DATABASE IF NOT EXISTS listings_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE listings_db;

CREATE TABLE IF NOT EXISTS listing_master (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  business_name VARCHAR(255) NOT NULL,
  category      VARCHAR(100) NOT NULL DEFAULT 'Uncategorized',
  city          VARCHAR(100) NOT NULL,
  address       TEXT NULL,
  phone         VARCHAR(50)  NULL,
  source        VARCHAR(50)  NOT NULL,
  dedupe_hash   CHAR(64)     NOT NULL COMMENT 'sha256(name|city|address|source) - prevents duplicate rows',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_listing_dedupe (dedupe_hash),
  KEY ix_listing_city (city),
  KEY ix_listing_category (category),
  KEY ix_listing_source (source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- App user (matches backend/.env.example). Change the password for anything beyond local use.
CREATE USER IF NOT EXISTS 'listings_user'@'%' IDENTIFIED BY 'listings_pass';
GRANT ALL PRIVILEGES ON listings_db.* TO 'listings_user'@'%';
FLUSH PRIVILEGES;
