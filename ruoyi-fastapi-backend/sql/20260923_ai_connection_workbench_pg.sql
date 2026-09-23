-- AI 连接工作台（PostgreSQL）

alter table ai_models alter column api_key type text;

update ai_models
set model_code = 'mimo-v2.5',
    model_name = coalesce(nullif(model_name, ''), 'Mimo 图片识别'),
    base_url = coalesce(nullif(base_url, ''), 'https://api.xiaomimimo.com/v1'),
    model_type = 'chat_completions',
    max_tokens = coalesce(max_tokens, 2048),
    support_images = 'Y',
    status = '0',
    update_by = 'ai-workbench-migration',
    update_time = current_timestamp
where model_code = '__internal_power_mimo__'
  and provider = 'Mimo';

with active_connection as (
    select model_id
    from ai_models
    where status = '0'
    order by model_sort, model_id
    limit 1
)
update ai_models
set status = '1'
where status = '0'
  and model_id <> (select model_id from active_connection);

update sys_menu
set menu_name = 'AI连接工作台',
    remark = '管理多套 AI 连接并切换全系统当前 AI'
where menu_id = 3050;
