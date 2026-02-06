# 卡牌图片下载工具

## 功能说明

这个工具用于批量下载和补充缺失的卡牌图片，支持：
- 从URL下载图片
- 自动转换为WebP格式
- 保留透明通道（PNG/RGBA）
- 自动保存到指定目录

## 使用方法

### 方式1：直接运行批处理文件（Windows）

双击 `download_images.bat` 即可启动工具。

### 方式2：使用Python运行

```bash
python tools/download_card_images.py
```

## 操作流程

1. **输入物品ID**
   - 例如：`7cbc8056-482b-4ccf-887a-ddb2702c856c`
   - 这个ID会作为文件名保存图片

2. **输入图片URL**
   - 粘贴完整的图片URL
   - 支持的格式：JPG, PNG, WebP, BMP, GIF等
   - 例如：`https://example.com/images/card.png`

3. **自动处理**
   - 工具会自动下载图片
   - 转换为WebP格式（质量90）
   - 保存到 `assets/images/card/{物品ID}.webp`

4. **重复或退出**
   - 输入下一个ID继续
   - 输入 `q` 或 `quit` 退出程序

## 示例

```
请输入物品ID (或输入 q 退出): 7cbc8056-482b-4ccf-887a-ddb2702c856c
请输入图片URL: https://example.com/fang.png

[下载] 正在从 https://example.com/fang.png 下载图片
[转换] 正在转换为 WebP 格式...
[成功] 图片已保存到: assets/images/card/7cbc8056-482b-4ccf-887a-ddb2702c856c.webp (45.2 KB)
```

## 注意事项

1. **图片已存在**
   - 如果图片已存在，工具会询问是否覆盖
   - 输入 `y` 覆盖，`n` 跳过

2. **URL格式**
   - 必须以 `http://` 或 `https://` 开头
   - 确保URL可以直接访问图片

3. **网络问题**
   - 如果下载失败，会显示错误信息
   - 可以重新尝试或检查URL是否正确

4. **图片质量**
   - WebP质量设置为90（高质量）
   - 保留透明通道（如果原图有）

## 依赖安装

如果首次使用，请先安装依赖：

```bash
pip install requests Pillow
```

或安装完整依赖：

```bash
pip install -r requirements.txt
```

## 文件说明

- `tools/download_card_images.py` - 主脚本
- `download_images.bat` - Windows批处理启动器
- `assets/images/card/` - 图片保存目录

## 退出程序

任何时候输入以下任一命令即可退出：
- `q`
- `quit`
- `exit`
- `退出`

或按 `Ctrl+C` 强制退出
