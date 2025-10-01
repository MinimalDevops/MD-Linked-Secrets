-- MD-Linked-Secrets Database Schema
-- PostgreSQL schema for local secret management tool

-- Enable UUID extension for better ID management
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the projects table
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create the env_vars table
CREATE TABLE IF NOT EXISTS env_vars (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    raw_value TEXT, -- Nullable, for direct values
    linked_to VARCHAR(255), -- Nullable, format: "PROJECT:VAR"
    concat_parts TEXT, -- Nullable, format: "PROJECT:VAR|PROJECT:VAR"
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure only one of raw_value, linked_to, or concat_parts is set
    CONSTRAINT check_value_type CHECK (
        (raw_value IS NOT NULL AND linked_to IS NULL AND concat_parts IS NULL) OR
        (raw_value IS NULL AND linked_to IS NOT NULL AND concat_parts IS NULL) OR
        (raw_value IS NULL AND linked_to IS NULL AND concat_parts IS NOT NULL)
    ),
    
    -- Ensure unique variable names within a project
    UNIQUE(project_id, name)
);

-- Create the project_links table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS project_links (
    id SERIAL PRIMARY KEY,
    source_project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    target_project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    link_type VARCHAR(50) DEFAULT 'dependency', -- dependency, shared, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent self-linking
    CONSTRAINT check_no_self_link CHECK (source_project_id != target_project_id),
    
    -- Ensure unique links
    UNIQUE(source_project_id, target_project_id)
);

-- Create the env_exports table
CREATE TABLE IF NOT EXISTS env_exports (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    export_path TEXT NOT NULL,
    exported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    with_prefix BOOLEAN DEFAULT FALSE,
    with_suffix BOOLEAN DEFAULT FALSE,
    prefix_value VARCHAR(50),
    suffix_value VARCHAR(50),
    resolved_values JSONB NOT NULL, -- Store resolved key-value pairs at export time
    export_hash VARCHAR(64), -- Hash of resolved values for quick comparison
    
    -- Ensure unique exports per project and path
    UNIQUE(project_id, export_path)
);

