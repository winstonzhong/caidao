# Django 项目 Agent 通用开发规范

> 本文档为 Django 项目通用开发规范，适用于所有基于此框架的项目。
> 各项目特有规则请查阅项目自身的 `AGENTS.md`。

---

## 1. 绝对禁止删除数据库（🚨 最高优先级）

**规则**: 严禁直接删除数据库文件（如 `*.sqlite3`），除非：
1. 已明确获得用户授权确认
2. 已完成数据库备份
3. 有明确的恢复方案

**原因**:
- 数据库删除会导致所有数据永久丢失
- 重建迁移可能导致历史数据无法恢复
- 即使文件系统有备份，索引和关联关系也可能损坏

**正确做法**:
```bash
# 删除前必须备份
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)

# 然后才能执行删除/重建操作
```

**严禁执行**:
```bash
# ❌ 绝对禁止
rm *.sqlite3
rm /path/to/project/*.sqlite3
rm -f *.sqlite3
```

**如果必须重建**:
1. 先完整备份当前数据库
2. 导出数据（如有必要）：`python manage.py dumpdata > backup.json`
3. 执行重建操作
4. 验证数据完整性

---

## 2. 绝对禁止重启 Django 开发服务器（⚠️ 核心）

**规则**: 永远不要手动重启 Django 开发服务器 (`python manage.py runserver`)

**原因**: Django 有自动重载机制，手动重启会导致端口占用错误

**正确做法**:
- 保存文件后等待 1-2 秒自动重载
- 刷新浏览器验证即可
- **严禁执行**: `pkill -f "runserver"` 或手动重启

---

## 3. Django 模板加载优先级陷阱（⚠️ 重点）

**规则**: 修改模板后不生效时，首先检查是否存在模板覆盖

**原因**: Django 模板加载器按 `TEMPLATES.DIRS` 顺序查找，**项目级 `templates/` 目录优先级高于应用级 `app/templates/` 目录**

**典型案例**:
```
# settings.py 配置
TEMPLATES = [{
    'DIRS': [BASE_DIR / "templates"],  # 优先级高！
    'APP_DIRS': True,                   # 应用模板目录，优先级低
}]

# 文件结构
project/
├── templates/app/some_template.html      # 旧的，会被使用！
└── app/templates/app/some_template.html  # 新的，被覆盖！
```

**检查方法**:
```bash
# 查找同名模板文件
find . -name "*.html" -path "*/templates/*" | grep <模板名>
```

**正确做法**:
1. 修改模板前先查找是否存在同名文件
2. 删除项目级 `templates/` 下的重复模板，只保留应用级模板
3. 保持单一数据源，避免模板分散在多处

---

## 4. 任务完成通知（必须）

**规则**: 所有任务完成后必须：
1. 播放提示音 `task_complete.wav`
2. 输出：`✓ 我的任务已完成，请审阅！`

```python
import subprocess

print('\a', end='', flush=True)
subprocess.run(
    ['aplay', '/home/yka-003/workspace/agent-tools/task_complete.wav'],
    capture_output=True,
    timeout=5
)
print("✓ 我的任务已完成，请审阅！")
```

---

## 5. 版本控制规范（必须）

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

## 6. caidao 工具库导入方式（⚠️ 重要）

**规则**: 使用外部 caidao 工具库时，必须使用正确的导入语法

**配置**:
```python
# settings.py - 添加 caidao 目录本身到 sys.path
sys.path.append(str(BASE_DIR.parent / "caidao"))
```

**正确导入方式**:
```python
# ✅ 正确：直接导入模块
from helper_task_redis2 import GLOBAL_REDIS

# ❌ 错误：使用包导入语法
from caidao.helper_task_redis2 import GLOBAL_REDIS
```

**方法调用**:
```python
# ✅ 使用中文方法名
length = GLOBAL_REDIS.获取队列中任务个数(queue_name)
items = GLOBAL_REDIS.预览队列内容(queue_name, count)
success = GLOBAL_REDIS.删除任务队列(queue_name)
success = GLOBAL_REDIS.推入Redis(queue_name, data)

# ❌ 不要使用英文别名（已移除）
# length = GLOBAL_REDIS.get_queue_length(queue_name)
```

**绝对禁止**:
- ❌ 在项目本地创建 `caidao/` 目录作为"代理"
- ❌ 重复拷贝外部 caidao 的文件到本地
- ❌ 修改导入语句为 `from caidao.xxx import ...`

**历史教训**:
- 多次创建本地 caidao 目录导致文件重复、配置混乱
- 错误地将 caidao 作为 Python 包处理（添加 `__init__.py`）
- 混淆了直接导入和包导入的区别

---

## 7. doctest 单元测试规范（⚠️ 必须）

**规则**: 所有含 doctest 的 `.py` 文件必须遵守以下规范

### 7.1 fixture 路径必须使用 `__file__` 绝对路径

❌ **错误**：相对路径依赖工作目录
```python
>>> with open('ut/fixtures/task_719.xml') as f:
...     xml = f.read()
```

✅ **正确**：基于 `__file__` 的绝对路径，任意目录运行均可
```python
>>> from pathlib import Path
>>> _f = Path(__file__).parent.parent / 'ut' / 'fixtures' / 'task_719.xml'
>>> with open(_f) as f:
...     xml = f.read()
```

