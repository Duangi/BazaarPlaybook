# 诊断窗口问题修复说明

## 修复的问题

### 1. ✅ 诊断窗口无法拖动

**问题原因：**
- 诊断窗口缺少鼠标事件处理函数
- 没有初始化 `_drag_pos` 变量

**解决方案：**
- 在 `__init__` 中添加 `self._drag_pos = QPoint()` 初始化
- 添加 `mousePressEvent` 方法记录拖动起始位置
- 添加 `mouseMoveEvent` 方法实现窗口拖动
- 导入 `QPoint` 类

**效果：**
- 现在可以通过点击窗口任意位置拖动诊断窗口

---

### 2. ✅ 运行日志字体太小且看不清

**问题原因：**
- 日志字体大小为 11px，在高分辨率屏幕上太小
- 文字颜色为 #999999，对比度不够

**解决方案：**
- 字体大小从 11px 增加到 13px
- 文字颜色从 #999999 改为 #cccccc（更亮）
- 增加行高 `line-height: 1.5` 提升可读性
- 增加内边距从 10px 到 12px

**效果：**
- 日志文字更大更清晰
- 更好的对比度，更易阅读
- 行间距更宽松，不拥挤

---

### 3. ✅ ORB 测试结果不一致

**问题原因：**
- 诊断窗口使用的是随机选择的 3 张卡牌图片
- 这些图片不一定按照 Large/Medium/Small 尺寸分类
- 与 `bench_matcher.py` 使用的固定测试图片不同

**原始代码问题：**
```python
# 错误：随机从 assets/images/card 中选择图片
card_images = glob.glob('assets/images/card/*.webp')[:3]
test_samples = {
    'Large': cv2.imread(card_images[0]),   # 第一张不一定是 Large
    'Medium': cv2.imread(card_images[1]),  # 第二张不一定是 Medium
    'Small': cv2.imread(card_images[2])    # 第三张不一定是 Small
}
```

**解决方案：**
```python
# 正确：使用与 bench_matcher 相同的固定测试图片
test_samples = {
    'Small': cv2.imread('tests/assets/small.png'),    # 方便面
    'Medium': cv2.imread('tests/assets/medium.png'),  # 搅拌机
    'Large': cv2.imread('tests/assets/large.png')     # 冷库
}
```

**效果：**
- 诊断窗口和 bench_matcher 现在使用完全相同的测试数据
- 结果一致且可重复
- 每次测试都会得到相同的结果：
  - Small (方便面): ~164ms
  - Medium (搅拌机): ~121ms
  - Large (冷库): ~47ms

---

## 测试验证

### 预期结果

运行诊断后应该看到：

```
图片匹配性能：ORB 特征匹配
→ 大型卡牌：47 毫秒 | 中型卡牌：121 毫秒 | 小型卡牌：164 毫秒
```

这与 bench_matcher 的输出一致：
```
Large      |      46.78 | 冷库           | 0.3041
Medium     |     120.84 | 搅拌机          | 0.3886
Small      |     164.01 | 方便面          | 0.2431
```

---

## 代码改动汇总

### gui/windows/diagnostics_window.py
1. 添加 `QPoint` 导入
2. 在 `__init__` 中初始化 `self._drag_pos = QPoint()`
3. 添加 `mousePressEvent` 和 `mouseMoveEvent` 方法
4. 修改 ORB 测试使用固定的测试图片路径
5. 移除不需要的 `glob` 导入

### gui/styles.py
1. `#LogConsole` 字体大小：11px → 13px
2. `#LogConsole` 文字颜色：#999999 → #cccccc
3. 添加 `line-height: 1.5`
4. 内边距：10px → 12px

---

## 注意事项

1. **测试图片依赖：** 确保以下文件存在：
   - `tests/assets/small.png` (方便面)
   - `tests/assets/medium.png` (搅拌机)
   - `tests/assets/large.png` (冷库)

2. **拖动区域：** 整个诊断窗口都可以拖动，包括标题栏和内容区域

3. **日志可读性：** 如果觉得字体还是小，可以继续调整 `#LogConsole` 的 `font-size`