-- Create the audit_log table
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(255), -- Could be user or system
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_env_vars_project_id ON env_vars(project_id);
CREATE INDEX IF NOT EXISTS idx_env_vars_linked_to ON env_vars(linked_to);
CREATE INDEX IF NOT EXISTS idx_env_vars_concat_parts ON env_vars(concat_parts);
CREATE INDEX IF NOT EXISTS idx_project_links_source ON project_links(source_project_id);
CREATE INDEX IF NOT EXISTS idx_project_links_target ON project_links(target_project_id);
CREATE INDEX IF NOT EXISTS idx_env_exports_project_id ON env_exports(project_id);
CREATE INDEX IF NOT EXISTS idx_env_exports_exported_at ON env_exports(exported_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at ON audit_log(changed_at);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_env_vars_updated_at 
    BEFORE UPDATE ON env_vars 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a function to validate linked_to format
CREATE OR REPLACE FUNCTION validate_linked_to_format()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.linked_to IS NOT NULL THEN
        -- Check if format is PROJECT:VAR
        IF NEW.linked_to !~ '^[A-Za-z0-9_-]+:[A-Za-z0-9_-]+$' THEN
            RAISE EXCEPTION 'linked_to must be in format PROJECT:VAR';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for linked_to validation
CREATE TRIGGER validate_env_vars_linked_to 
    BEFORE INSERT OR UPDATE ON env_vars 
    FOR EACH ROW EXECUTE FUNCTION validate_linked_to_format();

-- Create a function to validate concat_parts format
CREATE OR REPLACE FUNCTION validate_concat_parts_format()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.concat_parts IS NOT NULL THEN
        -- Check if format contains PROJECT:VAR parts separated by |
        IF NEW.concat_parts !~ '^([A-Za-z0-9_-]+:[A-Za-z0-9_-]+)(\|[A-Za-z0-9_-]+:[A-Za-z0-9_-]+)*$' THEN
            RAISE EXCEPTION 'concat_parts must be in format PROJECT:VAR|PROJECT:VAR';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for concat_parts validation
CREATE TRIGGER validate_env_vars_concat_parts 
    BEFORE INSERT OR UPDATE ON env_vars 
    FOR EACH ROW EXECUTE FUNCTION validate_concat_parts_format();

-- Create a function to detect circular references
CREATE OR REPLACE FUNCTION detect_circular_reference()
RETURNS TRIGGER AS $$
DECLARE
    current_var_id INTEGER;
    visited_vars INTEGER[] := ARRAY[]::INTEGER[];
    var_stack INTEGER[] := ARRAY[]::INTEGER[];
    linked_project VARCHAR(255);
    linked_var VARCHAR(255);
    target_var_id INTEGER;
BEGIN
    -- Only check for linked variables
    IF NEW.linked_to IS NULL THEN
        RETURN NEW;
    END IF;
    
    -- Extract project and variable from linked_to
    linked_project := split_part(NEW.linked_to, ':', 1);
    linked_var := split_part(NEW.linked_to, ':', 2);
    
    -- Find the target variable
    SELECT ev.id INTO target_var_id 
    FROM env_vars ev 
    JOIN projects p ON ev.project_id = p.id 
    WHERE p.name = linked_project AND ev.name = linked_var;
    
    IF target_var_id IS NULL THEN
        RAISE EXCEPTION 'Referenced variable % does not exist', NEW.linked_to;
    END IF;
    
    -- Check for circular reference using depth-first search
    current_var_id := target_var_id;
    var_stack := ARRAY[current_var_id];
    
    WHILE array_length(var_stack, 1) > 0 LOOP
        current_var_id := var_stack[array_length(var_stack, 1)];
        var_stack := var_stack[1:array_length(var_stack, 1)-1];
        
        -- If we've seen this variable before, it's a cycle
        IF current_var_id = ANY(visited_vars) THEN
            RAISE EXCEPTION 'Circular reference detected in variable linking';
        END IF;
        
        visited_vars := array_append(visited_vars, current_var_id);
        
        -- Add linked variables to stack
        SELECT array_append(var_stack, ev.id) INTO var_stack
        FROM env_vars ev
        WHERE ev.linked_to IS NOT NULL 
        AND ev.id = current_var_id;
    END LOOP;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for circular reference detection
CREATE TRIGGER detect_circular_reference_trigger 
    BEFORE INSERT OR UPDATE ON env_vars 
    FOR EACH ROW EXECUTE FUNCTION detect_circular_reference();

-- Create a view for resolved environment variables
CREATE OR REPLACE VIEW resolved_env_vars AS
SELECT 
    ev.id,
    ev.project_id,
    p.name as project_name,
    ev.name,
    ev.raw_value,
    ev.linked_to,
    ev.concat_parts,
    ev.description,
    ev.is_encrypted,
    ev.created_at,
    ev.updated_at,
    CASE 
        WHEN ev.raw_value IS NOT NULL THEN ev.raw_value
        WHEN ev.linked_to IS NOT NULL THEN 'LINKED: ' || ev.linked_to
        WHEN ev.concat_parts IS NOT NULL THEN 'CONCAT: ' || ev.concat_parts
    END as value_type
FROM env_vars ev
JOIN projects p ON ev.project_id = p.id;

-- Insert sample data for testing
INSERT INTO projects (name, description) VALUES 
('shared', 'Shared configuration and secrets'),
('webapp', 'Web application project'),
('api', 'API service project')
ON CONFLICT (name) DO NOTHING;

INSERT INTO env_vars (project_id, name, raw_value, description) VALUES 
((SELECT id FROM projects WHERE name = 'shared'), 'DATABASE_URL', 'postgresql://user:pass@localhost:5432/shared', 'Shared database connection'),
((SELECT id FROM projects WHERE name = 'shared'), 'REDIS_URL', 'redis://localhost:6379', 'Shared Redis connection'),
((SELECT id FROM projects WHERE name = 'webapp'), 'APP_NAME', 'MyWebApp', 'Application name'),
((SELECT id FROM projects WHERE name = 'api'), 'API_VERSION', 'v1', 'API version')
ON CONFLICT (project_id, name) DO NOTHING;

-- Insert linked variable example
INSERT INTO env_vars (project_id, name, linked_to, description) VALUES 
((SELECT id FROM projects WHERE name = 'webapp'), 'DB_URL', 'shared:DATABASE_URL', 'Linked to shared database URL')
ON CONFLICT (project_id, name) DO NOTHING;

-- Insert concatenated variable example
INSERT INTO env_vars (project_id, name, concat_parts, description) VALUES 
((SELECT id FROM projects WHERE name = 'api'), 'FULL_DB_URL', 'shared:DATABASE_URL|api:API_VERSION', 'Database URL with API version suffix')
ON CONFLICT (project_id, name) DO NOTHING;

-- Insert project links
INSERT INTO project_links (source_project_id, target_project_id, link_type) VALUES 
((SELECT id FROM projects WHERE name = 'webapp'), (SELECT id FROM projects WHERE name = 'shared'), 'dependency'),
((SELECT id FROM projects WHERE name = 'api'), (SELECT id FROM projects WHERE name = 'shared'), 'dependency')
ON CONFLICT (source_project_id, target_project_id) DO NOTHING; 