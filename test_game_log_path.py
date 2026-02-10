#!/usr/bin/env python3
"""
游戏日志路径测试脚本

测试跨平台日志路径获取功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from platforms.adapter import PlatformAdapter

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO")


def test_log_path_detection():
    """测试日志路径检测"""
    logger.info("=" * 60)
    logger.info("测试游戏日志路径检测")
    logger.info("=" * 60)
    
    # 显示当前平台
    logger.info(f"当前平台: {sys.platform}")
    
    # 获取日志路径提供者
    provider = PlatformAdapter.get_game_log_path_provider()
    logger.info(f"路径提供者类型: {type(provider).__name__}")
    
    # 获取日志目录
    log_dir = provider.get_log_directory()
    if log_dir:
        logger.info(f"日志目录: {log_dir}")
        if log_dir.exists():
            logger.success(f"✅ 日志目录存在")
            
            # 列出目录内容
            try:
                files = list(log_dir.iterdir())
                logger.info(f"目录内文件数: {len(files)}")
                for f in files:
                    size = f.stat().st_size if f.is_file() else 0
                    logger.info(f"  - {f.name} ({'目录' if f.is_dir() else f'{size:,} bytes'})")
            except Exception as e:
                logger.warning(f"无法列出目录内容: {e}")
        else:
            logger.warning(f"⚠️  日志目录不存在")
            logger.info("可能的原因：")
            logger.info("  1. 游戏尚未安装")
            logger.info("  2. 游戏从未运行过")
            logger.info("  3. 使用了自定义安装路径")
    else:
        logger.error("❌ 无法获取日志目录")
    
    # 获取 Player.log 路径
    player_log = provider.get_player_log_path()
    if player_log:
        logger.info(f"Player.log 路径: {player_log}")
        if player_log.exists():
            logger.success(f"✅ Player.log 存在")
            size = player_log.stat().st_size
            logger.info(f"文件大小: {size:,} bytes ({size / 1024 / 1024:.2f} MB)")
            
            # 读取前几行
            try:
                with open(player_log, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [f.readline() for _ in range(3)]
                    logger.info("文件前 3 行:")
                    for i, line in enumerate(lines, 1):
                        logger.info(f"  {i}: {line.strip()[:80]}...")
            except Exception as e:
                logger.warning(f"无法读取文件: {e}")
        else:
            logger.warning(f"⚠️  Player.log 不存在")
    else:
        logger.error("❌ 无法获取 Player.log 路径")
    
    # 获取 Player-prev.log 路径
    player_prev_log = provider.get_player_prev_log_path()
    if player_prev_log:
        logger.info(f"Player-prev.log 路径: {player_prev_log}")
        if player_prev_log.exists():
            logger.success(f"✅ Player-prev.log 存在")
            size = player_prev_log.stat().st_size
            logger.info(f"文件大小: {size:,} bytes ({size / 1024 / 1024:.2f} MB)")
        else:
            logger.info(f"Player-prev.log 不存在（正常，只在日志轮转后出现）")
    
    # 验证目录
    logger.info("\n验证日志目录:")
    if provider.validate_log_directory():
        logger.success("✅ 日志目录验证通过")
    else:
        logger.error("❌ 日志目录验证失败")


def test_platform_specific():
    """测试平台特定功能"""
    logger.info("\n" + "=" * 60)
    logger.info("平台特定检查")
    logger.info("=" * 60)
    
    if sys.platform.startswith("linux"):
        logger.info("Linux 平台特定检查:")
        
        # 检查是否为 Steam Deck
        try:
            with open('/sys/devices/virtual/dmi/id/product_name', 'r') as f:
                product = f.read().strip()
                if 'Jupiter' in product or 'Galileo' in product:
                    logger.success(f"✅ 检测到 Steam Deck: {product}")
                else:
                    logger.info(f"设备型号: {product}")
        except:
            logger.info("无法读取设备信息（可能非 Steam Deck）")
        
        # 检查 Steam 安装
        home = os.environ.get('HOME', '')
        steam_paths = [
            os.path.join(home, '.steam', 'steam'),
            os.path.join(home, '.var', 'app', 'com.valvesoftware.Steam'),
        ]
        
        for path in steam_paths:
            if os.path.exists(path):
                logger.success(f"✅ 找到 Steam 目录: {path}")
        
        # 检查 compatdata
        compatdata = os.path.join(home, '.steam', 'steam', 'steamapps', 'compatdata')
        if os.path.exists(compatdata):
            try:
                apps = [d for d in os.listdir(compatdata) if os.path.isdir(os.path.join(compatdata, d))]
                logger.info(f"找到 {len(apps)} 个 Proton 应用目录")
                if apps:
                    logger.info(f"App IDs: {', '.join(apps[:10])}{'...' if len(apps) > 10 else ''}")
            except:
                pass
    
    elif sys.platform == "darwin":
        logger.info("macOS 平台特定检查:")
        
        home = os.environ.get('HOME', '')
        library = os.path.join(home, 'Library')
        
        if os.path.exists(library):
            logger.success(f"✅ Library 目录存在: {library}")
            
            logs_dir = os.path.join(library, 'Logs')
            if os.path.exists(logs_dir):
                logger.success(f"✅ Logs 目录存在")
                
                # 列出 Logs 下的游戏公司目录
                try:
                    companies = [d for d in os.listdir(logs_dir) if os.path.isdir(os.path.join(logs_dir, d))]
                    if companies:
                        logger.info(f"找到的游戏公司目录: {', '.join(companies[:10])}")
                except:
                    pass
    
    elif sys.platform == "win32":
        logger.info("Windows 平台特定检查:")
        
        userprofile = os.environ.get('USERPROFILE', '')
        if userprofile:
            logger.success(f"✅ USERPROFILE: {userprofile}")
            
            appdata = os.path.join(userprofile, 'AppData', 'LocalLow')
            if os.path.exists(appdata):
                logger.success(f"✅ AppData\\LocalLow 存在")
                
                # 列出游戏公司目录
                try:
                    companies = [d for d in os.listdir(appdata) if os.path.isdir(os.path.join(appdata, d))]
                    if companies:
                        logger.info(f"找到的游戏公司目录: {', '.join(companies[:10])}")
                except:
                    pass


def test_log_watcher_integration():
    """测试与 LogWatcher 的集成"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 LogWatcher 集成")
    logger.info("=" * 60)
    
    try:
        from services.log_watcher import LogWatcher
        
        watcher = LogWatcher()
        
        if watcher.log_dir:
            logger.success(f"✅ LogWatcher 日志目录: {watcher.log_dir}")
        else:
            logger.warning("⚠️  LogWatcher 日志目录未设置")
        
        if watcher.player_log:
            logger.success(f"✅ LogWatcher Player.log: {watcher.player_log}")
        else:
            logger.warning("⚠️  LogWatcher Player.log 未设置")
        
        if watcher.analyzer:
            logger.success("✅ LogWatcher 分析器已初始化")
        else:
            logger.warning("⚠️  LogWatcher 分析器未初始化")
        
    except Exception as e:
        logger.exception(f"❌ LogWatcher 集成测试失败: {e}")


def main():
    """主测试流程"""
    logger.info("🎮 游戏日志路径跨平台测试\n")
    
    try:
        test_log_path_detection()
        test_platform_specific()
        test_log_watcher_integration()
        
        logger.info("\n" + "=" * 60)
        logger.success("🎉 测试完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.exception(f"测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n测试被用户中断")
        sys.exit(1)
