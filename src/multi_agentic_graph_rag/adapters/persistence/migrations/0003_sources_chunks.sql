CREATE TABLE agentic_qa.sources (
    project_id uuid NOT NULL,
    run_id uuid NOT NULL,
    source_id uuid NOT NULL,
    schema_version integer NOT NULL CHECK (schema_version >= 1),
    source_path text NOT NULL CHECK (source_path <> ''),
    extension text NOT NULL CHECK (extension IN ('.pdf', '.docx')),
    byte_checksum char(64) NOT NULL,
    normalized_checksum char(64) NOT NULL,
    block_count integer NOT NULL CHECK (block_count >= 0),
    PRIMARY KEY (project_id, run_id, source_id),
    FOREIGN KEY (project_id, run_id) REFERENCES agentic_qa.runs(project_id, run_id)
);

CREATE TABLE agentic_qa.chunks (
    project_id uuid NOT NULL,
    run_id uuid NOT NULL,
    source_id uuid NOT NULL,
    chunk_id uuid NOT NULL,
    schema_version integer NOT NULL CHECK (schema_version >= 1),
    ordinal integer NOT NULL CHECK (ordinal >= 0),
    text text NOT NULL CHECK (text <> ''),
    text_checksum char(64) NOT NULL,
    provenance jsonb NOT NULL,
    PRIMARY KEY (project_id, run_id, chunk_id),
    UNIQUE (project_id, run_id, source_id, ordinal),
    FOREIGN KEY (project_id, run_id, source_id)
        REFERENCES agentic_qa.sources(project_id, run_id, source_id)
);
