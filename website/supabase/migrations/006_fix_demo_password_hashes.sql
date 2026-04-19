-- Fixes login for all demo accounts: password is `admin123`
-- Run once if employees still have the old invalid bcrypt placeholder.
UPDATE employees
SET password_hash = '$2b$12$X9U.MfNpEckUSkUYVZdZoe5J/Gs2SeXb0maDXrq49SRFZB/9WjHfi',
    updated_at = now()
WHERE email IN (
  'admin@company.com',
  'ops@company.com',
  'support@company.com',
  'qa@company.com'
);
