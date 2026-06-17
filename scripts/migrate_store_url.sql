-- Añade URL pública de tienda a store_settings
USE binfrix;

ALTER TABLE store_settings
  ADD COLUMN IF NOT EXISTS store_url VARCHAR(500) NOT NULL DEFAULT '' AFTER contact_email;
