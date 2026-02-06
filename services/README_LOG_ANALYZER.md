# 游戏日志分析器

## 功能说明

`log_analyzer.py` 用于解析《The Bazaar》游戏的日志文件，追踪游戏状态、物品购买记录和PVP对战信息。

## 主要功能

1. **游戏会话追踪**
   - 自动检测游戏开始/结束
   - 记录游戏胜利/失败状态
   - 统计总游戏局数

2. **天数计算**
   - 从第1天开始
   - 每次PVP结束后进入下一天
   - 如果在第13天PVP后胜利或失败，天数仍然是13天（不会变成14天）

3. **物品追踪**
   - 记录所有购买的物品（instance_id → template_id映射）
   - 区分手牌和仓库位置
   - 显示物品中文名称（从items_db.json加载）

4. **PVP信息**
   - 实时输出PVP全量更新（双方手牌和仓库）
   - 玩家物品显示中文名称
   - 对手物品显示instance_id（无法获取template_id）
   - PVP结束后触发钩子函数（可用于自动截图）

## 使用方法

### 命令行测试

```bash
python services\log_analyzer.py
```

### 作为模块使用

```python
from services.log_analyzer import LogAnalyzer, get_log_directory, get_items_db_path

# 创建分析器
log_dir = get_log_directory()  # 自动选择开发/生产环境日志目录
items_db = get_items_db_path()
analyzer = LogAnalyzer(log_dir, items_db)

# 添加PVP结束回调（用于触发截图等操作）
def on_pvp_end(session, player_items, opponent_items):
    print(f"PVP结束！第{session.days}天")
    print(f"玩家: {len(player_items)}件物品")
    print(f"对手: {len(opponent_items)}件物品")
    # TODO: 在这里触发游戏内截图
    # trigger_screenshot()

analyzer.pvp_end_callbacks.append(on_pvp_end)

# 分析日志
result = analyzer.analyze()

# 获取分析结果
print(f"总游戏数: {result['games_count']}")
print(f"当前天数: {result['current_day']}")  # 0表示没有正在进行的游戏
print(f"当前手牌: {result['current_items']['hand']}")
print(f"当前仓库: {result['current_items']['storage']}")
```

## 日志格式说明

### 关键日志标记

- **游戏开始**: `[GameInstance] Starting new run...`
- **游戏结束**: 
  - 胜利: `State changed to [EndRunVictoryState]`
  - 失败: `State changed to [EndRunDefeatState]`
- **PVP开始**: `State changed to [PVPCombatState]`
- **PVP结束**: `State changed from [PVPCombatState] to [ReplayState]` 然后到 `[ChoiceState]`
- **物品购买**: `[BoardManager] Card Purchased: InstanceId: ... - TemplateId... - Target:... - Section...`
- **全量更新**: `[GameSimHandler] Cards Spawned: [...]`

### 日志位置

- **开发环境**: `D:\Projects\Reborn\assets\logs\`
- **生产环境**: `C:\Users\{用户名}\AppData\LocalLow\Tempo Storm\The Bazaar\`

文件：
- `Player.log`: 当前/最新的游戏日志
- `Player-prev.log`: 上一次的游戏日志

## 输出示例

```
[18:02:34.200] PVP全量更新:
  玩家手牌 (3件):
    槽位2: 草莓 (itm_N2DwG_m)
    槽位3: 方便面 (itm_a589jEX)
    槽位5: 制备工作台 (itm_AjpN3DA)
  对手手牌 (4件):
    槽位2: uP57emT
    槽位3: i7VXVQk
    槽位5: my2gDeW
    槽位6: pkI6St6
  对手仓库 (3件):
    槽位0: kBMnSFO
    槽位1: bYjDdt5
    槽位4: 5mVbkIk

>>> PVP结束钩子触发! 第1天战斗结束 <<<
    玩家物品: 3件
    对手物品: 7件
```

## 数据结构

### GameSession

```python
{
    "start_time": "18:01:54.350",
    "end_time": "18:30:00.000",  # None表示进行中
    "days": 13,  # 当前天数
    "is_finished": True,
    "victory": False,
    "items": {
        "itm_xxx": {
            "template_id": "uuid",
            "target": "PlayerSocket_2",
            "section": "Player"
        }
    },
    "pvp_battles": [
        {
            "start_time": "18:02:00.000",
            "day": 1,
            "player_items": [...],
            "opponent_items": [...]
        }
    ]
}
```

## 注意事项

1. 对手物品的instance_id在PVP中是临时ID，无法映射到template_id
2. 只有玩家自己购买的物品才能获取完整的template_id信息
3. PVP结束后天数会+1，但游戏结束（胜利/失败）时不会再增加
4. 对手的购买记录（ste_、enc_等前缀）与PVP中显示的instance_id不一致
