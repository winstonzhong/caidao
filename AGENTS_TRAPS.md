# 已知陷阱

记录开发过程中遇到的已知问题和陷阱。

---

## 1. Admin short_description 不能包含 `%`

**问题**: Django 的 `short_description` 支持字符串格式化，`%` 会被解释为格式说明符。

**错误示例**:
```python
check_similarity.short_description = "检查相似度 (>=60%)"  # ❌ 报错
```

**错误信息**:
```
ValueError: unsupported format character ')' (0x29) at index 12
```

**正确写法**:
```python
check_similarity.short_description = "检查相似度阈值超标"  # ✅
```

---

## 2. 禁止本地创建动态场景图片

**规则**: 所有动态场景图片必须由 AI 外部生成

**要求**:
- 本地只创建带文字说明的占位符
- 占位符格式：`[Placeholder - AI Image Pending]`
- 禁止直接生成最终图片文件

**原因**: 确保视觉质量，统一由 AI 生成高清图片

---

## 3. Attribute 模型字段名是 `attr_id` 而非 `attribute_id`

**问题**: 在 `game_data.Attribute` 模型中，属性ID字段是 `attr_id`，但容易误写为 `attribute_id`。

**错误示例**:
```python
# runtime/executor.py 中的 _handle_death 方法
for state in snapshot.attribute_states.all():
    if state.attribute.attribute_id == 'res_hp':  # ❌ 错误！
        state.cached_value = 0
        state.save()
```

**问题影响**:
- 条件判断始终为 False，代码块不会执行
- 角色死亡时 HP 不会被正确设置为 0
- 面板显示的 HP 值与日志记录不一致

**正确写法**:
```python
# 修复后的代码
for state in snapshot.attribute_states.all():
    if state.attribute.attr_id == 'hp':  # ✅ 正确！
        state.cached_value = 0
        state.save()
```

**注意事项**:
- `Attribute.attr_id` 存储的是纯属性ID（如 `'hp'`）
- DataFrame 中的列名是 `res_hp` / `attr_hp` （带前缀）
- 但模型字段是 `attr_id`，不是 `attribute_id`
- 此外，Attribute 中的 ID 是 `'hp'` 而非 `'res_hp'`
