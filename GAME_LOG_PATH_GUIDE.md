# 游戏日志路径跨平台适配说明

## 概述

《The Bazaar》游戏日志文件 (`Player.log`) 在不同操作系统上存储在不同位置。本项目通过平台适配器自动识别并获取正确的日志路径。

## 日志路径位置

### Windows
```
%USERPROFILE%\AppData\LocalLow\Tempo Storm\The Bazaar\Player.log
```

示例：
```
C:\Users\YourName\AppData\LocalLow\Tempo Storm\The Bazaar\Player.log
```

### macOS
```
~/Library/Logs/Tempo Storm/The Bazaar/Player.log
```

示例：
```
/Users/YourName/Library/Logs/Tempo Storm/The Bazaar/Player.log
```

### Linux（原生运行）
```
~/.config/unity3d/Tempo Storm/The Bazaar/Player.log
```
或
```
~/.local/share/unity3d/Tempo Storm/The Bazaar/Player.log
```

### Linux（通过 Steam Proton 运行）
```
~/.steam/steam/steamapps/compatdata/<APP_ID>/pfx/drive_c/users/steamuser/AppData/LocalLow/Tempo Storm/The Bazaar/Player.log
```

其中 `<APP_ID>` 是游戏的 Steam App ID。

### Steam Deck

**游戏模式（Gamescope + XWayland）**：
```
/home/deck/.steam/steam/steamapps/compatdata/<APP_ID>/pfx/drive_c/users/steamuser/AppData/LocalLow/Tempo Storm/The Bazaar/Player.log
```

**桌面模式（KDE Plasma）**：
与 Linux Proton 路径相同。

**Flatpak Steam**：
```
~/.var/app/com.valvesoftware.Steam/.steam/steam/steamapps/compatdata/<APP_ID>/pfx/drive_c/users/steamuser/AppData/LocalLow/Tempo Storm/The Bazaar/Player.log
```

## 实现架构

### 接口定义 (`platforms/interfaces/game_log.py`)

```python
class GameLogPathProvider(ABC):
    @abstractmethod
    def get_log_directory(self) -> Optional[Path]:
        """获取游戏日志目录"""
        pass
    
    @abstractmethod
    def get_player_log_path(self) -> Optional[Path]:
        """获取 Player.log 完整路径"""
        pass
    
    @abstractmethod
    def get_player_prev_log_path(self) -> Optional[Path]:
        """获取 Player-prev.log 完整路径"""
        pass
```

### 平台实现

#### Windows (`platforms/windows/game_log.py`)
- 读取 `%USERPROFILE%` 环境变量
- 拼接 `AppData\LocalLow\Tempo Storm\The Bazaar`

#### macOS (`platforms/macos/game_log.py`)
- 读取 `$HOME` 环境变量
- 拼接 `Library/Logs/Tempo Storm/The Bazaar`

#### Linux (`platforms/linux/game_log.py`)
自动检测多个可能的位置（按优先级）：

1. Unity 标准路径：`~/.config/unity3d/Tempo Storm/The Bazaar`
2. Unity 备选路径：`~/.local/share/unity3d/Tempo Storm/The Bazaar`
3. Steam Proton 路径：遍历 `~/.steam/steam/steamapps/compatdata/*/pfx/...`
4. Flatpak Steam 路径：`~/.var/app/com.valvesoftware.Steam/.steam/...`

**智能检测**：
- 自动遍历所有 compatdata 目录，找到包含游戏日志的路径
- 优先使用已存在的目录
- 如果都不存在，使用默认 Unity 路径并提示用户

### 适配器分发 (`platforms/adapter.py`)

```python
@staticmethod
def get_game_log_path_provider() -> GameLogPathProvider:
    if sys.platform == "win32":
        return WindowsGameLogPathProvider()
    elif sys.platform == "darwin":
        return MacOSGameLogPathProvider()
    elif sys.platform.startswith("linux"):
        return LinuxGameLogPathProvider()
    else:
        return NullGameLogPathProvider()
```

## 使用方式

### 在代码中使用

```python
from platforms.adapter import PlatformAdapter

# 获取路径提供者
provider = PlatformAdapter.get_game_log_path_provider()

# 获取日志目录
log_dir = provider.get_log_directory()
if log_dir and log_dir.exists():
    print(f"日志目录: {log_dir}")

# 获取 Player.log 路径
player_log = provider.get_player_log_path()
if player_log and player_log.exists():
    print(f"Player.log: {player_log}")
    with open(player_log, 'r') as f:
        content = f.read()
```

