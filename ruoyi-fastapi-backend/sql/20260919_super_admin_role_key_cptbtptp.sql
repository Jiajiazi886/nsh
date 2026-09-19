-- One-time production migration. Back up the database before running.
-- role_id is the stable identity; the login username is not changed.
UPDATE sys_role
SET role_key = 'cptbtptp',
    update_by = 'system',
    update_time = NOW()
WHERE role_id = 1
  AND role_key <> 'cptbtptp';
