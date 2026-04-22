# docsscoring-rules.md

# eBay-Research-Edge Scoring Rules

## 1. 目的
商品の優先順位付けを感覚ではなく数値ベースで行うため、
候補スコアを定義する。

## 2. 総合スコア
candidate_score = 0.4  demand_score + 0.4  profit_score + 0.2  supply_score

## 3. demand_score
需要の強さを評価する。

使用指標
- sold_30d
- sold_90d
- str

例
- sold_30d が多いほど加点
- str が高いほど加点

## 4. profit_score
利益の出やすさを評価する。

使用指標
- estimated_profit_rate
- estimated_profit_jpy

例
- 粗利率が高いほど加点
- 利益額が高いほど加点

## 5. supply_score
競合の強さ・供給過多リスクを評価する。

使用指標
- active_count

例
- active_count が少ないほど加点

## 6. 初期判定ルール
- 80点以上 list_candidate
- 60〜79点 hold
- 59点以下 skip

## 7. 注意
- 本スコアはMVP段階の仮ルールである
- 実運用しながら重みや閾値を調整する
- 将来的にはカテゴリごとに別ルールを持たせる可能性がある