### LogWatcher 自动集成

`services/log_watcher.py` 已自动使用平台适配器：

```python
from platforms.adapter import PlatformAdapter

log_path_provider = PlatformAdapter.get_game_log_path_provider()
self.log_dir = log_path_provider.get_log_directory()
self.player_log = log_path_provider.get_player_log_path()
```

## 测试

运行测试脚本验证路径检测：

```bash
python test_game_log_path.py
```

输出示例（macOS）：
```
🎮 游戏日志路径跨平台测试

============================================================
测试游戏日志路径检测
============================================================
当前平台: darwin
路径提供者类型: MacOSGameLogPathProvider
日志目录: /Users/YourName/Library/Logs/Tempo Storm/The Bazaar
✅ 日志目录存在
目录内文件数: 2
  - Player.log (1,234,567 bytes)
  - Player-prev.log (987,654 bytes)
Player.log 路径: /Users/YourName/Library/Logs/Tempo Storm/The Bazaar/Player.log
✅ Player.log 存在
文件大小: 1,234,567 bytes (1.18 MB)
```

## 故障排查

### 问题：找不到日志文件

**可能原因**：
1. 游戏尚未运行过
2. 使用了自定义安装路径
3. 通过 Wine/Proton 运行但路径检测失败

**解决方案**：

**Windows**：
```bash
# 手动检查路径
dir "%USERPROFILE%\AppData\LocalLow\Tempo Storm\The Bazaar"
```

**macOS**：
```bash
# 手动检查路径
ls -la ~/Library/Logs/Tempo\ Storm/The\ Bazaar/
```

**Linux**：
```bash
# 检查 Unity 标准路径
ls -la ~/.config/unity3d/Tempo\ Storm/The\ Bazaar/

# 检查 Steam Proton 路径
find ~/.steam/steam/steamapps/compatdata -name "Player.log" -path "*/Tempo Storm/*"

# 检查 Flatpak Steam
find ~/.var/app/com.valvesoftware.Steam -name "Player.log" -path "*/Tempo Storm/*"
```

### 问题：Steam Deck 找不到日志

**解决方案**：

1. 确认游戏已运行过一次
2. 在桌面模式打开终端（Konsole）：
```bash
# 查找游戏日志
find ~/.steam -name "Player.log" -path "*/Tempo Storm/*" 2>/dev/null

# 列出所有 compatdata 目录
ls ~/.steam/steam/steamapps/compatdata/
```

3. 如果找到日志，记下 App ID，可以手动设置：
```python
provider = PlatformAdapter.get_game_log_path_provider()
if isinstance(provider, LinuxGameLogPathProvider):
    provider.set_steam_app_id("YOUR_APP_ID")
```

### 问题：权限被拒绝

**Linux/Steam Deck**：
```bash
# 检查文件权限
ls -l ~/.config/unity3d/Tempo\ Storm/The\ Bazaar/Player.log

# 修复权限
chmod 644 ~/.config/unity3d/Tempo\ Storm/The\ Bazaar/Player.log
```

## 日志文件格式

### Player.log
当前游戏会话的日志文件，包含：
- 游戏启动信息
- 关卡（Day）进度
- PVP 对战记录
- 物品获取记录
- 错误和调试信息

### Player-prev.log
上一次游戏会话的日志文件（日志轮转后生成）。

## 性能注意事项

### 文件大小
- Player.log 通常在 1-10 MB
- 长时间游戏会话可能超过 50 MB
- 建议定期清理旧日志（游戏会自动轮转）

### 读取策略
项目使用增量读取策略：
- 记录上次读取位置
- 仅读取新增内容
- 避免重复解析整个文件

## 相关文件

- `platforms/interfaces/game_log.py` - 日志路径接口定义
- `platforms/windows/game_log.py` - Windows 实现
- `platforms/macos/game_log.py` - macOS 实现
- `platforms/linux/game_log.py` - Linux 实现（包括 Steam Deck）
- `platforms/adapter.py` - 平台分发器
- `services/log_watcher.py` - 日志监控服务（已集成）
- `services/log_analyzer.py` - 日志分析器
- `test_game_log_path.py` - 测试脚本

## 未来扩展

- [ ] 支持自定义日志路径配置
- [ ] 自动检测游戏 Steam App ID
- [ ] 支持多个 Steam 库路径
- [ ] 云同步日志支持（Steam Cloud）
- [ ] 日志压缩和归档功能
