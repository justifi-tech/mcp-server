-- PostgreSQL initialization script for MCP Server
-- Zero-trust security setup with least privilege access

-- Create dedicated database for MCP (only if it doesn't exist)
SELECT 'CREATE DATABASE mcp'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mcp')\gexec

-- Connect to the mcp database to set up schema and user
\c mcp;

-- Create dedicated schema for MCP application (only if it doesn't exist)
CREATE SCHEMA IF NOT EXISTS mcp_app;

-- Create restricted user for MCP server application (only if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mcp_server') THEN
        CREATE USER mcp_server WITH PASSWORD 'mcp_secure_password_change_in_production';
    END IF;
END $$;

-- Revoke all default privileges from mcp_server on public schema
REVOKE ALL ON SCHEMA public FROM mcp_server;
REVOKE ALL ON DATABASE mcp FROM mcp_server;

-- Grant minimal required privileges on mcp database
GRANT CONNECT ON DATABASE mcp TO mcp_server;

-- Grant usage and create privileges only on mcp_app schema
GRANT USAGE ON SCHEMA mcp_app TO mcp_server;
GRANT CREATE ON SCHEMA mcp_app TO mcp_server;

-- Grant privileges on all current and future tables in mcp_app schema
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mcp_app TO mcp_server;
ALTER DEFAULT PRIVILEGES IN SCHEMA mcp_app GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mcp_server;

-- Grant privileges on all current and future sequences in mcp_app schema
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA mcp_app TO mcp_server;
ALTER DEFAULT PRIVILEGES IN SCHEMA mcp_app GRANT USAGE, SELECT ON SEQUENCES TO mcp_server;

-- Ensure postgres superuser cannot access mcp_app schema (zero-trust)
-- Note: postgres still has superuser privileges but we're being explicit
REVOKE ALL ON SCHEMA mcp_app FROM postgres;

-- Create the message_store table in the mcp_app schema (only if it doesn't exist)
CREATE TABLE IF NOT EXISTS mcp_app.message_store (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    message JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for performance (only if they don't exist)
CREATE INDEX IF NOT EXISTS idx_message_store_session_id ON mcp_app.message_store(session_id);
CREATE INDEX IF NOT EXISTS idx_message_store_created_at ON mcp_app.message_store(created_at);

-- Grant specific table privileges to mcp_server
GRANT SELECT, INSERT, UPDATE, DELETE ON mcp_app.message_store TO mcp_server;
GRANT USAGE, SELECT ON SEQUENCE mcp_app.message_store_id_seq TO mcp_server;

-- Additional security: Create a read-only user for monitoring/analytics (optional)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mcp_readonly') THEN
        CREATE USER mcp_readonly WITH PASSWORD 'mcp_readonly_password_change_in_production';
    END IF;
END $$;
GRANT CONNECT ON DATABASE mcp TO mcp_readonly;
GRANT USAGE ON SCHEMA mcp_app TO mcp_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA mcp_app TO mcp_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA mcp_app GRANT SELECT ON TABLES TO mcp_readonly;

-- Revoke public schema access from readonly user too
REVOKE ALL ON SCHEMA public FROM mcp_readonly;

-- Log the setup completion
DO $$
BEGIN
    RAISE NOTICE 'MCP Database setup completed successfully';
    RAISE NOTICE 'Database: mcp';
    RAISE NOTICE 'Schema: mcp_app'; 
    RAISE NOTICE 'Application User: mcp_server (read/write access to mcp_app schema only)';
    RAISE NOTICE 'Readonly User: mcp_readonly (read-only access to mcp_app schema only)';
    RAISE NOTICE 'Security: Zero-trust setup with least privilege access';
END $$; 