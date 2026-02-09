"""解析Player.log中的PVP对局胜负记录"""
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

def parse_pvp_log(log_path):
    """解析PVP日志文件，按每局游戏的范围统计PVP战绩
    
    返回:
        runs: 每局游戏的统计 [{"start_line": ..., "end_line": ..., "pvp_battles": [...], "result": "victory/defeat"}]
    """
    
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 关键模式
    run_start_pattern = r'\[GameInstance\] Starting new run\.\.\.'
    pvp_to_replay_pattern = r'\[AppState\] State changed from \[PVPCombatState\] to \[ReplayState\]'
    replay_to_choice_pattern = r'\[AppState\] State changed from \[ReplayState\] to \[ChoiceState\]'
    replay_to_end_pattern = r'\[AppState\] State changed from \[ReplayState\] to \[EndRun(Victory|Defeat)State\]'
    
    # 第一步：找到所有局的起始和结束行
    run_starts = []
    run_ends = []
    
    for idx, line in enumerate(lines):
        if re.search(run_start_pattern, line):
            time_match = re.search(r'\[(\d{2}:\d{2}:\d{2}\.\d{3})\]', line)
            if time_match:
                run_starts.append((idx, time_match.group(1)))
        
        end_match = re.search(replay_to_end_pattern, line)
        if end_match:
            time_match = re.search(r'\[(\d{2}:\d{2}:\d{2}\.\d{3})\]', line)
            result_type = end_match.group(1)  # Victory or Defeat
            if time_match:
                run_ends.append((idx, time_match.group(1), result_type.lower()))
    
    print(f"找到 {len(run_starts)} 局游戏开始标记")
    print(f"找到 {len(run_ends)} 局游戏结束标记\n")
    
    # 第二步：构建每局的范围
    runs = []
    for i, (start_line, start_time) in enumerate(run_starts):
        # 找到对应的结束行（第一个在start_line之后的结束）
        end_line = None
        end_time = None
        result = "unknown"
        
        for end_idx, end_t, end_result in run_ends:
            if end_idx > start_line:
                end_line = end_idx
                end_time = end_t
                result = end_result
                break
        
        # 如果没找到结束，用下一局的开始或文件结尾
        if end_line is None:
            if i + 1 < len(run_starts):
                end_line = run_starts[i + 1][0]
            else:
                end_line = len(lines) - 1
            result = "ongoing"
        
        runs.append({
            "run_id": i + 1,
            "start_line": start_line,
            "end_line": end_line,
            "start_time": start_time,
            "end_time": end_time,
            "result": result,
            "pvp_battles": []
        })
    
    # 第三步：在每局范围内统计PVP
    for run in runs:
        pvp_count = 0
        
        for line_idx in range(run["start_line"], run["end_line"] + 1):
            line = lines[line_idx]
            
            # 找到PVP结束标记
            if re.search(pvp_to_replay_pattern, line):
                time_match = re.search(r'\[(\d{2}:\d{2}:\d{2}\.\d{3})\]', line)
                if not time_match:
                    continue
                
                pvp_time = time_match.group(1)
                
                # 查找后续状态（在接下来的100行内）
                next_state = None
                for next_idx in range(line_idx + 1, min(line_idx + 100, len(lines))):
                    next_line = lines[next_idx]
                    
                    # 如果进入ChoiceState = 赢了
                    if re.search(replay_to_choice_pattern, next_line):
                        next_state = "WIN"
                        break
                    
                    # 如果进入EndRunState = 最后一场
                    end_match = re.search(replay_to_end_pattern, next_line)
                    if end_match:
                        result_type = end_match.group(1)
                        next_state = "WIN" if result_type == "Victory" else "LOSS"
                        break
                
                if next_state:
                    pvp_count += 1
                    run["pvp_battles"].append({
                        "number": pvp_count,
                        "time": pvp_time,
                        "result": next_state
                    })
    
    return runs


def print_summary(runs):
    """打印总结"""
    print("\n" + "=" * 80)
    print("每局详细战绩".center(80))
    print("=" * 80)
    
    for run in runs:
        pvp_wins = sum(1 for b in run['pvp_battles'] if b['result'] == 'WIN')
        pvp_losses = sum(1 for b in run['pvp_battles'] if b['result'] == 'LOSS')
        total_pvp = len(run['pvp_battles'])
        
        result_icon = "🏆" if run['result'] == 'victory' else "💀" if run['result'] == 'defeat' else "⏳"
        
        print(f"\n第 {run['run_id']} 局 {result_icon} {run['result'].upper()}")
        print(f"  时间: {run['start_time']} ~ {run['end_time'] or '进行中'}")
        print(f"  PVP总数: {total_pvp} 场 ({pvp_wins}胜 {pvp_losses}负)")
        
        if total_pvp > 0:
            winrate = pvp_wins / total_pvp * 100
            print(f"  胜率: {winrate:.1f}%")
            print(f"  详细:")
            
            for battle in run['pvp_battles']:
                status = "✅" if battle['result'] == 'WIN' else "❌"
                print(f"    {status} PVP #{battle['number']:02d} [{battle['time']}] {battle['result']}")
        
        print("  " + "-" * 76)
    
    # 总结
    print("\n" + "=" * 80)
    print("总结报告".center(80))
    print("=" * 80)
    
    total_runs = len(runs)
    total_victories = sum(1 for r in runs if r['result'] == 'victory')
    total_defeats = sum(1 for r in runs if r['result'] == 'defeat')
    total_ongoing = sum(1 for r in runs if r['result'] == 'ongoing')
    
    total_pvp_wins = sum(sum(1 for b in r['pvp_battles'] if b['result'] == 'WIN') for r in runs)
    total_pvp_losses = sum(sum(1 for b in r['pvp_battles'] if b['result'] == 'LOSS') for r in runs)
    total_pvp = total_pvp_wins + total_pvp_losses
    
    print(f"\n总局数: {total_runs}")
    print(f"  ├─ 胜利: {total_victories} 局")
    print(f"  ├─ 失败: {total_defeats} 局")
    print(f"  └─ 进行中: {total_ongoing} 局")
    
    print(f"\n总PVP场次: {total_pvp}")
    print(f"  ├─ 胜利: {total_pvp_wins} 场")
    print(f"  ├─ 失败: {total_pvp_losses} 场")
    if total_pvp > 0:
        print(f"  └─ 总胜率: {total_pvp_wins / total_pvp * 100:.1f}%")
    
    print("\n每局战绩汇总:")
    for run in runs:
        pvp_wins = sum(1 for b in run['pvp_battles'] if b['result'] == 'WIN')
        pvp_losses = sum(1 for b in run['pvp_battles'] if b['result'] == 'LOSS')
        total_pvp = len(run['pvp_battles'])
        
        result_icon = "🏆" if run['result'] == 'victory' else "💀" if run['result'] == 'defeat' else "⏳"
        
        if total_pvp > 0:
            wr = pvp_wins / total_pvp * 100
            print(f"  第 {run['run_id']} 局 {result_icon}: {pvp_wins}W-{pvp_losses}L (胜率 {wr:.1f}%, 共{total_pvp}场)")
        else:
            print(f"  第 {run['run_id']} 局 {result_icon}: 无PVP数据")
    
    print("=" * 80)


if __name__ == "__main__":
    log_path = Path(__file__).parent.parent / "assets" / "logs" / "Player.log"
    
    if not log_path.exists():
        print(f"错误: 日志文件不存在: {log_path}")
        exit(1)
    
    print(f"开始解析日志: {log_path}\n")
    runs = parse_pvp_log(log_path)
    print_summary(runs)
