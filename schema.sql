--  商品情報を保存するテーブル
create table products (
  id uuid default gen_random_uuid() primary key,
  platform text not null, -- 'mercari' など
  item_id text not null, -- プラットフォーム上のID
  title text not null,
  price bigint not null,
  image_url text,
  product_url text,
  scraped_at timestamp with time zone default now(),
  
  -- AI分析結果
  ai_analysis jsonb, -- { "condition": "A", "estimated_price": 50000, "profit": 5000 }
  
  -- ステータス管理
  status text default 'new', -- 'new'(新規), 'analyzed'(分析済), 'profitable'(利益あり), 'discarded'(対象外)
  
  unique(platform, item_id)
);

-- 検索設定（監視リスト）を保存するテーブル
create table search_configs (
  id uuid default gen_random_uuid() primary key,
  keyword text not null,
  min_price bigint,
  max_price bigint,
  target_profit bigint default 3000, -- 目標利益額
  is_active boolean default true,
  created_at timestamp with time zone default now()
);

-- 初期データのサンプル（テスト用）
insert into search_configs (keyword, min_price, max_price, target_profit)
values ('MacBook Air M1', 30000, 80000, 10000);
