-- Persistent Univer workbook data for guild schedule free-form sheets.
-- Safe to run more than once against the local MySQL development database.

CREATE TABLE IF NOT EXISTS guild_schedule_workbook (
  workbook_id bigint NOT NULL AUTO_INCREMENT COMMENT '自由表格ID',
  schedule_id bigint NOT NULL DEFAULT 0 COMMENT '排表ID',
  workbook_json longtext NOT NULL COMMENT 'Univer工作簿JSON',
  create_time datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_time datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (workbook_id),
  UNIQUE KEY uk_guild_schedule_workbook_schedule (schedule_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='约战排表自由表格数据表';
