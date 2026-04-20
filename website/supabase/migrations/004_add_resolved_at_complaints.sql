-- Add resolved_at if your project was created before this column existed.
-- Run in Supabase SQL Editor if PUT /api/complaints still errors on resolved_at after you re-enable it in code.
ALTER TABLE complaints ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;

COMMENT ON COLUMN complaints.resolved_at IS 'First transition to resolved/closed; optional if only updated_at is used';
