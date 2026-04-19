-- Add Quality Assurance role for RBAC (employees.role)
ALTER TABLE employees DROP CONSTRAINT IF EXISTS employees_role_check;
ALTER TABLE employees ADD CONSTRAINT employees_role_check CHECK (
  role IN ('admin', 'operational', 'call_center', 'quality_assurance')
);

INSERT INTO employees (id, name, email, password_hash, role, department) VALUES
  (
    'a0000000-0000-0000-0000-000000000004',
    'QA Lead',
    'qa@company.com',
    '$2b$12$X9U.MfNpEckUSkUYVZdZoe5J/Gs2SeXb0maDXrq49SRFZB/9WjHfi',
    'quality_assurance',
    'Quality Assurance'
  )
ON CONFLICT (email) DO UPDATE SET
  role = EXCLUDED.role,
  department = EXCLUDED.department;
