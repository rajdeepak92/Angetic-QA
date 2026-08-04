ALTER TABLE agentic_qa.runs
ADD CONSTRAINT runs_failure_consistency CHECK (
    (status = 'failed' AND error_category IS NOT NULL AND error_message IS NOT NULL)
    OR
    (status <> 'failed' AND error_category IS NULL AND error_message IS NULL)
);
