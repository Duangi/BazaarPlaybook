"""
测试 LogAnalyzer 是否使用新的胜负判定逻辑
"""
from services.log_analyzer import LogAnalyzer, get_log_directory
from pathlib import Path

# 初始化
log_dir = get_log_directory()
items_db_path = Path(__file__).parent / "assets" / "json" / "items_db.json"
analyzer = LogAnalyzer(log_dir, str(items_db_path))

# 分析
print("🔍 开始分析日志...")
result = analyzer.analyze()

sessions = result.get("sessions", [])
print(f"\n📊 找到 {len(sessions)} 场游戏\n")
print("=" * 80)

for idx, session in enumerate(sessions, 1):
    pvp_battles = session.pvp_battles
    total = len(pvp_battles)
    wins = sum(1 for b in pvp_battles if b.get('victory', False))
    losses = total - wins
    
    victory_emoji = "🏆" if session.victory else "💀"
    
    print(f"\n{victory_emoji} 游戏 #{idx}")
    print(f"   开始时间: {session.start_time}")
    if hasattr(session, 'start_datetime'):
        print(f"   完整时间: {session.start_datetime}")
    print(f"   最终结果: {'胜利' if session.victory else '失败'}")
    print(f"   存活天数: {session.days} 天")
    print(f"   英雄: {session.hero}")
    print(f"   小局战绩: {wins} 胜 {losses} 负 (共 {total} 场)")
    
    # 显示前5场小局的详细结果
    if pvp_battles:
        print(f"   前5场详情:")
        for i, battle in enumerate(pvp_battles[:5], 1):
            result_icon = "✅" if battle.get('victory', False) else "❌"
            print(f"      小局 #{i}: {result_icon} {'胜利' if battle.get('victory', False) else '失败'} (第{battle.get('day', '?')}天)")

print("\n" + "=" * 80)
print(f"\n✅ 分析完成！共 {len(sessions)} 场游戏")
