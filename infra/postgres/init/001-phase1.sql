CREATE TABLE IF NOT EXISTS phase1_environment_marker (
    id integer PRIMARY KEY,
    initialized_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO phase1_environment_marker (id)
VALUES (1)
ON CONFLICT (id) DO NOTHING;
