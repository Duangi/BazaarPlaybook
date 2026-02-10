"""
实时日志监控服务
监控 Player.log 和 Player-prev.log 的变化，实时解析新增会话
"""
import os
import time
from pathlib import Path
from threading import Thread, Event
from PySide6.QtCore import QObject, Signal
from loguru import logger
from typing import Optional

from services.log_analyzer import LogAnalyzer
from platforms.adapter import PlatformAdapter


class LogWatcher(QObject):
    """日志监控服务"""
    
    # 信号：新会话检测到
    new_session_detected = Signal(object)  # GameSession
    # 信号：会话更新（PVP完成）
    session_updated = Signal(object)  # GameSession
    # 信号：监控状态改变
    status_changed = Signal(bool, str)  # (is_running, status_message)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 获取平台特定的日志路径
        log_path_provider = PlatformAdapter.get_game_log_path_provider()
        
        # 日志文件路径（跨平台）
        self.log_dir = log_path_provider.get_log_directory()
        self.player_log = log_path_provider.get_player_log_path()
        self.player_prev_log = log_path_provider.get_player_prev_log_path()
        
        # 验证路径
        if self.log_dir is None or self.player_log is None:
            logger.error("无法获取游戏日志路径，日志监控功能将不可用")
            logger.info("请确保游戏已安装并至少运行过一次")
        else:
            logger.info(f"日志目录: {self.log_dir}")
            logger.info(f"Player.log: {self.player_log}")
        
        # 日志分析器
        if self.log_dir:
            self.analyzer = LogAnalyzer(str(self.log_dir))
        else:
            self.analyzer = None
        
        # 监控线程控制
        self.running = False
        self.stop_event = Event()
        self.monitor_thread: Optional[Thread] = None
        
        # 文件监控状态：记录上次读取的文件位置
        self.last_player_log_pos = 0  # Player.log的读取位置
        self.last_player_prev_log_pos = 0  # Player-prev.log的读取位置
        self.last_session_count = 0
        
        # 已知的会话ID集合（避免重复通知）
        self.known_session_ids = set()
    
    def start(self):
        """启动监控"""
        if self.running:
            logger.warning("[LogWatcher] 已在运行中")
            return
        
        # 检查日志路径是否有效
        if self.log_dir is None or self.analyzer is None:
            logger.error("[LogWatcher] 日志路径无效，无法启动监控")
            self.status_changed.emit(False, "日志路径无效")
            return
        
        self.running = True
        self.stop_event.clear()
        
        # 启动监控线程
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("[LogWatcher] 日志监控已启动")
        self.status_changed.emit(True, "监控中...")
    
    def stop(self):
        """停止监控"""
        if not self.running:
            return
        
        self.running = False
        self.stop_event.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        logger.info("[LogWatcher] 日志监控已停止")
        self.status_changed.emit(False, "已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        # 初始化：记录当前文件大小和会话数
        self._initialize_state()
        
        while self.running and not self.stop_event.is_set():
            try:
                # 检查日志文件变化
                self._check_log_changes()
                
                # 等待一段时间再检查（避免频繁IO）
                self.stop_event.wait(1.0)  # 每秒检查一次
                
            except Exception as e:
                logger.error(f"[LogWatcher] 监控循环错误: {e}")
                time.sleep(5)  # 出错后等待5秒再继续
    
    def _initialize_state(self):
        """初始化监控状态"""
        try:
            # 检查路径有效性
            if not self.player_log or not self.analyzer:
                logger.error("[LogWatcher] 日志路径无效，无法初始化")
                return
            
            # 记录初始文件位置（移动到文件末尾）
            if self.player_log.exists():
                self.last_player_log_pos = self.player_log.stat().st_size
            
            if self.player_prev_log and self.player_prev_log.exists():
                self.last_player_prev_log_pos = self.player_prev_log.stat().st_size
            
            # 初次分析，获取所有已存在的会话
            result = self.analyzer.analyze()
            sessions = result.get('sessions', [])
            
            # 记录已知会话ID
            self.known_session_ids = {s.session_id for s in sessions}
            self.last_session_count = len(sessions)
            
            logger.info(f"[LogWatcher] 初始化完成，已有 {len(sessions)} 个会话")
            logger.info(f"[LogWatcher] Player.log 位置: {self.last_player_log_pos}, Player-prev.log 位置: {self.last_player_prev_log_pos}")
            
        except Exception as e:
            logger.error(f"[LogWatcher] 初始化失败: {e}")
    
    def _check_log_changes(self):
        """检查日志文件变化，只读取增量内容"""
        try:
            new_lines = []  # 存储新增的所有行
            
            # 检查 Player.log 的增量
            if self.player_log.exists():
                current_size = self.player_log.stat().st_size
                if current_size > self.last_player_log_pos:
                    # 文件增长，读取增量部分
                    with open(self.player_log, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(self.last_player_log_pos)
                        incremental_content = f.read()
                        if incremental_content.strip():
                            new_lines.extend(incremental_content.splitlines())
                            logger.debug(f"[LogWatcher] Player.log 新增 {len(incremental_content.splitlines())} 行")
                    self.last_player_log_pos = current_size
                elif current_size < self.last_player_log_pos:
                    # 文件被重置（清空或重写），重新读取全文
                    logger.info(f"[LogWatcher] Player.log 被重置，重新读取")
                    self.last_player_log_pos = 0
                    with open(self.player_log, 'r', encoding='utf-8', errors='ignore') as f:
                        new_lines.extend(f.read().splitlines())
                    self.last_player_log_pos = current_size
            
            # 检查 Player-prev.log 的增量
            if self.player_prev_log.exists():
                current_size = self.player_prev_log.stat().st_size
                if current_size > self.last_player_prev_log_pos:
                    with open(self.player_prev_log, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(self.last_player_prev_log_pos)
                        incremental_content = f.read()
                        if incremental_content.strip():
                            new_lines.extend(incremental_content.splitlines())
                            logger.debug(f"[LogWatcher] Player-prev.log 新增 {len(incremental_content.splitlines())} 行")
                    self.last_player_prev_log_pos = current_size
                elif current_size < self.last_player_prev_log_pos:
                    logger.info(f"[LogWatcher] Player-prev.log 被重置，重新读取")
                    self.last_player_prev_log_pos = 0
                    with open(self.player_prev_log, 'r', encoding='utf-8', errors='ignore') as f:
                        new_lines.extend(f.read().splitlines())
                    self.last_player_prev_log_pos = current_size
            
            # 如果有新内容，进行增量分析
            if new_lines:
                logger.debug(f"[LogWatcher] 检测到 {len(new_lines)} 行新内容，进行增量分析...")
                self._analyze_incremental(new_lines)
                
        except Exception as e:
            logger.error(f"[LogWatcher] 检查日志变化失败: {e}")
    
    def _analyze_incremental(self, new_lines: list):
        """增量分析新内容，只处理增量部分"""
        try:
            # 使用analyzer的增量分析方法
            result = self.analyzer.analyze_incremental(new_lines)
            
            if not result:
                return
            
            new_sessions = result.get('new_sessions', [])
            updated_sessions = result.get('updated_sessions', [])
            
            # 通知新会话
            for session in new_sessions:
                logger.info(f"[LogWatcher] 检测到新会话: {session.session_id} (Day {session.days})")
                self.new_session_detected.emit(session)
                self.known_session_ids.add(session.session_id)
            
            # 通知更新的会话
            for session in updated_sessions:
                logger.info(f"[LogWatcher] 会话更新: {session.session_id}")
                self.session_updated.emit(session)
            
        except Exception as e:
            logger.error(f"[LogWatcher] 增量分析失败: {e}")
            import traceback
            traceback.print_exc()
    
    def force_analyze(self):
        """强制重新分析日志（用于手动刷新）"""
        logger.info("[LogWatcher] 强制重新分析日志...")
        # 重新初始化状态，全量分析
        self._initialize_state()
