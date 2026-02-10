# Steam Deck 安装和使用指南

## 系统要求

- Steam Deck（游戏模式或桌面模式）
- SteamOS 3.x（基于 Arch Linux）
- 游戏需运行在窗口模式或无边框窗口模式

## 快速安装（桌面模式）

### 1. 进入桌面模式

从游戏模式按下 STEAM 按钮，选择"电源" > "切换到桌面"

### 2. 打开终端（Konsole）

在应用启动器中搜索"Konsole"并打开

### 3. 禁用只读文件系统（仅首次）

```bash
sudo steamos-readonly disable
```

输入密码（如果没有设置过，先用 `passwd` 命令设置）

### 4. 安装 Python 和 pip

```bash
# 更新包数据库
sudo pacman -Sy

# 安装 Python 和 pip
sudo pacman -S python python-pip

# 验证安装
python --version
pip --version
```

### 5. 克隆项目（或使用 USB 拷贝）

**方式 A：使用 git**
```bash
sudo pacman -S git
cd ~/Documents
git clone https://github.com/Duangi/BazaarPlaybook.git
cd BazaarPlaybook
```

**方式 B：USB 拷贝**
```bash
# 插入 USB，然后拷贝项目到用户目录
cp -r /run/media/deck/YOUR_USB/BazaarPlaybook ~/Documents/
cd ~/Documents/BazaarPlaybook
```

### 6. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 如果遇到权限问题，使用 --user
pip install --user -r requirements.txt
```

### 7. 运行项目

```bash
python main.py
```

## 游戏模式运行（高级）

### 方式 1：添加为非 Steam 游戏

1. 创建启动脚本：
```bash
cat > ~/BazaarPlaybook_launcher.sh << 'EOF'
#!/bin/bash
cd ~/Documents/BazaarPlaybook
python main.py
EOF

chmod +x ~/BazaarPlaybook_launcher.sh
```

2. 在 Steam 中：
   - 游戏 > 添加非 Steam 游戏
   - 浏览并选择 `~/BazaarPlaybook_launcher.sh`
   - 添加后可以在游戏模式下启动

### 方式 2：使用 Decky Loader 插件（推荐）

1. 安装 Decky Loader（如果未安装）
2. 通过 Decky 插件商店安装"SteamGridDB"和"AutoFlatpaks"
3. 将项目添加为系统服务或开机自启动

## 窗口管理说明

### X11 vs Wayland

**游戏模式（Gamescope）**：
- 使用 Gamescope 合成器（基于 Wayland）
- 通过 XWayland 兼容层支持 X11 应用
- 窗口管理功能完全可用

**桌面模式（KDE Plasma）**：
- 默认使用 X11 会话
- 窗口管理功能完全兼容
- 支持所有窗口操作

### 验证环境

```bash
# 检查显示服务器类型
echo $XDG_SESSION_TYPE
# 输出 "x11" 表示使用 X11（推荐）
# 输出 "wayland" 可能需要 XWayland 兼容层

# 检查 DISPLAY 变量
echo $DISPLAY
# 应输出 :0 或 :1

# 测试 X11 连接
xdpyinfo | head -n 5
# 应显示显示器信息
```

## 故障排查

### 问题：ImportError: No module named 'Xlib'

**解决方案**：
```bash
pip install --user python-xlib ewmh
```

### 问题：无法找到窗口

**原因**：游戏运行在全屏独占模式

**解决方案**：
1. 在游戏设置中切换到"窗口模式"或"无边框窗口"
2. Steam Deck 按 STEAM + X 可以调出虚拟键盘/设置

### 问题：权限被拒绝

**解决方案**：
```bash
# 检查 X11 访问权限
xhost +local:

# 或者使用 --user 安装
pip install --user -r requirements.txt
```

### 问题：性能问题

**优化建议**：
```bash
# 1. 使用 CPU 模式（Steam Deck GPU 较弱）
# 项目已自动配置为 Linux 使用 onnxruntime CPU 版本

# 2. 降低检测频率
# 在设置中调整扫描间隔（如 500ms -> 1000ms）

# 3. 关闭不必要的特效
# 在 GUI 设置中禁用动画和透明效果
```

### 问题：Steam Deck 重启后设置丢失

**原因**：SteamOS 只读文件系统在更新后恢复

**解决方案**：
```bash
# 将项目和依赖安装到用户目录
pip install --user -r requirements.txt

# 或者使用 Flatpak 容器化（高级）
flatpak install flathub org.freedesktop.Platform.ffmpeg-full
```

## 性能基准

在 Steam Deck (AMD Van Gogh APU) 上：

| 功能 | 性能 | 说明 |
|------|------|------|
| 窗口查询 | ~2-3ms | X11 通过 XWayland |
| YOLO 检测 (CPU) | ~100-150ms | 使用 onnxruntime CPU |
| OCR 识别 | ~50-80ms | RapidOCR ONNX |
| 截图 (MSS) | ~10-20ms | mss 库 |

**总体帧率**：约 5-8 FPS（取决于检测复杂度）

## 已知限制

1. **GPU 加速**：Steam Deck 的 AMD GPU 不支持 CUDA，只能使用 CPU 模式
2. **全屏游戏**：全屏独占模式下无法获取窗口信息（需切换到窗口模式）
3. **电池续航**：后台运行会增加功耗，建议插电使用
4. **系统更新**：SteamOS 更新可能重置系统包，需要重新安装 Python

## 推荐配置

在 Steam Deck 上的最佳实践：

1. **游戏设置**：
   - 窗口模式或无边框窗口
   - 分辨率：1280x800（原生分辨率）
   - 刷新率：60Hz

2. **项目设置**：
   - 检测间隔：1000ms（降低 CPU 占用）
   - 禁用动画效果
   - 使用轻量级主题

3. **系统设置**：
   - 性能模式：平衡或性能
   - 风扇曲线：自动或激进
   - 帧率限制：30 或 60 FPS

## 社区支持

遇到 Steam Deck 特定问题？

- GitHub Issues：[提交问题](https://github.com/Duangi/BazaarPlaybook/issues)
- Steam Deck 中文社区
- Reddit: r/SteamDeck

## 贡献

如果你在 Steam Deck 上成功运行并有优化建议，欢迎提交 PR 或 Issue！
