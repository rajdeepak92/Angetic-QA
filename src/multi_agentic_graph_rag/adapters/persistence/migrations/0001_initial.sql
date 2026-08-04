CREATE TABLE agentic_qa.projects (
    project_id uuid PRIMARY KEY,
    schema_version integer NOT NULL CHECK (schema_version >= 1),
    name text NOT NULL CHECK (name <> '' AND name = btrim(name)),
    created_at timestamptz NOT NULL
);

CREATE TABLE agentic_qa.runs (
    project_id uuid NOT NULL REFERENCES agentic_qa.projects(project_id),
    run_id uuid NOT NULL,
    schema_version integer NOT NULL CHECK (schema_version >= 1),
    target_stage text NOT NULL CHECK (
        target_stage IN ('requirements', 'user_stories', 'test_scenarios')
    ),
    status text NOT NULL CHECK (
        status IN ('pending', 'running', 'succeeded', 'failed', 'blocked', 'cancelled')
    ),
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL CHECK (updated_at >= created_at),
    error_category text,
    error_message text CHECK (error_message IS NULL OR length(error_message) BETWEEN 1 AND 500),
    PRIMARY KEY (project_id, run_id),
    CHECK ((status = 'failed') = (error_category IS NOT NULL AND error_message IS NOT NULL)),
    CHECK (
        error_category IS NULL OR error_category IN (
            'validation', 'conflict', 'not_found', 'transient_provider',
            'transient_store', 'permanent_provider', 'permanent_store',
            'integrity', 'cancellation'
        )
    )
);
