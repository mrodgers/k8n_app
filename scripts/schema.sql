-- Research System SQL Schema for PostgreSQL

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at DOUBLE PRECISION NOT NULL,
    updated_at DOUBLE PRECISION NOT NULL,
    assigned_to VARCHAR(64),
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}'
);

-- Create index for task status
CREATE INDEX IF NOT EXISTS tasks_status_idx ON tasks(status);
CREATE INDEX IF NOT EXISTS tasks_assigned_idx ON tasks(assigned_to);

-- Results table
CREATE TABLE IF NOT EXISTS results (
    id VARCHAR(64) PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    format VARCHAR(20) NOT NULL DEFAULT 'text',
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_at DOUBLE PRECISION NOT NULL,
    updated_at DOUBLE PRECISION NOT NULL,
    created_by VARCHAR(64),
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}'
);

-- Create indexes for results
CREATE INDEX IF NOT EXISTS results_task_id_idx ON results(task_id);
CREATE INDEX IF NOT EXISTS results_status_idx ON results(status);
CREATE INDEX IF NOT EXISTS results_created_by_idx ON results(created_by);

-- Add comments for documentation
COMMENT ON TABLE tasks IS 'Research tasks for the system';
COMMENT ON TABLE results IS 'Results generated from research tasks';
COMMENT ON COLUMN tasks.id IS 'Unique identifier for the task';
COMMENT ON COLUMN tasks.title IS 'Short descriptive title for the task';
COMMENT ON COLUMN tasks.description IS 'Detailed description of the research task';
COMMENT ON COLUMN tasks.status IS 'Current status (pending, in_progress, completed, failed)';
COMMENT ON COLUMN tasks.created_at IS 'Timestamp when the task was created';
COMMENT ON COLUMN tasks.updated_at IS 'Timestamp when the task was last updated';
COMMENT ON COLUMN tasks.assigned_to IS 'Agent or user assigned to this task';
COMMENT ON COLUMN tasks.tags IS 'Array of tags for categorizing tasks';
COMMENT ON COLUMN tasks.metadata IS 'Additional properties for the task';
COMMENT ON COLUMN results.id IS 'Unique identifier for the result';
COMMENT ON COLUMN results.task_id IS 'Reference to the associated task';
COMMENT ON COLUMN results.content IS 'Main content of the research result';
COMMENT ON COLUMN results.format IS 'Format of the content (text, json, html, etc.)';
COMMENT ON COLUMN results.status IS 'Current status (draft, reviewed, final)';
COMMENT ON COLUMN results.created_at IS 'Timestamp when the result was created';
COMMENT ON COLUMN results.updated_at IS 'Timestamp when the result was last updated';
COMMENT ON COLUMN results.created_by IS 'Agent or user who created this result';
COMMENT ON COLUMN results.tags IS 'Array of tags for categorizing results';
COMMENT ON COLUMN results.metadata IS 'Additional properties for the result';