"""
ログ設定とローテーション機能
"""

import os
import shutil
import logging


def setup_log_rotation() -> str:
    """ログローテーション設定（無条件実行）"""
    log_file = 'morizo_ai.log'
    backup_file = 'morizo_ai.log.1'
    
    # 既存のログファイルがある場合は無条件でバックアップを作成
    if os.path.exists(log_file):
        try:
            # 既存のバックアップファイルがある場合は削除
            if os.path.exists(backup_file):
                os.remove(backup_file)
                print(f"🗑️ 古いバックアップログを削除: {backup_file}")
            
            # 現在のログファイルをバックアップに移動（無条件）
            shutil.move(log_file, backup_file)
            file_size = os.path.getsize(backup_file)
            print(f"📦 ログファイルをバックアップ: {log_file} → {backup_file} (サイズ: {file_size/1024/1024:.1f}MB)")
        except Exception as e:
            print(f"⚠️ ログローテーション失敗: {str(e)}")
    else:
        print(f"📝 新しいログファイルを作成: {log_file}")
    
    return log_file


def setup_logging():
    """ログ設定を初期化"""
    # ログローテーション実行
    log_file = setup_log_rotation()
    
    # ファイルハンドラー（INFOレベルで適度なログ量）
    file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # コンソールハンドラー（INFOレベルのみ）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # ルートロガー設定（INFOレベルで適度なログ量）
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 個別ロガーはDEBUGレベルに設定（ファイルには出力されない）
    logging.getLogger('morizo_ai.planner').setLevel(logging.DEBUG)
    logging.getLogger('morizo_ai.true_react').setLevel(logging.DEBUG)
    logging.getLogger('morizo_ai.ambiguity_detector').setLevel(logging.DEBUG)
    logging.getLogger('morizo_ai.session').setLevel(logging.DEBUG)
    
    # MCP関連のログをINFOレベルに設定（デバッグ用）
    logging.getLogger('morizo_ai.mcp').setLevel(logging.INFO)
    
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
