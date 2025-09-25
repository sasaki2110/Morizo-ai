#!/usr/bin/env python3
"""
レシピベクトルDBテストプログラム

このスクリプトは、構築されたレシピベクトルDBの動作確認を行います。

使用方法:
    python tests/test_recipe_vector_db.py

前提条件:
    - recipe_vector_db/が存在すること
    - OpenAI APIキーが設定されていること
"""

import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

# LangChain関連のインポート
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RecipeVectorDBTester:
    """レシピベクトルDBのテストクラス"""
    
    def __init__(self, vector_db_path: str):
        """
        初期化
        
        Args:
            vector_db_path: ベクトルDBのパス
        """
        self.vector_db_path = vector_db_path
        self.vectorstore = None
        
    def load_vector_db(self):
        """ベクトルDBを読み込む"""
        try:
            logger.info(f"ベクトルDB読み込み中: {self.vector_db_path}")
            
            # OpenAI Embeddingsの初期化
            embeddings = OpenAIEmbeddings()
            
            # ChromaDBベクトルストアを読み込み
            self.vectorstore = Chroma(
                persist_directory=self.vector_db_path,
                embedding_function=embeddings
            )
            
            logger.info("ベクトルDB読み込み完了")
            return True
            
        except Exception as e:
            logger.error(f"ベクトルDB読み込みエラー: {e}")
            return False
    
    def test_basic_search(self, query: str, k: int = 5):
        """
        基本的な検索テスト
        
        Args:
            query: 検索クエリ
            k: 取得件数
        """
        try:
            logger.info(f"検索テスト: '{query}' (上位{k}件)")
            
            # 類似度検索
            results = self.vectorstore.similarity_search(query, k=k)
            
            logger.info(f"検索結果: {len(results)}件")
            
            for i, result in enumerate(results):
                metadata = result.metadata
                # テキストからタイトルを抽出
                text = result.page_content
                title = text.split(' ')[0] if text else 'Unknown'
                category = metadata.get('recipe_category', 'Unknown')
                main_ingredients = metadata.get('main_ingredients', 'Unknown')
                
                logger.info(f"  {i+1}. {title}")
                logger.info(f"     分類: {category}")
                logger.info(f"     主材料: {main_ingredients}")
                logger.info(f"     テキスト: {text[:100]}...")
                logger.info("")
            
            return results
            
        except Exception as e:
            logger.error(f"検索テストエラー: {e}")
            return []
    
    def test_search_with_score(self, query: str, k: int = 5):
        """
        スコア付き検索テスト
        
        Args:
            query: 検索クエリ
            k: 取得件数
        """
        try:
            logger.info(f"スコア付き検索テスト: '{query}' (上位{k}件)")
            
            # スコア付き類似度検索
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            logger.info(f"検索結果: {len(results)}件")
            
            for i, (result, score) in enumerate(results):
                metadata = result.metadata
                title = metadata.get('title', 'Unknown')
                category = metadata.get('recipe_category', 'Unknown')
                
                logger.info(f"  {i+1}. {title} (スコア: {score:.4f})")
                logger.info(f"     分類: {category}")
                logger.info("")
            
            return results
            
        except Exception as e:
            logger.error(f"スコア付き検索テストエラー: {e}")
            return []
    
    def test_metadata_filter(self, query: str, category_filter: str = None):
        """
        メタデータフィルタリングテスト
        
        Args:
            query: 検索クエリ
            category_filter: 分類フィルタ
        """
        try:
            logger.info(f"メタデータフィルタテスト: '{query}'")
            if category_filter:
                logger.info(f"フィルタ: 分類 = '{category_filter}'")
            
            # フィルタ条件を設定
            filter_dict = {}
            if category_filter:
                filter_dict['recipe_category'] = category_filter
            
            # フィルタ付き検索
            if filter_dict:
                results = self.vectorstore.similarity_search(
                    query, 
                    k=5, 
                    filter=filter_dict
                )
            else:
                results = self.vectorstore.similarity_search(query, k=5)
            
            logger.info(f"フィルタ結果: {len(results)}件")
            
            for i, result in enumerate(results):
                metadata = result.metadata
                title = metadata.get('title', 'Unknown')
                category = metadata.get('recipe_category', 'Unknown')
                
                logger.info(f"  {i+1}. {title} ({category})")
            
            return results
            
        except Exception as e:
            logger.error(f"メタデータフィルタテストエラー: {e}")
            return []
    
    def test_database_info(self):
        """データベース情報の表示"""
        try:
            logger.info("=== データベース情報 ===")
            
            # コレクション情報を取得
            collection = self.vectorstore._collection
            
            # ドキュメント数を取得
            count = collection.count()
            logger.info(f"総ドキュメント数: {count}")
            
            # メタデータの例を取得
            sample_docs = collection.get(limit=3)
            
            if sample_docs['metadatas']:
                logger.info("メタデータの例:")
                for i, metadata in enumerate(sample_docs['metadatas'][:3]):
                    logger.info(f"  {i+1}. {metadata}")
            
            logger.info("")
            
        except Exception as e:
            logger.error(f"データベース情報取得エラー: {e}")

def main():
    """メイン処理"""
    # .envファイルの読み込み
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    env_path = project_root / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f".envファイルを読み込みました: {env_path}")
    else:
        logger.warning(f".envファイルが見つかりません: {env_path}")
    
    # OpenAI APIキーの確認
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEYが設定されていません。.envファイルを確認してください。")
        sys.exit(1)
    
    # ベクトルDBのパス設定
    vector_db_path = project_root / "recipe_vector_db"
    
    if not vector_db_path.exists():
        logger.error(f"ベクトルDBが見つかりません: {vector_db_path}")
        logger.error("先に scripts/build_vector_db.py を実行してください。")
        sys.exit(1)
    
    logger.info("=== レシピベクトルDBテスト開始 ===")
    
    # テストクラスの初期化
    tester = RecipeVectorDBTester(str(vector_db_path))
    
    # ベクトルDBの読み込み
    if not tester.load_vector_db():
        logger.error("ベクトルDBの読み込みに失敗しました。")
        sys.exit(1)
    
    # データベース情報の表示
    tester.test_database_info()
    
    # テストケースの実行
    test_cases = [
        ("牛乳", "牛乳を使ったレシピの検索"),
        ("卵", "卵を使ったレシピの検索"),
        ("肉", "肉を使ったレシピの検索"),
        ("野菜", "野菜を使ったレシピの検索"),
        ("主菜", "主菜の検索"),
        ("副菜", "副菜の検索"),
        ("フレンチトースト", "具体的な料理名の検索"),
        ("肉じゃが", "具体的な料理名の検索"),
    ]
    
    for query, description in test_cases:
        logger.info(f"=== {description} ===")
        tester.test_basic_search(query, k=3)
        logger.info("")
    
    # スコア付き検索のテスト
    logger.info("=== スコア付き検索テスト ===")
    tester.test_search_with_score("牛乳と卵", k=3)
    
    # メタデータフィルタのテスト
    logger.info("=== メタデータフィルタテスト ===")
    tester.test_metadata_filter("牛乳", "主菜")
    tester.test_metadata_filter("野菜", "副菜")
    
    logger.info("=== レシピベクトルDBテスト完了 ===")

if __name__ == "__main__":
    main()
