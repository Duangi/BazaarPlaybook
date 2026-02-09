"""
测试PVP胜负判断逻辑
"""
from services.log_analyzer import LogAnalyzer, get_log_directory, get_items_db_path

if __name__ == "__main__":
    log_dir = get_log_directory()
    items_db_path = get_items_db_path()
    
    print(f"日志目录: {log_dir}")
    print(f"物品数据库: {items_db_path}")
    print("="*80)
    
    analyzer = LogAnalyzer(log_dir, items_db_path)
    result = analyzer.analyze()
    
    print(f"\n总游戏数: {result['games_count']}")
    
    # 显示所有游戏的PVP战斗记录
    for i, session in enumerate(result['sessions'], 1):
        print(f"\n{'='*80}")
        print(f"游戏 #{i}")
        print(f"{'='*80}")
        print(f"开始时间: {session.start_time}")
        print(f"结束时间: {session.end_time if session.is_finished else '进行中'}")
        print(f"英雄: {session.hero or '未知'}")
        print(f"游戏状态: {'✅ 胜利' if session.victory else '❌ 失败' if session.is_finished else '⏳ 进行中'}")
        print(f"总天数: {session.days}")
        print(f"PVP战斗次数: {len(session.pvp_battles)}")
        
        if session.pvp_battles:
            print(f"\nPVP战斗详情:")
            for j, pvp in enumerate(session.pvp_battles, 1):
                result_emoji = "✅ 胜" if pvp['victory'] else "❌ 败"
                result_text = "胜利" if pvp['victory'] else "失败"
                print(f"  第{pvp['day']}天 - {result_emoji} [{result_text}] ({pvp['start_time']})")
                print(f"    玩家: {len(pvp['player_items'])}件物品")
                print(f"    对手: {len(pvp['opponent_items'])}件物品")
        else:
            print("\n没有PVP战斗记录")
