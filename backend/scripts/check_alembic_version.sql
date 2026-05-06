-- 检查当前 alembic 版本
SELECT * FROM alembic_version;

-- 检查所有表是否存在
SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE() ORDER BY table_name;
