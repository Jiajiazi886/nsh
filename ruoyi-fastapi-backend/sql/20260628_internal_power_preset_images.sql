-- 系统内功预设图片字段与内置图标回填。
-- 可重复执行：MySQL 8+ / MariaDB 10.3+。

SET @column_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'system_internal_power_preset'
    AND COLUMN_NAME = 'image_url'
);

SET @ddl := IF(
  @column_exists = 0,
  'ALTER TABLE system_internal_power_preset ADD COLUMN image_url varchar(255) DEFAULT '''' COMMENT ''内功图片地址'' AFTER bonus_desc',
  'SELECT 1'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE system_internal_power_preset
SET image_url = CASE
  WHEN name = '破釜' AND element_key = 'metal' THEN '/neigong/01_破釜_金.png'
  WHEN name = '贯山月' AND element_key = 'metal' THEN '/neigong/02_贯山月_金.png'
  WHEN name = '惊羽' AND element_key = 'metal' THEN '/neigong/03_惊羽_金.png'
  WHEN name = '击衰' AND element_key = 'metal' THEN '/neigong/04_击衰_金.png'
  WHEN name = '锻寒芒' AND element_key = 'metal' THEN '/neigong/05_锻寒芒_金.png'
  WHEN name = '移星障' AND element_key = 'wood' THEN '/neigong/06_移星障_木.png'
  WHEN name = '凌穹' AND element_key = 'wood' THEN '/neigong/07_凌穹_木.png'
  WHEN name = '沧浪行' AND element_key = 'wood' THEN '/neigong/08_沧浪行_木.png'
  WHEN name = '裁锋' AND element_key = 'wood' THEN '/neigong/09_裁锋_木.png'
  WHEN name = '破重云' AND element_key = 'wood' THEN '/neigong/10_破重云_木.png'
  WHEN name = '珠明' AND element_key = 'water' THEN '/neigong/11_珠明_水.png'
  WHEN name = '望惊川' AND element_key = 'water' THEN '/neigong/12_望惊川_水.png'
  WHEN name = '沉浪' AND element_key = 'water' THEN '/neigong/13_沉浪_水.png'
  WHEN name = '鲸落' AND element_key = 'water' THEN '/neigong/14_鲸落_水.png'
  WHEN name = '噬汐' AND element_key = 'water' THEN '/neigong/15_噬汐_水.png'
  WHEN name = '楚狂歌' AND element_key = 'fire' THEN '/neigong/16_楚狂歌_火.png'
  WHEN name = '斩精' AND element_key = 'fire' THEN '/neigong/17_斩精_火.png'
  WHEN name = '众妙' AND element_key = 'fire' THEN '/neigong/18_众妙_火.png'
  WHEN name = '燎原' AND element_key = 'fire' THEN '/neigong/19_燎原_火.png'
  WHEN name = '焚刃' AND element_key = 'fire' THEN '/neigong/20_焚刃_火.png'
  WHEN name = '征袍' AND element_key = 'earth' THEN '/neigong/21_征袍_土.png'
  WHEN name = '御千嶂' AND element_key = 'earth' THEN '/neigong/22_御千嶂_土.png'
  WHEN name = '固垒' AND element_key = 'earth' THEN '/neigong/23_固垒_土.png'
  WHEN name = '覆沙阙' AND element_key = 'earth' THEN '/neigong/24_覆沙阙_土.png'
  WHEN name = '纳百观' AND element_key = 'earth' THEN '/neigong/25_纳百观_土.png'
  WHEN name = '五韵谣' AND element_key = 'mixed' THEN '/neigong/26_五韵谣_金木水火土.png'
  WHEN name = '稀有-日月两仪' AND element_key = 'fire' THEN '/neigong/27_稀有-日月两仪_火.png'
  WHEN name = '稀有-日月两仪' AND element_key = 'earth' THEN '/neigong/28_稀有-日月两仪_土.png'
  WHEN name = '稀有-不动明王' AND element_key = 'wood' THEN '/neigong/29_稀有-不动明王_木.png'
  WHEN name = '稀有-不动明王' AND element_key = 'water' THEN '/neigong/30_稀有-不动明王_水.png'
  WHEN name = '稀有-绝电惊沙' AND element_key = 'metal' THEN '/neigong/31_稀有-绝电惊沙_金.png'
  WHEN name = '稀有-绝电惊沙' AND element_key = 'wood' THEN '/neigong/32_稀有-绝电惊沙_木.png'
  WHEN name = '稀有-承影锋烁' AND element_key = 'metal' THEN '/neigong/33_稀有-承影锋烁_金.png'
  WHEN name = '稀有-承影锋烁' AND element_key = 'fire' THEN '/neigong/34_稀有-承影锋烁_火.png'
  WHEN name = '稀有-灼星贯日' AND element_key = 'wood' THEN '/neigong/35_稀有-灼星贯日_木.png'
  WHEN name = '稀有-灼星贯日' AND element_key = 'fire' THEN '/neigong/36_稀有-灼星贯日_火.png'
  ELSE image_url
END,
update_time = NOW()
WHERE (image_url IS NULL OR image_url = '')
  AND name IN (
    '破釜', '贯山月', '惊羽', '击衰', '锻寒芒', '移星障', '凌穹', '沧浪行', '裁锋', '破重云',
    '珠明', '望惊川', '沉浪', '鲸落', '噬汐', '楚狂歌', '斩精', '众妙', '燎原', '焚刃',
    '征袍', '御千嶂', '固垒', '覆沙阙', '纳百观', '五韵谣',
    '稀有-日月两仪', '稀有-不动明王', '稀有-绝电惊沙', '稀有-承影锋烁', '稀有-灼星贯日'
  );
