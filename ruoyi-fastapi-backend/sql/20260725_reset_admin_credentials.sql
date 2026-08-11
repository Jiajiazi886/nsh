-- For an existing deployment only. A new database already receives these values from ruoyi-fastapi.sql.
UPDATE sys_user
SET user_name = 'cptbtptp369',
    password = '$2b$12$YvxDRUVcRBiYUZF1CxwVS.uShtsv7hqoEXAGP8VqcJjWcFDfATLNW',
    update_by = 'cptbtptp369',
    update_time = NOW()
WHERE user_id = 1;
