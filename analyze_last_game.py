"""
分析最近一场游戏的所有小局胜负情况
根据新规则：找到 ReplayState 转换，往上数第3行看是否有 "All exit tasks completed"
"""
import re
from datetime import datetime

def analyze_last_game(log_path):
    """分析最近一场游戏的所有小局"""
    
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到所有 ReplayState 转换的行号
    replay_transitions = []
    for i, line in enumerate(lines):
        if '[AppState] State changed from [PVPCombatState] to [ReplayState]' in line:
            replay_transitions.append(i)
    
    print(f"📊 总共找到 {len(replay_transitions)} 个小局\n")
    print("=" * 80)
    
    results = []
    
    for idx, line_num in enumerate(replay_transitions, 1):
        # 提取时间戳
        time_match = re.search(r'\[(\d{2}:\d{2}:\d{2}\.\d+)\]', lines[line_num])
        timestamp = time_match.group(1) if time_match else "Unknown"
        
        # 检查往上第3行是否有 "All exit tasks completed"
        check_line_num = line_num - 3
        if check_line_num >= 0:
            check_line = lines[check_line_num]
            has_exit_tasks = '[AppState] All exit tasks completed' in check_line
        else:
            has_exit_tasks = False
        
        result = "✅ 胜利" if has_exit_tasks else "❌ 失败"
        
        # 查找对应的 Combat simulation completed 时间
        combat_time = None
        # 从 ReplayState 往前找最近的 Combat simulation completed
        for i in range(line_num - 1, max(0, line_num - 100), -1):
            if '[CombatSimHandler] Combat simulation completed in' in lines[i]:
                time_match = re.search(r'completed in ([\d.]+)s', lines[i])
                if time_match:
                    combat_time = time_match.group(1)
                break
        
        print(f"🎮 小局 #{idx}")
        print(f"   时间: {timestamp}")
        print(f"   结果: {result}")
        if combat_time:
            print(f"   战斗时长: {combat_time}秒")
        
        # 显示判断依据（往上第3行的内容）
        if check_line_num >= 0:
            check_content = lines[check_line_num].strip()
            print(f"   判断依据（往上第3行）: {check_content[:100]}...")
        
        print("-" * 80)
        
        results.append({
            'round': idx,
            'timestamp': timestamp,
            'result': result,
            'combat_time': combat_time,
            'win': has_exit_tasks
        })
    
    # 统计
    wins = sum(1 for r in results if r['win'])
    losses = len(results) - wins
    
    print("\n" + "=" * 80)
    print(f"📈 统计结果:")
    print(f"   总场次: {len(results)}")
    print(f"   胜利: {wins} 场 ({wins/len(results)*100:.1f}%)")
    print(f"   失败: {losses} 场 ({losses/len(results)*100:.1f}%)")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    log_path = "assets/logs/Player.log"
    results = analyze_last_game(log_path)
    
    # 保存结果到文件
    with open("last_game_analysis.txt", "w", encoding="utf-8") as f:
        f.write("最近一场游戏的小局分析结果\n")
        f.write("=" * 80 + "\n\n")
        for r in results:
            f.write(f"小局 #{r['round']}\n")
            f.write(f"  时间: {r['timestamp']}\n")
            f.write(f"  结果: {r['result']}\n")
            if r['combat_time']:
                f.write(f"  战斗时长: {r['combat_time']}秒\n")
            f.write("\n")
        
        wins = sum(1 for r in results if r['win'])
        losses = len(results) - wins
        f.write("-" * 80 + "\n")
        f.write(f"胜利: {wins} 场\n")
        f.write(f"失败: {losses} 场\n")
    
    print("\n✅ 分析结果已保存到 last_game_analysis.txt")
