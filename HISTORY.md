# Changelog

## v0.2.0 (2026-06-12) — API 设计改进

### Breaking Changes

#### 1. match 方向反转
```python
# 旧: data.match(pattern)
Chain(['a', 'b']).match(Chain([Patom.any(0), 'b']))

# 新: pattern.match(data)
Chain([Patom.any(0), 'b']).match(Chain(['a', 'b']))
```

#### 2. any() 语义调整
```python
# 旧: any(0) = 无限制, any(max=0) = 无限制
# 新: any(0) = 无限制, any(max=0) 报错, any(max=-1) = 无限制
Patom.any(0)      # 0 或更多 ✓
Patom.any()       # 至少 1 个 ✓
Patom.any(max=0)  # ValueError ✗
Patom.any(max=-1) # 无限制 ✓
```

#### 3. long → len
```python
# 旧
Patom.long(3)
Patom.long(2, 5)

# 新
Patom.len(3)
Patom.len(2, 5)
```

#### 4. apply 参数 long → count
```python
# 旧
Patom.apply(func, long=2)

# 新
Patom.apply(func, count=2)
```

#### 5. startswith 删除
```python
# 旧
chain.startswith(prefix)

# 新 (使用 match partial)
pattern.match(data, partial=True)
```

#### 6. ext() 必须传参
```python
# 旧
Patom.ext()  # 无意义的空操作

# 新
Patom.ext(chain)  # 必须传参
```

### New Features

#### 1. Chain / Chain 拼接
```python
Chain(['a', 'b']) / Chain(['c', 'd'])  # Chain(['a', 'b', 'c', 'd'])
```

#### 2. Chain.from_str()
```python
Chain.from_str('a.b.c')    # Chain(['a', 'b', 'c'])
Chain.from_str('.a.b.c')   # Chain(['a', 'b', 'c'])
```

#### 3. 数字自动转字符串
```python
Chain([123])       # Chain(['123'])
Chain / 1 / 2 / 3  # Chain(['1', '2', '3'])
Chain([3.14])      # Chain(['3.14'])
```

#### 4. enum 支持字符串
```python
# 旧: 必须包 Chain
Patom.enum(Chain(['a']), Chain(['b']))

# 新: 字符串自动解析 (支持点分)
Patom.enum('a', 'b', 'c')
Patom.enum('type.h1', 'type.h2')
```

#### 5. ext 支持字符串和 Atom
```python
# 旧: 只支持 Chain
Patom.ext(Chain(['a']))

# 新: 支持 Chain、字符串、ChainPatternAtom
Patom.ext('a')
Patom.ext('a.b')
Patom.ext(Patom.enum('x', 'y'))
```

#### 6. 糖语法支持数字段
```python
# 旧: .hi.123 不支持
# 新: .hi.123 → Chain(['hi', '123'])
```

#### 7. 糖语法 .match() 继续被吞
```python
# .user.admin.match(rule) 中的 .match() 会被当作链段
# 正确用法: rule.match(.user.admin)
```

### Files Changed

| 文件 | 改动说明 |
|------|----------|
| `src/latychain/_chain.py` | match方向、Chain/Chain拼接、from_str、数字转字符串、__getitem__切片返回Chain |
| `src/latychain/_atoms.py` | any语义、long→len、apply long→count、enum支持字符串、ext必填+支持Atom |
| `src/latychain/_hook.py` | 糖语法match不被吞、支持数字段 |
| `src/latychain/__init__.py` | 文档同步 |
| `README.md` | 全面重写 |
| `docs/api-reference.md` | 全面重写 |
| `docs/guide.md` | 全面重写 |
| `test/test_core.py` | 更新测试 |
| `test/_test_doc_examples.py` | 更新测试 |
| `test/_test_doc_sugar.py` | 更新测试 |
| `test/_test_sugar.py` | 更新测试 |
| `test/_verify_readme_explicit.py` | 更新测试 |
| `test/_verify_readme_sugar.py` | 更新测试 |

### Test Results

```
Core API: 40 passed, 0 failed
Sugar syntax: ✅ All passed
Doc examples: 31 passed, 0 failed
README explicit: 9 passed, 0 failed
README sugar: ✅ All passed
pytest: 40 passed in 0.77s
```
