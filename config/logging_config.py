"""
ログ設定とローテーション機能
"""

import os
import shutil
import logging


def setup_log_rotation() -> str:
    """ログローテーション設定"""
    log_file = 'morizo_ai.log'
    backup_file = 'morizo_ai.log.1'
    
    # 既存のログファイルがある場合、バックアップを作成
    if os.path.exists(log_file):
        try:
            # 既存のバックアップファイルがある場合は削除
            if os.path.exists(backup_file):
                os.remove(backup_file)
                print(f"🗑️ 古いバックアップログを削除: {backup_file}")
            
            # 現在のログファイルをバックアップに移動
            shutil.move(log_file, backup_file)
            print(f"📦 ログファイルをバックアップ: {log_file} → {backup_file}")
            
        except Exception as e:
            print(f"⚠️ ログローテーション失敗: {str(e)}")
    else:
        print(f"📝 新しいログファイルを作成: {log_file}")
    
    return log_file


def setup_logging():
    """ログ設定を初期化"""
    # ログローテーション実行
    log_file = setup_log_rotation()
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8', mode='a'),
            logging.StreamHandler()  # コンソール出力も残す
        ],
        force=True  # 既存の設定を上書き
    )
    
    # FastMCPのログを抑制
    logging.getLogger('mcp').setLevel(logging.WARNING)
    logging.getLogger('mcp.client').setLevel(logging.WARNING)
    logging.getLogger('mcp.server').setLevel(logging.WARNING)
    
    # HTTP関連のログを抑制
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('hpack').setLevel(logging.WARNING)
    
    # ログテスト
    logger = logging.getLogger('morizo_ai')
    logger.info("🚀 Morizo AI アプリケーション起動 - ログテスト")
    
    return logger
