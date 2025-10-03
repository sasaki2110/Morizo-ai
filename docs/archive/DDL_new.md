# DDL for recipe_historys table migration

-- ----------------------------------------------------------------
-- 1. 旧 'recipes' テーブル関連オブジェクトの削除
-- ----------------------------------------------------------------
-- Note: 存在しないオブジェクトを削除しようとしてもエラーにならないように `IF EXISTS` を使用しています。

-- RLSポリシーの削除 (テーブル削除時にCASCADEで消えますが、念のため個別に削除)
DROP POLICY IF EXISTS "Users can view own recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can insert own recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can update own recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can delete own recipes" ON public.recipes;

-- テーブルの削除 (CASCADEにより、関連するインデックスやトリガーも自動的に削除されます)
DROP TABLE IF EXISTS public.recipes CASCADE;


-- ----------------------------------------------------------------
-- 2. 新 'recipe_historys' テーブルの作成と設定
-- ----------------------------------------------------------------

-- 料理履歴テーブル
CREATE TABLE recipe_historys (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    source VARCHAR(100), -- 'web', 'rag', 'manual'
    url TEXT, -- レシピのURL
    cooked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5), -- 評価
    notes TEXT, -- メモ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックス作成
CREATE INDEX idx_recipe_historys_user_id ON recipe_historys(user_id);
CREATE INDEX idx_recipe_historys_title ON recipe_historys(title);

-- 更新日時自動更新のトリガー
-- Note: `update_updated_at_column` 関数が未作成の場合は、先にDDL.mdから関数定義を実行してください。
CREATE TRIGGER update_recipe_historys_updated_at BEFORE UPDATE ON recipe_historys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS有効化
ALTER TABLE recipe_historys ENABLE ROW LEVEL SECURITY;

-- ポリシー作成
CREATE POLICY "Users can view own recipe_historys" ON recipe_historys
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own recipe_historys" ON recipe_historys
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own recipe_historys" ON recipe_historys
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own recipe_historys" ON recipe_historys
    FOR DELETE USING (auth.uid() = user_id);
