#!/usr/bin/env python3
"""
曖昧性検出システム
複数アイテムの操作で曖昧性が発生する場合を検出
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from action_planner import Task


@dataclass
class AmbiguityInfo:
    """曖昧性情報"""
    type: str  # "multiple_items", "ambiguous_quantity", "bulk_operation"
    item_name: str
    items: List[Dict[str, Any]]
    task: Task
    needs_confirmation: bool = True


class AmbiguityDetector:
    """曖昧性検出クラス"""
    
    def __init__(self):
        # 確認が必要なツール
        self.confirmation_required_tools = {
            "inventory_delete_by_name",
            "inventory_update_by_name", 
            "inventory_delete_by_name_oldest",
            "inventory_delete_by_name_latest",
            "inventory_update_by_name_oldest",
            "inventory_update_by_name_latest"
        }
    
    def detect_ambiguity(self, task: Task, inventory: List[Dict[str, Any]]) -> Optional[AmbiguityInfo]:
        """曖昧性を検出"""
        import logging
        logger = logging.getLogger("morizo_ai.ambiguity_detector")
        
        logger.info(f"🔍 [曖昧性検出] タスク: {task.tool}, パラメータ: {task.parameters}")
        logger.info(f"🔍 [曖昧性検出] 在庫件数: {len(inventory)}")
        
        if not self.needs_confirmation(task):
            logger.info(f"🔍 [曖昧性検出] 確認不要: {task.tool}")
            return None
        
        if task.tool in ["inventory_delete_by_name", "inventory_update_by_name"]:
            result = self._detect_multiple_items(task, inventory)
            logger.info(f"🔍 [曖昧性検出] 複数アイテム検出結果: {result}")
            return result
        elif task.tool in ["inventory_delete_by_name_oldest", "inventory_delete_by_name_latest",
                          "inventory_update_by_name_oldest", "inventory_update_by_name_latest"]:
            result = self._detect_fifo_ambiguity(task, inventory)
            logger.info(f"🔍 [曖昧性検出] FIFO検出結果: {result}")
            return result
        
        logger.info(f"🔍 [曖昧性検出] 該当ツールなし: {task.tool}")
        return None
    
    def needs_confirmation(self, task: Task) -> bool:
        """確認が必要なタスクかどうかを判定"""
        return task.tool in self.confirmation_required_tools
    
    def _detect_multiple_items(self, task: Task, inventory: List[Dict[str, Any]]) -> Optional[AmbiguityInfo]:
        """複数アイテムの曖昧性を検出"""
        import logging
        logger = logging.getLogger("morizo_ai.ambiguity_detector")
        
        item_name = task.parameters.get("item_name")
        logger.info(f"🔍 [複数アイテム検出] item_name: {item_name}")
        
        if not item_name:
            logger.info(f"🔍 [複数アイテム検出] item_nameが存在しません")
            return None
        
        # 指定された名前のアイテムを検索
        matching_items = [
            item for item in inventory 
            if item.get("item_name") == item_name
        ]
        
        logger.info(f"🔍 [複数アイテム検出] マッチングアイテム数: {len(matching_items)}")
        logger.info(f"🔍 [複数アイテム検出] マッチングアイテム: {matching_items}")
        
        # inventory_delete_by_name の場合は、在庫件数に関係なく常に確認が必要
        if task.tool in ["inventory_delete_by_name", "inventory_update_by_name"]:
            result = AmbiguityInfo(
                type="multiple_items",
                item_name=item_name,
                items=matching_items,
                task=task,
                needs_confirmation=True
            )
            logger.info(f"🔍 [複数アイテム検出] 曖昧性検出（在庫件数: {len(matching_items)}）: {result}")
            return result
        
        logger.info(f"🔍 [複数アイテム検出] 曖昧性なし（アイテム数: {len(matching_items)}）")
        return None
    
    def _detect_fifo_ambiguity(self, task: Task, inventory: List[Dict[str, Any]]) -> Optional[AmbiguityInfo]:
        """FIFO操作の曖昧性を検出"""
        import logging
        logger = logging.getLogger("morizo_ai.ambiguity_detector")
        
        item_name = task.parameters.get("item_name")
        if not item_name:
            return None
        
        # 指定された名前のアイテムを検索
        matching_items = [
            item for item in inventory 
            if item.get("item_name") == item_name
        ]
        
        # inventory_delete_by_name_latest/oldest の場合は、在庫件数に関係なく常に確認が必要
        result = AmbiguityInfo(
            type="fifo_operation",
            item_name=item_name,
            items=matching_items,
            task=task,
            needs_confirmation=True
        )
        logger.info(f"🔍 [FIFO検出] 曖昧性検出（在庫件数: {len(matching_items)}）: {result}")
        return result
    
    def generate_suggestions(self, ambiguity_info: AmbiguityInfo) -> List[Dict[str, str]]:
        """選択肢を生成"""
        if ambiguity_info.type == "multiple_items":
            return [
                {"value": "oldest", "description": "最古のアイテムを操作"},
                {"value": "latest", "description": "最新のアイテムを操作"},
                {"value": "all", "description": "全てのアイテムを操作"},
                {"value": "cancel", "description": "キャンセル"}
            ]
        elif ambiguity_info.type == "fifo_operation":
            if "oldest" in ambiguity_info.task.tool:
                return [
                    {"value": "confirm", "description": "最古のアイテムを操作（確認済み）"},
                    {"value": "cancel", "description": "キャンセル"}
                ]
            elif "latest" in ambiguity_info.task.tool:
                return [
                    {"value": "confirm", "description": "最新のアイテムを操作（確認済み）"},
                    {"value": "cancel", "description": "キャンセル"}
                ]
        
        return [
            {"value": "confirm", "description": "操作を実行"},
            {"value": "cancel", "description": "キャンセル"}
        ]
