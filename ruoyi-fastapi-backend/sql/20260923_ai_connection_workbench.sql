-- 大模型配置（MySQL）
-- API Key 仍以 Fernet 密文存储，TEXT 用于兼容更长的上游密钥。

alter table ai_models
    modify column api_key text null comment 'API Key（加密存储）';

-- 将旧版单 Mimo Key 记录补齐为可编辑连接，保留原密文。
update ai_models
set model_code = 'mimo-v2.5',
    model_name = coalesce(nullif(model_name, ''), 'Mimo 图片识别'),
    base_url = coalesce(nullif(base_url, ''), 'https://api.xiaomimimo.com/v1'),
    model_type = 'chat_completions',
    max_tokens = coalesce(max_tokens, 2048),
    support_images = 'Y',
    status = '0',
    update_by = 'ai-workbench-migration',
    update_time = now()
where model_code = '__internal_power_mimo__'
  and provider = 'Mimo';

-- 若历史数据中存在多个“当前”项，保留排序最前的一个。
update ai_models
set status = '1'
where status = '0'
  and model_id <> (
      select active_id
      from (
          select model_id as active_id
          from ai_models
          where status = '0'
          order by model_sort, model_id
          limit 1
      ) as active_connection
  );

update sys_menu
set menu_name = '大模型配置',
    remark = '管理多套 AI 连接并切换全系统当前 AI'
where menu_id = 3050;
