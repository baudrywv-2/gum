-- Extra databases created on first Postgres boot.
SELECT 'CREATE DATABASE gum_test OWNER gum'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'gum_test')\gexec
