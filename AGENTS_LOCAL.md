## 1. 数据库迁移规范（⚠️ 必须）

**规则**: 进行数据库结构变更（迁移）时，必须：

1. **迁移前备份** - 使用滚动备份脚本备份所有数据库
2. **使用 mm.bat 迁移** - 统一使用项目中的迁移脚本执行迁移
3. **禁止删除数据库** - 严禁删除数据库文件进行重建

**原因**:
- 数据库迁移可能导致数据丢失或结构损坏
- 多数据库配置（default/base）需要一致迁移
- 备份可确保意外情况下可恢复

**正确做法**:

```bash
# 步骤1: 执行滚动备份（迁移前必须）
cd /home/yka-003/workspace/caidao/backups
./rolling_backup.sh

# 步骤2: 执行数据库迁移（使用项目脚本）
cd /home/yka-003/workspace/caidao
./mm.bat
# 或手动执行：
# python manage.py makemigrations
# python manage.py migrate
# python manage.py migrate --database=base
```

**严禁执行**:
```bash
# ❌ 禁止先删除再重建
rm /home/yka-003/workspace/caidao/*.sqlite3

# ❌ 禁止使用 --fake 绕过迁移（除非确定知道后果）
python manage.py migrate --fake

# ❌ 禁止直接删除迁移文件后重建
rm */migrations/00*.py
```

---

## 2. 测试保证（必须）

**规则**: 当 `.py` 文件发生逻辑变更时，必须执行所有单元测试和集成测试

```bash
python manage.py test
```

**要求**:
- 所有测试必须通过后才可签入
- 如有测试失败，必须修复后再提交
- 测试覆盖率：单元测试 + 集成测试全覆盖

**目的**: 防止代码回归，确保功能正确性
