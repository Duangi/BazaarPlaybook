"""
游戏日志分析器
用于解析Player.log和Player-prev.log，追踪游戏状态、物品购买和PVP信息
"""
import re
from typing import List, Dict, Optional
from pathlib import Path


class GameSession:
    """单次游戏会话"""
    def __init__(self, start_time: str, start_line: int, log_file_date: str = None):
        self.start_time = start_time  # 时间戳，格式: HH:MM:SS.mmm
        self.start_line = start_line
        self.log_file_date = log_file_date  # 日志文件日期，格式: YYYY-MM-DD
        self.end_time: Optional[str] = None
        self.end_line: Optional[int] = None
        self.days = 1  # 游戏从第1天开始
        self.is_finished = False
        self.victory = False
        self.hero: Optional[str] = None  # 英雄名称
        # 追踪物品：{instance_id: {"template_id": uuid, "target": socket, "section": area}}
        self.items: Dict[str, Dict] = {}
        # PVP战斗记录
        self.pvp_battles: List[Dict] = []
        
        # ✅ 生成唯一ID：使用日期+时间的hash
        self._generate_unique_id()
    
    def _generate_unique_id(self):
        """生成唯一ID"""
        import hashlib
        # 使用日期+开始时间作为唯一标识
        if self.log_file_date:
            unique_str = f"{self.log_file_date}_{self.start_time}_{self.start_line}"
        else:
            unique_str = f"{self.start_time}_{self.start_line}"
        
        # 生成SHA256 hash的前16位作为ID
        hash_obj = hashlib.sha256(unique_str.encode())
        self.session_id = hash_obj.hexdigest()[:16]
    
    def get_full_start_datetime(self) -> str:
        """获取完整的开始日期时间"""
        if self.log_file_date:
            return f"{self.log_file_date} {self.start_time}"
        return self.start_time
    
    def get_full_end_datetime(self) -> str:
        """获取完整的结束日期时间"""
        if self.log_file_date and self.end_time:
            return f"{self.log_file_date} {self.end_time}"
        return self.end_time or ""
    
    def add_item(self, instance_id: str, template_id: str, target: str, section: str):
        """记录物品购买"""
        self.items[instance_id] = {
            "template_id": template_id,
            "target": target,
            "section": section
        }
    
    def add_pvp_battle(self, start_time: str, player_items: List[Dict], opponent_items: List[Dict], victory: Optional[bool] = None, duration: Optional[str] = None):
        """记录PVP战斗（包含完整的物品信息和胜负）"""
        self.pvp_battles.append({
            "start_time": start_time,
            "day": self.days,  # 记录当前天数
            "player_items": player_items,
            "opponent_items": opponent_items,
            "victory": victory,  # 胜负信息
            "duration": duration  # 战斗耗时（秒）
        })
        # PVP战斗后，如果游戏继续（没有结束），才进入下一天
        # 天数增加在state变回ChoiceState时处理
    
    def finish(self, end_time: str, end_line: int, victory: bool = False):
        """结束游戏会话"""
        self.end_time = end_time
        self.end_line = end_line
        self.is_finished = True
        # 🔥 修复：信任游戏日志的victory状态（EndRunVictoryState/EndRunDefeatState）
        # 游戏规则可能不是简单的10胜，还可能考虑其他因素
        self.victory = victory
        
        # 🔥 DEBUG: 打印胜场数vs最终结果
        win_count = sum(1 for b in self.pvp_battles if b.get('victory', False))
        print(f"[DEBUG] Session结束: 胜场={win_count}, EndRun状态={'Victory' if victory else 'Defeat'}")
    
    def get_current_items(self) -> Dict[str, List[Dict]]:
        """获取当前物品分类"""
        hand = []
        storage = []
        
        for instance_id, item_info in self.items.items():
            target = item_info["target"]
            template_id = item_info["template_id"]
            
            item_data = {
                "instance_id": instance_id,
                "template_id": template_id,
                "target": target
            }
            
            if "PlayerSocket" in target:
                hand.append(item_data)
            elif "PlayerStorageSocket" in target:
                storage.append(item_data)
        
        # 按槽位排序
        hand.sort(key=lambda x: self._extract_socket_num(x["target"]))
        storage.sort(key=lambda x: self._extract_socket_num(x["target"]))
        
        return {
            "hand": hand,
            "storage": storage
        }
    
    @staticmethod
    def _extract_socket_num(target: str) -> int:
        """从Target中提取槽位编号"""
        match = re.search(r'Socket_(\d+)', target)
        return int(match.group(1)) if match else 999


