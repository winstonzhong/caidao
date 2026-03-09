# Agent 开发规范

> 已知陷阱详见 [AGENTS_TRAPS.md](./AGENTS_TRAPS.md)

---

## 1. 绝对禁止重启 Django 开发服务器（⚠️ 核心）

**规则**: 永远不要手动重启 Django 开发服务器 (`python manage.py runserver`)

**原因**: Django 有自动重载机制，手动重启会导致端口占用错误

**正确做法**: 
- 保存文件后等待 1-2 秒自动重载
- 刷新浏览器验证即可
- **严禁执行**: `pkill -f "runserver"` 或手动重启

---

## 2. 任务完成通知（必须）

**规则**: 所有任务完成后必须：
1. 播放提示音 `task_complete.wav`
2. 输出：`✓ 我的任务已完成，请审阅！`

```python
import subprocess

print('\a', end='', flush=True)
subprocess.run(['aplay', 'task_complete.wav'], capture_output=True, timeout=5)
print("✓ 我的任务已完成，请审阅！")
```

---

## 3. 版本控制规范（必须）

**规则**: 每次代码变更后立即执行 Git 签入

```bash
git add <变更的文件>
git commit -m "<type>: <描述>"
git tag -a "<标签>" -m "<描述>"
```

**签入后要求**: 必须输出简要汇总（约两行），提示用户已签入

示例输出：
```
✓ 已签入 3 个文件: runtime/models.py, runtime/admin.py
  提交: feat: 添加场景分布修复功能 | 标签: v1.2.0
```

提交类型：`feat`, `fix`, `refactor`, `docs`, `perf`

---

## 4. 测试保证（必须）

**规则**: 当 `.py` 文件发生逻辑变更时，必须执行所有单元测试和集成测试

```bash
python manage.py test
```

**要求**:
- 所有测试必须通过后才可签入
- 如有测试失败，必须修复后再提交
- 测试覆盖率：单元测试 + 集成测试全覆盖

**目的**: 防止代码回归，确保功能正确性
