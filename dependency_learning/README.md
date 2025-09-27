# Dependency Learning Lab

## 📋 概要

MorizoAIの依存関係エラー修正に向けた、段階的な学習プロジェクトです。
手を動かして概念を理解する実践的なアプローチを採用します。

## 🎯 学習目標

- **依存関係管理の概念理解**: タスクIDシステム、依存関係グラフ、トポロジカルソート
- **実装スキルの習得**: 実際のコードで依存関係を管理する方法
- **MorizoAIへの適用**: 学習内容を既存コードベースに段階的に適用

## 📚 学習プロジェクト構成

```
dependency_learning/
├── README.md
├── requirements.txt
├── phase1_simple_dependencies.py
├── phase2_mock_tools.py
├── phase3_parallel_execution.py
├── phase4_error_handling.py
├── tests/
│   ├── test_dependencies.py
│   └── test_execution.py
└── examples/
    ├── menu_planning.py
    └── shopping_assistant.py
```

## 🚀 段階的学習プラン

### Phase 1: 超シンプルな依存関係（30分）
- **目標**: 依存関係の基本概念理解
- **ファイル**: `phase1_simple_dependencies.py`
- **学習ポイント**: 依存関係の基本概念、実行順序の決定方法

### Phase 2: 実際のツール実行（1時間）
- **目標**: 実際のMCPツールを模擬した依存関係管理
- **ファイル**: `phase2_mock_tools.py`
- **学習ポイント**: 実際のツール実行の模擬、データフローの管理

### Phase 3: 並列実行の学習（1時間）
- **目標**: 並列実行可能なタスクの特定と実行
- **ファイル**: `phase3_parallel_execution.py`
- **学習ポイント**: 並列実行の概念、非同期プログラミング

### Phase 4: エラーハンドリング（30分）
- **目標**: 依存関係エラー時の処理
- **ファイル**: `phase4_error_handling.py`
- **学習ポイント**: エラーハンドリング、代替処理の実装

## 🎯 MorizoAIでの現在の問題

### 依存関係エラーの詳細
```python
# 現在（問題あり）
task1 = {"description": "現在の在庫をリストアップ"}
task2 = {"dependencies": ["現在の在庫をリストアップ"]}  # 完全一致が必要

# 改善案
task1 = {"id": "inventory_fetch", "description": "現在の在庫をリストアップ"}
task2 = {"dependencies": ["inventory_fetch"]}  # IDで参照
```

## 📊 学習の進め方

1. **各Phaseで目標を設定**
2. **テスト駆動で学習**
3. **実際のMorizoAIに適用**

## 🚀 学習開始

```bash
cd /app/Morizo-ai/dependency_learning
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

**作成日**: 2025年9月26日  
**バージョン**: 1.0  
**作成者**: AIエージェント協働チーム