class LogAnalyzer:
    """日志分析器"""
    
    # 正则表达式模式
    TIMESTAMP_PATTERN = r'\[(\d{2}:\d{2}:\d{2}\.\d{3})\]'
    START_RUN_PATTERN = r'\[GameInstance\] Starting new run\.\.\.'
    STATE_CHANGE_PATTERN = r'\[AppState\] State changed from \[.*?\] to \[(.*?)\]'
    CARD_PURCHASED_PATTERN = r'\[BoardManager\] Card Purchased: InstanceId: (.*?) - TemplateId(.*?) - Target:(.*?) - Section(.*?)$'
    CARDS_SPAWNED_PATTERN = r'\[GameSimHandler\] Cards Spawned: (.+)'
    CARDS_DISPOSED_PATTERN = r'\[GameSimHandler\] Cards Disposed: (.+)'
    HERO_PATTERN = r'Hero: \[(\w+)\]'  # 提取英雄名称
    COMBAT_COMPLETED_PATTERN = r'\[CombatSimHandler\] Combat simulation completed in ([\d\.]+)s'  # 战斗耗时
    
    def __init__(self, log_dir: str, items_db_path: Optional[str] = None):
        """
        初始化日志分析器
        
        Args:
            log_dir: 日志文件所在目录
            items_db_path: items_db.json文件路径，用于查询物品名称
        """
        self.log_dir = Path(log_dir)
        self.sessions: List[GameSession] = []
        self.current_session: Optional[GameSession] = None
        self._in_pvp = False
        self._last_pvp_start = None
        self._pvp_player_items = []
        self._pvp_opponent_items = []
        self._pvp_duration = None  # PVP战斗耗时
        
        # ✅ 新增：缓存最近的几行日志，用于往回查找 "All exit tasks completed"
        self._recent_lines = []  # 存储最近5行的内容
        self._recent_lines_max = 5
        
        # ✅ 当前正在解析的日志文件日期
        self._current_log_file_date: Optional[str] = None
        
        # 加载物品数据库
        self.items_db = {}
        if items_db_path:
            import json
            try:
                with open(items_db_path, 'r', encoding='utf-8') as f:
                    items_list = json.load(f)
                    # 将列表转换为字典，以id为key
                    if isinstance(items_list, list):
                        self.items_db = {item['id']: item for item in items_list if 'id' in item}
                    else:
                        self.items_db = items_list
            except Exception as e:
                print(f"Warning: Failed to load items_db.json: {e}")
        
        # PVP结束回调函数列表
        self.pvp_end_callbacks: List = []
        
        # 增量分析的临时状态
        self._incremental_mode = False
        self._incremental_new_sessions = []
        self._incremental_updated_sessions = []
        self._incremental_pvp_completed = False  # 标记是否检测到PVP完成
    
    def analyze_incremental(self, new_lines: List[str]) -> Dict:
        """
        增量分析新增的日志行
        
        Args:
            new_lines: 新增的日志行列表
            
        Returns:
            包含新会话和更新会话的字典
        """
        if not new_lines:
            return {'new_sessions': [], 'updated_sessions': []}
        
        # 标记为增量模式
        self._incremental_mode = True
        self._incremental_new_sessions = []
        self._incremental_updated_sessions = []
        self._incremental_pvp_completed = False
        
        # 记录当前已知的会话和PVP战斗数
        known_session_ids_before = {s.session_id for s in self.sessions}
        pvp_counts_before = {s.session_id: len(s.pvp_battles) for s in self.sessions}
        
        # 确保current_session指向最后一个未完成的会话（同一个对象实例）
        if self.sessions:
            last_session = self.sessions[-1]
            if not last_session.is_finished:
                # 关键修复：直接修改列表中的session，而不是创建新引用
                self.current_session = last_session
                print(f"[LogAnalyzer] 增量分析: current_session设置为 {self.current_session.session_id}, days={self.current_session.days}, pvp_battles={len(self.current_session.pvp_battles)}, id={id(self.current_session)}")
                print(f"[LogAnalyzer] 增量分析: sessions[-1] id={id(self.sessions[-1])}, 是否同一对象={id(self.current_session) == id(self.sessions[-1])}")
            else:
                print(f"[LogAnalyzer] 增量分析: 最后一个session已完成，current_session保持不变")
        else:
            print(f"[LogAnalyzer] 增量分析: sessions为空，current_session保持不变")
        
        try:
            # 逐行处理新增内容
            for line in new_lines:
                try:
                    # 使用现有的_process_line方法处理每一行
                    # line_num设为-1，因为我们不知道确切的行号
                    self._process_line(line, -1)
                    
                    # 检测是否有duration（PVP战斗结束）
                    if 'Combat simulation completed' in line:
                        self._incremental_pvp_completed = True
                        print(f"[LogAnalyzer] 增量分析检测到PVP完成")
                        
                except Exception as e:
                    # 单行错误不应影响整体处理
                    import traceback
                    print(f"[LogAnalyzer] 处理行时出错: {e}")
                    traceback.print_exc()
            
            # 检测新会话
            new_sessions = [s for s in self.sessions if s.session_id not in known_session_ids_before]
            
            # ✅ 合并因游戏重启而分裂的session（在检测更新之前）
            merged_session = None
            if new_sessions:
                prev_count = len(self.sessions)
                self._merge_restart_sessions()
                # 如果sessions数量减少，说明发生了合并
                if len(self.sessions) < prev_count:
                    # 重新计算new_sessions（合并后新session已被删除）
                    new_sessions = [s for s in self.sessions if s.session_id not in known_session_ids_before]
                    # 被合并的session（倒数第一个，即prev_session）需要加入updated列表
                    merged_session = self.sessions[-1] if self.sessions else None
                    print(f"[LogAnalyzer] 合并完成，merged_session: {merged_session.session_id if merged_session else None}")
            
            # 只在检测到PVP完成时才返回更新的会话
            updated_sessions = []
            if self._incremental_pvp_completed:
                for session in self.sessions:
                    if session.session_id in known_session_ids_before:
                        # 检查PVP战斗数是否增加
                        old_pvp_count = pvp_counts_before.get(session.session_id, 0)
                        new_pvp_count = len(session.pvp_battles)
                        print(f"[LogAnalyzer] 检查session {session.session_id}: old_pvp_count={old_pvp_count}, new_pvp_count={new_pvp_count}, session_id={id(session)}")
                        if self.current_session:
                            print(f"[LogAnalyzer]   current_session.pvp_battles={len(self.current_session.pvp_battles)}, current_session_id={id(self.current_session)}")
                        if new_pvp_count > old_pvp_count:
                            updated_sessions.append(session)
                            print(f"[LogAnalyzer] 检测到PVP战斗完成: {session.session_id}, 战斗数 {old_pvp_count} -> {new_pvp_count}, days={session.days}")
            
            # 如果发生了合并，将合并后的session加入updated列表
            if merged_session and merged_session not in updated_sessions:
                updated_sessions.append(merged_session)
                print(f"[LogAnalyzer] 合并后的session加入更新列表: {merged_session.session_id}, days={merged_session.days}, pvp={len(merged_session.pvp_battles)}")
            
            # 保存缓存
            if new_sessions or updated_sessions:
                print(f"[LogAnalyzer] 准备保存缓存: new_sessions={len(new_sessions)}, updated_sessions={len(updated_sessions)}")
                print(f"[LogAnalyzer] 当前self.sessions数量: {len(self.sessions)}")
                if updated_sessions:
                    for s in updated_sessions:
                        print(f"[LogAnalyzer]   更新的session: {s.session_id}, days={s.days}, pvp_battles={len(s.pvp_battles)}")
                self._save_sessions_cache()
            else:
                print(f"[LogAnalyzer] 无需保存缓存（无新会话或更新）")
            
            return {
                'new_sessions': new_sessions,
                'updated_sessions': updated_sessions
            }
            
        finally:
            # 恢复正常模式
            self._incremental_mode = False
            self._incremental_new_sessions = []
            self._incremental_updated_sessions = []
            self._incremental_pvp_completed = False
    
    def _load_cached_sessions(self) -> List[GameSession]:
        """从缓存加载已解析的会话"""
        cache_file = self.log_dir / "sessions_cache.json"
        
        if not cache_file.exists():
            return []
        
        try:
            import json
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            sessions = []
            for session_data in cached_data:
                # 重建 GameSession 对象
                session = GameSession(
                    session_data['start_time'],
                    session_data['start_line'],
                    session_data.get('log_file_date')
                )
                session.session_id = session_data['session_id']
                session.end_time = session_data.get('end_time')
                session.end_line = session_data.get('end_line')
                session.days = session_data.get('days', 1)
                session.is_finished = session_data.get('is_finished', False)
                session.victory = session_data.get('victory', False)
                session.hero = session_data.get('hero')
                session.items = session_data.get('items', {})
                session.pvp_battles = session_data.get('pvp_battles', [])
                
                sessions.append(session)
            
            print(f"[LogAnalyzer] 从缓存加载了 {len(sessions)} 个会话")
            return sessions
        except Exception as e:
            print(f"[LogAnalyzer] 加载缓存失败: {e}")
            return []
    
    def _save_sessions_cache(self):
        """保存会话到缓存"""
        cache_file = self.log_dir / "sessions_cache.json"
        
        try:
            import json
            cached_data = []
            
            print(f"[LogAnalyzer] 开始保存缓存，当前sessions数量: {len(self.sessions)}")
            
            for session in self.sessions:
                print(f"[LogAnalyzer]   保存session: {session.session_id}, days={session.days}, pvp_battles={len(session.pvp_battles)}, is_finished={session.is_finished}")
                session_data = {
                    'session_id': session.session_id,
                    'start_time': session.start_time,
                    'start_line': session.start_line,
                    'log_file_date': session.log_file_date,
                    'end_time': session.end_time,
                    'end_line': session.end_line,
                    'days': session.days,
                    'is_finished': session.is_finished,
                    'victory': session.victory,
                    'hero': session.hero,
                    'items': session.items,
                    'pvp_battles': session.pvp_battles
                }
                cached_data.append(session_data)
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, indent=2, ensure_ascii=False)
            
            print(f"[LogAnalyzer] 已保存 {len(cached_data)} 个会话到缓存")
        except Exception as e:
            print(f"[LogAnalyzer] 保存缓存失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _merge_restart_sessions(self):
        """合并因游戏重启/崩溃而分裂的session
        
        关键逻辑：只要上一个session没有检测到结束标记（is_finished=False），
        新的session就应该合并进去，因为游戏实际上还在继续。
        
        游戏重启后可能已经打了很多PVP，但游戏仍在继续，只有检测到EndRunState才是真正结束。
        """
        if len(self.sessions) < 2:
            return
        
        # 循环处理多次重启的情况
        merged_count = 0
        while len(self.sessions) >= 2:
            prev_session = self.sessions[-2]
            curr_session = self.sessions[-1]
            
            # ✅ 合并条件：前一个session未完成
            # 不要求pvp_battles=0，因为游戏重启后可能已经打了多场PVP
            should_merge = not prev_session.is_finished
            
            if should_merge:
                merged_count += 1
                print(f"[LogAnalyzer] 检测到游戏重启/崩溃，合并session {prev_session.session_id} 和 {curr_session.session_id}")
                print(f"[LogAnalyzer]   prev: hero={prev_session.hero}, days={prev_session.days}, pvp={len(prev_session.pvp_battles)}, finished={prev_session.is_finished}")
                print(f"[LogAnalyzer]   curr: hero={curr_session.hero}, days={curr_session.days}, pvp={len(curr_session.pvp_battles)}, finished={curr_session.is_finished}")
                
                # 将当前session的items合并到前一个
                prev_session.items.update(curr_session.items)
                
                # ✅ 合并PVP战斗记录
                prev_session.pvp_battles.extend(curr_session.pvp_battles)
                
                # ✅ 更新天数（取两者最大值）
                if curr_session.days > prev_session.days:
                    prev_session.days = curr_session.days
                
                # 如果当前session有英雄信息且前一个没有，更新英雄
                if curr_session.hero and not prev_session.hero:
                    prev_session.hero = curr_session.hero
                    print(f"[LogAnalyzer]   更新英雄: {curr_session.hero}")
                
                # ✅ 如果当前session已完成，将完成状态复制到前一个
                if curr_session.is_finished:
                    prev_session.is_finished = True
                    prev_session.victory = curr_session.victory
                    prev_session.end_time = curr_session.end_time
                    prev_session.end_line = curr_session.end_line
                    print(f"[LogAnalyzer]   游戏已结束: victory={curr_session.victory}")
                
                # 删除当前session（因为它实际上是前一个session的继续）
                self.sessions.pop()
                
                # 更新current_session指向合并后的session
                self.current_session = prev_session
                
                print(f"[LogAnalyzer]   合并后: hero={prev_session.hero}, days={prev_session.days}, pvp={len(prev_session.pvp_battles)}, finished={prev_session.is_finished}")
            else:
                # 不满足合并条件，退出循环
                break
        
        if merged_count > 0:
            print(f"[LogAnalyzer] 共合并了 {merged_count} 个重启session，当前sessions数量: {len(self.sessions)}")
    
    def _get_cached_session_ids(self) -> set:
        """获取所有已缓存的会话ID"""
        cached_sessions = self._load_cached_sessions()
        return {s.session_id for s in cached_sessions}
    
    def analyze(self) -> Dict:
        """
        分析日志文件
        
        Returns:
            分析结果，包含游戏数量、当前天数、当前物品等
        """
        # ✅ 暂时禁用缓存，强制重新解析（避免历史错误数据）
        # cached_sessions = self._load_cached_sessions()
        # cached_session_ids = {s.session_id for s in cached_sessions}
        cached_sessions = []
        cached_session_ids = set()
        
        # 按顺序读取日志文件
        log_files = []
        prev_log = self.log_dir / "Player-prev.log"
        curr_log = self.log_dir / "Player.log"
        
        if prev_log.exists():
            log_files.append(prev_log)
        if curr_log.exists():
            log_files.append(curr_log)
        
        if not log_files:
            # 如果没有日志文件，返回缓存的会话
            self.sessions = cached_sessions
            return {
                "games_count": len(cached_sessions),
                "current_day": 0,
                "current_items": {"hand": [], "storage": []},
                "sessions": cached_sessions,
                "error": "No log files found" if not cached_sessions else None
            }
        
        # 解析所有日志文件（只解析新的会话）
        for log_file in log_files:
            self._parse_log_file(log_file)
        
        # ✅ 合并缓存的会话和新解析的会话
        # 过滤掉已经缓存的会话（避免重复）
        new_sessions = [s for s in self.sessions if s.session_id not in cached_session_ids]
        
        # 🔧 清理缓存中的错误finished状态
        # 之前的bug可能导致未真正结束的session被标记为finished
        # 重新设置所有缓存session为未完成，让它们有机会被重新检测或合并
        print(f"[LogAnalyzer] 清理缓存中可能的错误finished状态...")
        for session in cached_sessions:
            if session.is_finished and session.session_id not in cached_session_ids:
                # 这个判断永远不会执行，因为session在cached_sessions里
                pass
        # 实际上我们需要从日志重新检测finished状态
        # 简单方案：如果没有在新解析中发现这个session，说明它在旧日志里
        # 暂时保留缓存的状态，但在合并时会重新处理
        
        # 合并所有会话
        all_sessions = cached_sessions + new_sessions
        
        # ✅ 按日志中的自然顺序排序（不按时间，按出现顺序）
        # 使用start_line作为排序依据，保持日志中的原始顺序
        # 注意：跨文件时，prev.log的会话在前，Player.log的会话在后
        all_sessions.sort(key=lambda s: s.start_line)
        
        self.sessions = all_sessions
        
        # ✅ 合并因游戏重启而分裂的session
        self._merge_restart_sessions()
        
        # ✅ 保存到缓存（包括新解析的会话）
        if new_sessions:
            print(f"[LogAnalyzer] 发现 {len(new_sessions)} 个新会话")
            self._save_sessions_cache()
        
        # ========== 调试输出：列出所有session的详细信息 ==========
        print(f"\n{'='*80}")
        print(f"[LogAnalyzer] 分析完成，当前共有 {len(self.sessions)} 个session:")
        for i, s in enumerate(self.sessions, 1):
            # 计算胜负
            wins = sum(1 for b in s.pvp_battles if b.get('victory', False))
            losses = sum(1 for b in s.pvp_battles if b.get('victory') is False and b.get('victory') is not None)
            pvp_result = f"{wins}胜{losses}负" if s.pvp_battles else "无PVP"
            status = "✅已完成" if s.is_finished else "🔴进行中"
            victory_text = "胜利" if s.victory else "失败" if s.is_finished else "进行中"
            print(f"  [{i}] {s.session_id[:8]}... | {s.hero or '未知'} | 第{s.days}天 | {pvp_result} | {status} | {victory_text} | {s.start_time}")
        print(f"{'='*80}\n")
        # ========================================================
        
        # 返回分析结果
        total_games = len(self.sessions)
        current_day = 0
        current_items = {"hand": [], "storage": []}
        
        # 获取最后一个未完成的会话（当前游戏）
        if self.sessions:
            last_session = self.sessions[-1]
            if not last_session.is_finished:
                current_day = last_session.days
                current_items = last_session.get_current_items()
        
        return {
            "games_count": total_games,
            "current_day": current_day,
            "current_items": current_items,
            "sessions": self.sessions
        }
    
    def _parse_log_file(self, log_file: Path):
        """解析单个日志文件"""
        try:
            # ✅ 从文件修改时间推断日期
            import os
            from datetime import datetime
            
            file_mtime = os.path.getmtime(log_file)
            file_date = datetime.fromtimestamp(file_mtime)
            self._current_log_file_date = file_date.strftime("%Y-%m-%d")
            
            print(f"[LogAnalyzer] 解析日志文件: {log_file.name}, 日期: {self._current_log_file_date}")
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        self._process_line(line, line_num)
                    except Exception as e:
                        print(f"Error processing line {line_num} in {log_file.name}: {e}")
                        print(f"Line content: {line[:100]}")
                        import traceback
                        traceback.print_exc()
        except Exception as e:
            print(f"Error parsing {log_file}: {e}")
    
    def _process_line(self, line: str, line_num: int):
        """处理单行日志"""
        # ✅ 将当前行加入缓存（保留最近5行）
        self._recent_lines.append(line)
        if len(self._recent_lines) > self._recent_lines_max:
            self._recent_lines.pop(0)
        
        # 提取时间戳
        timestamp_match = re.search(self.TIMESTAMP_PATTERN, line)
        if not timestamp_match:
            return
        
        timestamp = timestamp_match.group(1)
        
        # 检测游戏开始
        if re.search(self.START_RUN_PATTERN, line):
            self._handle_game_start(timestamp, line_num)
            return
        
        # 如果没有活动会话，跳过
        if not self.current_session:
            return
        
        # 检测英雄选择（在会话存在时）
        hero_match = re.search(self.HERO_PATTERN, line)
        if hero_match and not self.current_session.hero:
            self.current_session.hero = hero_match.group(1)
            return
        
        # 检测状态变化
        state_match = re.search(self.STATE_CHANGE_PATTERN, line)
        if state_match:
            new_state = state_match.group(1)
            self._handle_state_change(new_state, timestamp, line_num, line)
            return
        
        # 检测物品购买
        purchase_match = re.search(self.CARD_PURCHASED_PATTERN, line)
        if purchase_match:
            instance_id = purchase_match.group(1)
            template_id = purchase_match.group(2)
            target = purchase_match.group(3)
            section = purchase_match.group(4)
            
            # 追踪所有物品购买（包括对手的，用于后续映射）
            if "Player" in target and not instance_id.startswith("pvp_"):
                self.current_session.add_item(instance_id, template_id, target, section)
            # 记录对手物品的template映射
            elif "Opponent" in target:
                # 临时存储对手物品映射
                if not hasattr(self, '_opponent_template_map'):
                    self._opponent_template_map = {}
                self._opponent_template_map[instance_id] = template_id
            return
        
        # 检测Cards Disposed（PVP前的清理）
        disposed_match = re.search(self.CARDS_DISPOSED_PATTERN, line)
        if disposed_match and self._in_pvp:
            # PVP即将开始的清理阶段
            pass
        
        # 检测Combat simulation completed（战斗耗时）
        # 🔥 修复：移除 _in_pvp 条件，因为这一行可能出现在状态转换之前
        combat_completed_match = re.search(self.COMBAT_COMPLETED_PATTERN, line)
        if combat_completed_match:
            duration = combat_completed_match.group(1)
            # ✅ 确保duration是浮点数格式
            try:
                duration = float(duration)
                self._pvp_duration = duration
                print(f"[DEBUG] 捕获战斗耗时: {duration}s")
            except ValueError:
                print(f"[DEBUG] 无法解析duration: {duration}")
        
        # 检测Cards Spawned（全量更新）
        spawned_match = re.search(self.CARDS_SPAWNED_PATTERN, line)
        if spawned_match:
            cards_str = spawned_match.group(1)
            self._handle_cards_spawned(cards_str, timestamp, line)
    
    def _handle_game_start(self, timestamp: str, line_num: int):
        """处理游戏开始"""
        # ✅ 不再自动finish上一个session
        # 如果游戏崩溃/重启，上一个session应该保持未完成状态，等待合并逻辑处理
        # 只有检测到EndRunState时才真正finish
        
        # if self.current_session and not self.current_session.is_finished:
        #     # 可能是崩溃或退出，标记为失败
        #     self.current_session.finish(timestamp, line_num, victory=False)
        
        # 创建新会话，传入日期信息
        self.current_session = GameSession(timestamp, line_num, self._current_log_file_date)
        self.sessions.append(self.current_session)
        
        print(f"[LogAnalyzer] 新游戏开始: {self.current_session.get_full_start_datetime()} (ID: {self.current_session.session_id})")
    
    def _handle_cards_spawned(self, cards_str: str, timestamp: str, line: str):
        """处理Cards Spawned事件（全量更新）"""
        # 解析所有卡牌
        # 格式: [instance_id [Owner] [Location] [Socket] [Size] |
        card_pattern = r'\[(\w+) \[(Player|Opponent)\] \[(\w+)\] \[Socket_(\d+)\]'
        cards = re.findall(card_pattern, cards_str)
        
        # 检查是否有Player的卡牌
        has_player = any(owner == "Player" for _, owner, _, _ in cards)
        has_opponent = any(owner == "Opponent" for _, owner, _, _ in cards)
        
        if has_player:
            # PVP中的玩家物品全量更新（包括战斗结束后的ReplayState）
            if self._in_pvp or hasattr(self, '_pvp_player_items'):
                # 收集玩家物品
                player_items = []
                for instance_id, owner, location, socket in cards:
                    if owner == "Player":
                        # 确保item_info是字典
                        item_info = self.current_session.items.get(instance_id, {})
                        if isinstance(item_info, dict):
                            template_id = item_info.get("template_id", "unknown")
                        else:
                            template_id = "unknown"
                        
                        player_items.append({
                            "instance_id": instance_id,
                            "template_id": template_id,
                            "location": location,
                            "socket": socket
                        })
                
                # 如果是PVP战斗中，更新临时列表
                if self._in_pvp:
                    self._pvp_player_items = player_items
                # 如果是战斗结束后，也更新（用于最终显示）
                elif hasattr(self, '_pvp_player_items') and player_items:
                    self._pvp_player_items = player_items
        
        if has_opponent:
            # PVP中的对手物品全量更新（包括战斗结束后的ReplayState）
            if self._in_pvp or hasattr(self, '_pvp_opponent_items'):
                # 收集对手物品
                opponent_items = []
                opponent_template_map = getattr(self, '_opponent_template_map', {})
                
                for instance_id, owner, location, socket in cards:
                    if owner == "Opponent":
                        template_id = opponent_template_map.get(instance_id, "unknown")
                        opponent_items.append({
                            "instance_id": instance_id,
                            "template_id": template_id,
                            "location": location,
                            "socket": socket
                        })
                
                # 更新临时列表
                self._pvp_opponent_items = opponent_items
                
                # 输出PVP全量更新（对手物品更新后输出）
                self._log_pvp_full_update(timestamp)
    
    def _log_pvp_full_update(self, timestamp: str):
        """输出PVP全量更新信息到日志"""
        print(f"\n[{timestamp}] PVP全量更新:")
        
        # 输出玩家物品
        player_hand = [i for i in self._pvp_player_items if i['location'] == 'Hand']
        print(f"  玩家手牌 ({len(player_hand)}件):")
        for item in sorted(player_hand, key=lambda x: int(x['socket'])):
            item_name = self._get_item_name(item['template_id'])
            print(f"    槽位{item['socket']}: {item_name} ({item['instance_id']})")
        
        player_stash = [i for i in self._pvp_player_items if i['location'] == 'Stash']
        if player_stash:
            print(f"  玩家仓库 ({len(player_stash)}件):")
            for item in sorted(player_stash, key=lambda x: int(x['socket'])):
                item_name = self._get_item_name(item['template_id'])
                print(f"    槽位{item['socket']}: {item_name} ({item['instance_id']})")
        
        # 输出对手物品
        opponent_hand = [i for i in self._pvp_opponent_items if i['location'] == 'Hand']
        print(f"  对手手牌 ({len(opponent_hand)}件):")
        for item in sorted(opponent_hand, key=lambda x: int(x['socket'])):
            # 对手物品无法获取template_id，只显示instance_id
            print(f"    槽位{item['socket']}: {item['instance_id']}")
        
        opponent_stash = [i for i in self._pvp_opponent_items if i['location'] == 'Stash']
        if opponent_stash:
            print(f"  对手仓库 ({len(opponent_stash)}件):")
            for item in sorted(opponent_stash, key=lambda x: int(x['socket'])):
                print(f"    槽位{item['socket']}: {item['instance_id']}")
    
    def _get_item_name(self, template_id: str) -> str:
        """根据template_id获取物品中文名称"""
        if template_id == "unknown":
            return "未知物品"
        
        item_data = self.items_db.get(template_id, {})
        # 优先使用name_cn，其次name_en，最后使用id前8位
        name_cn = item_data.get("name_cn")
        if name_cn:
            return name_cn
        name_en = item_data.get("name_en")
        if name_en:
            return name_en
        return template_id[:8] if len(template_id) > 8 else template_id
    
    def _handle_state_change(self, new_state: str, timestamp: str, line_num: int, line: str):
        """处理状态变化"""
        if not self.current_session:
            return
        
        # 检测PVP开始
        if new_state == "PVPCombatState":
            self._in_pvp = True
            self._last_pvp_start = timestamp
            self._pvp_player_items = []
            self._pvp_opponent_items = []
            self._pvp_duration = None  # 🔥 重置duration，防止旧数据污染
            if not hasattr(self, '_opponent_template_map'):
                self._opponent_template_map = {}
        
        # 检测PVP结束进入ReplayState（战斗回放）
        elif new_state == "ReplayState" and self._in_pvp:
            # ✅ 新判断逻辑：往上数第3行，看是否有 "All exit tasks completed"
            victory = self._check_pvp_victory_from_recent_lines()
            
            print(f"[DEBUG] PVP结束 → ReplayState，胜负判断: {'胜利' if victory else '失败'}")
            print(f"[DEBUG] PVP耗时: {self._pvp_duration}")
            
            # 记录战斗信息
            if self._pvp_player_items or self._pvp_opponent_items:
                self.current_session.add_pvp_battle(
                    self._last_pvp_start or timestamp,
                    self._pvp_player_items.copy(),
                    self._pvp_opponent_items.copy(),
                    victory=victory,
                    duration=self._pvp_duration
                )
                print(f"[DEBUG] 已添加PVP战斗记录，duration={self._pvp_duration}")
                
                # 触发PVP结束回调
                for callback in self.pvp_end_callbacks:
                    try:
                        callback(self.current_session, self._pvp_player_items, self._pvp_opponent_items)
                    except Exception as e:
                        print(f"PVP回调函数执行失败: {e}")
                
                # 每场PVP战斗后，天数都+1（进入下一天），不管输赢
                self.current_session.days += 1
                print(f"[DEBUG] PVP战斗后，天数更新: {self.current_session.days - 1} -> {self.current_session.days}")
            
            # 标记PVP已结束，清理数据
            self._in_pvp = False
            self._pvp_just_ended = True
            self._pvp_player_items = []
            self._pvp_opponent_items = []
            self._pvp_duration = None
        
        # 检测从ReplayState到ChoiceState或EncounterState（仅用于清理状态）
        elif (new_state == "ChoiceState" or new_state == "EncounterState") and getattr(self, '_pvp_just_ended', False):
            # 清理PVP相关状态标记
            self._pvp_just_ended = False
        
        # 检测游戏胜利结束
        elif new_state == "EndRunVictoryState":
            # 清理PVP状态标记
            self._pvp_just_ended = False
            
            self.current_session.finish(timestamp, line_num, victory=True)
            self.current_session = None
        
        # 检测游戏失败结束
        elif new_state == "EndRunDefeatState":
            # 清理PVP状态标记
            self._pvp_just_ended = False
            
            self.current_session.finish(timestamp, line_num, victory=False)
            self.current_session = None
    
    def _check_pvp_victory_from_recent_lines(self) -> bool:
        """
        检查最近的日志行，判断PVP胜负
        规则：从当前行往上数第3行，如果有 "All exit tasks completed" 就是赢了
        
        Returns:
            True = 胜利，False = 失败
        """
        # 最近的行数应该 >= 4（当前行 + 往上3行）
        if len(self._recent_lines) < 4:
            print(f"[DEBUG] 缓存行数不足：{len(self._recent_lines)}，默认判断为失败")
            return False
        
        # _recent_lines[-1] = 当前行（ReplayState转换）
        # _recent_lines[-2] = 往上1行
        # _recent_lines[-3] = 往上2行
        # _recent_lines[-4] = 往上3行 ← 我们要检查这一行
        third_line_up = self._recent_lines[-4]
        
        # 检查是否包含 "All exit tasks completed"
        has_exit_tasks = "All exit tasks completed" in third_line_up
        
        print(f"[DEBUG] 往上第3行内容: {third_line_up.strip()}")
        print(f"[DEBUG] 是否包含 'All exit tasks completed': {has_exit_tasks}")
        
        return has_exit_tasks


def get_log_directory() -> str:
    """
    获取日志目录路径
    ✅ 固定使用生产环境路径
    
    Returns:
        日志目录路径
    """
    # ✅ 固定路径
    prod_log_dir = Path(r"C:\Users\Admin\AppData\LocalLow\Tempo Storm\The Bazaar")
    return str(prod_log_dir)


def get_items_db_path() -> str:
    """获取items_db.json路径"""
    items_db = Path(__file__).parent.parent / "assets" / "json" / "items_db.json"
    return str(items_db) if items_db.exists() else None


if __name__ == "__main__":
    # 测试代码
    log_dir = get_log_directory()
    items_db_path = get_items_db_path()
    print(f"Log directory: {log_dir}")
    print(f"Items DB: {items_db_path}")
    
    # 定义PVP结束回调函数（用于触发截图）
    def on_pvp_end(session, player_items, opponent_items):
        print(f"\n>>> PVP结束钩子触发! 第{session.days}天战斗结束 <<<")
        print(f"    玩家物品: {len(player_items)}件")
        print(f"    对手物品: {len(opponent_items)}件")
        # TODO: 在这里触发游戏内截图
        # 例如: trigger_screenshot()
    
    analyzer = LogAnalyzer(log_dir, items_db_path)
    analyzer.pvp_end_callbacks.append(on_pvp_end)
    result = analyzer.analyze()
    
    print("\n" + "="*60)
    print("游戏统计:")
    print("="*60)
    print(f"总游戏数: {result['games_count']}")
    print(f"当前天数: {result['current_day']} (0表示没有正在进行的游戏)")
    
    if result['current_day'] > 0:
        print("\n当前手牌:")
        for item in result['current_items']['hand']:
            print(f"  - {item['instance_id']}: {item['template_id']}")
        print("\n当前仓库:")
        for item in result['current_items']['storage']:
            print(f"  - {item['instance_id']}: {item['template_id']}")
    
    # 显示最后一场游戏的详细信息
    if result['sessions']:
        last_session = result['sessions'][-1]
        print("\n" + "="*60)
        print("最后一场游戏详情:")
        print("="*60)
        print(f"开始时间: {last_session.start_time}")
        print(f"结束时间: {last_session.end_time if last_session.is_finished else '进行中'}")
        print(f"游戏状态: {'胜利' if last_session.victory else '失败' if last_session.is_finished else '进行中'}")
        print(f"总天数: {last_session.days}")
        print(f"PVP战斗次数: {len(last_session.pvp_battles)}")
        
        print(f"\n物品购买记录 (共{len(last_session.items)}件):")
        for instance_id, item_info in last_session.items.items():
            location = "手牌" if "PlayerSocket" in item_info['target'] else "仓库" if "PlayerStorageSocket" in item_info['target'] else "未知"
            print(f"  - {instance_id}: {item_info['template_id'][:8]}... ({location})")
        
        if last_session.pvp_battles:
            print("\nPVP战斗记录:")
            for pvp in last_session.pvp_battles:
                day = pvp['day']
                print(f"  第{day}天 ({pvp['start_time']}):")
                print(f"    玩家: {len(pvp['player_items'])}件物品")
                print(f"    对手: {len(pvp['opponent_items'])}件物品")
        
        # 显示最终物品状态
        final_items = last_session.get_current_items()
        print(f"\n最终手牌 ({len(final_items['hand'])}件):")
        for item in final_items['hand']:
            socket_num = re.search(r'Socket_(\d+)', item['target'])
            socket = socket_num.group(1) if socket_num else '?'
            print(f"  槽位{socket}: {item['instance_id']} ({item['template_id'][:8]}...)")
        
        print(f"\n最终仓库 ({len(final_items['storage'])}件):")
        for item in final_items['storage']:
            socket_num = re.search(r'Socket_(\d+)', item['target'])
            socket = socket_num.group(1) if socket_num else '?'
            print(f"  槽位{socket}: {item['instance_id']} ({item['template_id'][:8]}...)")
