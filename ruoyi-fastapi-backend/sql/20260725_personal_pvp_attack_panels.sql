-- 个人防守计算器：用户私有进攻方面板模板与账号级当前设置。
-- MySQL 8+ / MariaDB 10.3+，可与应用启动时的 Base.metadata.create_all 共用。

CREATE TABLE IF NOT EXISTS personal_pvp_attack_panel (
  panel_id BIGINT NOT NULL AUTO_INCREMENT COMMENT '面板主键',
  user_id BIGINT NOT NULL COMMENT '所属用户ID',
  sequence_no INT NOT NULL COMMENT '用户内模板序号',
  panel_name VARCHAR(100) NOT NULL COMMENT '系统生成的面板名称',
  panel_json LONGTEXT NOT NULL COMMENT '进攻方面板JSON',
  create_time DATETIME NULL COMMENT '创建时间',
  update_time DATETIME NULL COMMENT '更新时间',
  PRIMARY KEY (panel_id),
  UNIQUE KEY uq_personal_pvp_attack_panel_user_sequence (user_id, sequence_no),
  KEY idx_personal_pvp_attack_panel_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='个人PVP进攻方面板模板表';

CREATE TABLE IF NOT EXISTS personal_defense_calculator_setting (
  user_id BIGINT NOT NULL COMMENT '用户ID',
  defender_json LONGTEXT NOT NULL COMMENT '防守方面板JSON',
  selected_panel_source VARCHAR(16) NOT NULL DEFAULT 'system' COMMENT '面板来源 system 或 personal',
  selected_panel_id BIGINT NOT NULL DEFAULT 0 COMMENT '选中面板ID',
  create_time DATETIME NULL COMMENT '创建时间',
  update_time DATETIME NULL COMMENT '更新时间',
  PRIMARY KEY (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='个人防守计算器设置表';
