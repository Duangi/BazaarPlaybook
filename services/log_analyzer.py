"""
游戏日志分析器
用于解析Player.log和Player-prev.log，追踪游戏状态、物品购买和PVP信息
"""
import re
from typing import List, Dict, Optional
from pathlib import Path


class GameSession:
    """单次游戏会话"""
    def __init__(self, start_time: str, start_line: int):
        self.start_time = start_time
        self.start_line = start_line
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
    
    def add_item(self, instance_id: str, template_id: str, target: str, section: str):
        """记录物品购买"""
        self.items[instance_id] = {
            "template_id": template_id,
            "target": target,
            "section": section
        }
    
    def add_pvp_battle(self, start_time: str, player_items: List[Dict], opponent_items: List[Dict], victory: Optional[bool] = None):
        """记录PVP战斗（包含完整的物品信息和胜负）"""
        self.pvp_battles.append({
            "start_time": start_time,
            "day": self.days,  # 记录当前天数
            "player_items": player_items,
            "opponent_items": opponent_items,
            "victory": victory  # 胜负信息
        })
        # PVP战斗后，如果游戏继续（没有结束），才进入下一天
        # 天数增加在state变回ChoiceState时处理
    
    def finish(self, end_time: str, end_line: int, victory: bool = False):
        """结束游戏会话"""
        self.end_time = end_time
        self.end_line = end_line
        self.is_finished = True
        self.victory = victory
    
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
    
    def analyze(self) -> Dict:
        """
        分析日志文件
        
        Returns:
            分析结果，包含游戏数量、当前天数、当前物品等
        """
        # 按顺序读取日志文件
        log_files = []
        prev_log = self.log_dir / "Player-prev.log"
        curr_log = self.log_dir / "Player.log"
        
        if prev_log.exists():
            log_files.append(prev_log)
        if curr_log.exists():
            log_files.append(curr_log)
        
        if not log_files:
            return {
                "games_count": 0,
                "current_day": 0,
                "current_items": {"hand": [], "storage": []},
                "error": "No log files found"
            }
        
        # 解析所有日志文件
        for log_file in log_files:
            self._parse_log_file(log_file)
        
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
        
        # 检测Cards Spawned（全量更新）
        spawned_match = re.search(self.CARDS_SPAWNED_PATTERN, line)
        if spawned_match:
            cards_str = spawned_match.group(1)
            self._handle_cards_spawned(cards_str, timestamp, line)
    
    def _handle_game_start(self, timestamp: str, line_num: int):
        """处理游戏开始"""
        # 如果有未完成的会话，标记为未完成结束
        if self.current_session and not self.current_session.is_finished:
            # 可能是崩溃或退出，标记为失败
            self.current_session.finish(timestamp, line_num, victory=False)
        
        # 创建新会话
        self.current_session = GameSession(timestamp, line_num)
        self.sessions.append(self.current_session)
    
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
            if not hasattr(self, '_opponent_template_map'):
                self._opponent_template_map = {}
        
        # 检测PVP结束进入ReplayState（战斗回放）
        elif new_state == "ReplayState" and self._in_pvp:
            # 标记PVP已结束，等待后续状态判断胜负
            self._in_pvp = False
            self._pvp_just_ended = True
        
        # 检测从ReplayState到ChoiceState或EncounterState（PVP胜利，继续下一天）
        elif (new_state == "ChoiceState" or new_state == "EncounterState") and getattr(self, '_pvp_just_ended', False):
            # ReplayState → ChoiceState 或 EncounterState 意味着这局PVP赢了
            # ChoiceState: 正常进入下一天
            # EncounterState: 触发了随机事件（也是胜利）
            victory = True
            
            # 记录战斗信息（这时的物品是PVP结束后的阵容）
            if self._pvp_player_items or self._pvp_opponent_items:
                self.current_session.add_pvp_battle(
                    self._last_pvp_start or timestamp,
                    self._pvp_player_items.copy(),
                    self._pvp_opponent_items.copy(),
                    victory=victory
                )
                
                # 触发PVP结束回调
                for callback in self.pvp_end_callbacks:
                    try:
                        callback(self.current_session, self._pvp_player_items, self._pvp_opponent_items)
                    except Exception as e:
                        print(f"PVP回调函数执行失败: {e}")
                
                # 天数+1（进入下一天）
                self.current_session.days += 1
            
            # 清理PVP相关数据
            self._pvp_just_ended = False
            self._pvp_player_items = []
            self._pvp_opponent_items = []
        
        # 检测游戏胜利结束
        elif new_state == "EndRunVictoryState":
            # 如果是从ReplayState直接进入Victory，说明最后一场赢了
            if getattr(self, '_pvp_just_ended', False):
                # 记录最后一场PVP（胜利）
                if self._pvp_player_items or self._pvp_opponent_items:
                    self.current_session.add_pvp_battle(
                        self._last_pvp_start or timestamp,
                        self._pvp_player_items.copy(),
                        self._pvp_opponent_items.copy(),
                        victory=True
                    )
                self._pvp_just_ended = False
            
            self.current_session.finish(timestamp, line_num, victory=True)
            self.current_session = None
        
        # 检测游戏失败结束
        elif new_state == "EndRunDefeatState":
            # 如果是从ReplayState直接进入Defeat，说明最后一场输了
            if getattr(self, '_pvp_just_ended', False):
                # 记录最后一场PVP（失败）
                if self._pvp_player_items or self._pvp_opponent_items:
                    self.current_session.add_pvp_battle(
                        self._last_pvp_start or timestamp,
                        self._pvp_player_items.copy(),
                        self._pvp_opponent_items.copy(),
                        victory=False
                    )
                self._pvp_just_ended = False
            
            self.current_session.finish(timestamp, line_num, victory=False)
            self.current_session = None


def get_log_directory() -> str:
    """
    获取日志目录路径
    优先使用开发环境的assets/logs，如果不存在则使用生产环境路径
    
    Returns:
        日志目录路径
    """
    # 开发环境路径
    dev_log_dir = Path(__file__).parent.parent / "assets" / "logs"
    if dev_log_dir.exists():
        return str(dev_log_dir)
    
    # 生产环境路径
    prod_log_dir = Path.home() / "AppData" / "LocalLow" / "Tempo Storm" / "The Bazaar"
    if prod_log_dir.exists():
        return str(prod_log_dir)
    
    # 默认返回开发环境路径（即使不存在）
    return str(dev_log_dir)


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
