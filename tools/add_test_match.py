"""
添加测试用历史战绩数据
"""
import json
from pathlib import Path
from datetime import datetime
import uuid

# 初始化路径
user_data_dir = Path(__file__).parent.parent / "user_data"
match_history_path = user_data_dir / "match_history.json"

# 创建测试数据
test_match = {
    "match_id": str(uuid.uuid4()),
    "hero": "Vanessa",
    "start_time": "2024-01-15 14:30:00",
    "end_time": "2024-01-15 15:45:00",
    "days": 13,
    "victory": True,
    "is_finished": True,
    "created_at": datetime.now().isoformat(),
    "pvp_battles": []
}

# 创建13天的PVP数据
item_templates = [
    "012658f4-b289-4f10-917c-a9a1f3f9ca03",  # 草莓
    "0229faa7-2eec-4746-9134-ade4f3aebe45",  # 制备工作台
    "027ef534-d047-4e18-8496-d9fd4773e15d",  # 蛋糕糊
    "004cb876-1ed2-4a4b-88d4-475cea76a03d",  # 另一个物品
    "00e3a7ff-af5e-47ce-a2c0-2d4ec31ac7d7",  # 另一个物品
    "014d9c98-e823-443c-98a3-6367ab81c956",  # 另一个物品
    "01f6e150-ba23-429c-a43b-2508f63fc798",  # 另一个物品
    "020a0ec0-21e6-41af-899f-063573ba9ca5",  # 另一个物品
]

for day in range(1, 14):
    battle = {
        "day": day,
        "start_time": f"2024-01-15 14:{30+day:02d}:00",
        "victory": day % 2 == 1,  # 奇数天胜利，偶数天失败
        "player_items": [
            {
                "instance_id": f"itm_test_{day}_1",
                "template_id": item_templates[(day - 1) % len(item_templates)],
                "location": "PlayerSocket",
                "socket": 0
            },
            {
                "instance_id": f"itm_test_{day}_2",
                "template_id": item_templates[(day) % len(item_templates)],
                "location": "PlayerSocket",
                "socket": 1
            },
            {
                "instance_id": f"itm_test_{day}_3",
                "template_id": item_templates[(day + 1) % len(item_templates)],
                "location": "PlayerSocket",
                "socket": 2
            }
        ],
        "opponent_items": [
            {
                "instance_id": f"itm_opp_{day}_1",
                "template_id": item_templates[(day + 2) % len(item_templates)],
                "location": "OpponentSocket",
                "socket": 0
            }
        ],
        "screenshot": str(Path(__file__).parent.parent / "tests" / "assets" / "Jules1.png")
    }
    test_match["pvp_battles"].append(battle)

# 读取现有数据
try:
    with open(match_history_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception:
    data = {"matches": []}

# 添加测试数据
data["matches"].append(test_match)

# 保存
with open(match_history_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✓ 已添加测试战绩数据到 {match_history_path}")
print(f"  对局ID: {test_match['match_id']}")
print(f"  英雄: {test_match['hero']}")
print(f"  天数: {test_match['days']}")
print(f"  结果: {'胜利' if test_match['victory'] else '失败'}")