### 7.2 重复路径构造必须封装为模块级 helper 函数

❌ **错误**：超过 2 处重复的路径构造代码
```python
>>> _f = Path(__file__).parent.parent / 'ut' / 'fixtures' / 'popup_detector'
>>> with open(_f / 'a.xml') as f: xml_a = f.read()
>>> with open(_f / 'b.xml') as f: xml_b = f.read()
>>> img = cv2.imread(str(_f / 'c.png'))
```

✅ **正确**：提取为模块级 helper 函数，doctest 直接调用
```python
# 模块级别定义（类外面，全局命名空间）
def load_fixture(filename: str) -> str:
    from pathlib import Path
    fpath = Path(__file__).parent.parent / 'ut' / 'fixtures' / 'popup_detector' / filename
    with open(fpath, encoding='utf-8') as f:
        return f.read()

# doctest 中使用
>>> xml_a = load_fixture('a.xml')
>>> xml_b = load_fixture('b.xml')
>>> img = load_fixture_img('c.png')
```

### 7.3 `if __name__ == "__main__":` 仅用于触发执行

❌ **错误**：在 `__main__` 块内定义 doctest 依赖的函数
```python
if __name__ == "__main__":
    def load_fixture(filename):   # doctest 无法访问！
        ...
    import doctest
    doctest.testmod()
```

✅ **正确**：helper 函数定义在模块级别，`__main__` 仅触发 doctest
```python
def load_fixture(filename: str) -> str:   # 模块级别，doctest 可访问
    ...

if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False, report=False))
```

**原因**: doctest 在**模块导入时**执行，此时 `if __name__ == "__main__":` 块**尚未执行**。

### 7.4 模块级 doctest 与方法级 doctest 上下文隔离

模块 docstring 中定义的变量（如 `_fixture_dir`）在方法 docstring 的 doctest 中**不可见**。

```python
"""
>>> _fixture_dir = Path(__file__).parent / 'fixtures'
"""

class MyClass:
    def my_method(self):
        """
        >>> # _fixture_dir 在这里不可见！必须重新定义
        >>> from pathlib import Path
        >>> _f = Path(__file__).parent / 'fixtures'
        """
```

**推荐做法**：统一使用模块级 helper 函数，所有 doctest（模块级+方法级）都调用同一函数。

### 7.5 运行方式

```bash
# 方式1: 项目根目录（推荐）
cd /path/to/project
python -m doctest path/to/module.py -v

# 方式2: 任意目录（需模块含 __main__ 入口）
python /absolute/path/to/module.py
# 输出: TestResults(failed=0, attempted=61)
```

### 7.6 签入前必须运行 doctest

```bash
python -m doctest some_module.py
# 所有 .py 文件如有逻辑变更，必须运行对应 doctest
```

**要求**：
- 0 failures 方可签入
- 新增功能必须附带 doctest
- 修改逻辑后必须重新运行 doctest 验证

---

## 8. Django Views 绝对禁止异常黑洞（🚨 必须）

**规则**: 所有 Django `views.py` 中的 API 视图函数，**严禁**使用外层 `try/except Exception` 静默吞掉异常。

**禁止写法**:
```python
# ❌ 异常黑洞 — 后端看不到任何堆栈，无法定位问题
@require_http_methods(["GET"])
def my_api(request):
    try:
        ...
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
```

**正确写法**:
```python
# ✅ 异常直接抛出，由 Django 处理（DEBUG 模式显示错误页面，生产模式记录日志并返回 500）
@require_http_methods(["GET"])
def my_api(request):
    ...  # 不写外层 try/except，让异常自然抛出

# 或仅在需要局部容错时使用精确的异常类型
@require_http_methods(["GET"])
def my_api(request):
    try:
        ...
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    # 其他异常直接抛出，Django 会自动记录并返回 500
```

**原因**:
- 异常被吞掉后，后端控制台看不到任何堆栈，无法定位问题
- 前端只能看到模糊的 error 字符串，调试极其困难
- Django 的 DEBUG 模式会自动输出详细的错误页面（含堆栈），生产模式会自动记录日志并返回 500

**例外**: 局部容错场景（如图片处理失败不应阻断整体返回），但必须同时打印 traceback:
```python
except Exception as img_err:
    import traceback
    traceback.print_exc()
    # 继续执行，不阻断
```

---

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

---

## 测试与 doctest 变更保证（必须）

**规则**：当 `.py` 文件发生逻辑变更时，必须执行该文件的所有 doctest 单元测试以及所有单元测试和集成测试。

1. 若变更的文件包含 doctest，先运行对应 doctest：
   ```bash
   python -m doctest path/to/module.py
   # 或（模块含 __main__ 入口时）
   python /absolute/path/to/module.py
   ```
2. 再运行项目全部单元测试和集成测试：
   ```bash
   python manage.py test
   ```
   > 注：部分项目使用 `pytest` 或 `run_tests.py` / `run_all_tests.py`，请以项目实际测试命令为准。

**要求**：
- doctest 与全部测试均 0 failures 方可签入
- 新增功能必须附带 doctest
- 修改逻辑后必须重新运行 doctest 与全部测试验证
- 测试失败必须修复后再提交
- 测试覆盖率：单元测试 + 集成测试全覆盖
