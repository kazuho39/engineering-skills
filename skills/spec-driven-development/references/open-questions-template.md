# Open-Questions Template（未確定事項テンプレート）

`<親文書>-open-questions.md`（`design-open-questions.md` または `specification-open-questions.md`）を作るときのひな形。構成の考え方は [document-structure](document-structure.md) を参照。

- 未確定事項・PoC が必要な箇所・決定済み事項の記録があるときだけ作る。
- 入口の文書の「オープンクエスチョン」節には、未解決の件数と PoC の有無だけを書き、このファイルへのリンクを張る。

````markdown
# オープンクエスチョン（{design|specification}）: {機能名}

対象: [{design.md}](./{design.md}) の未確定事項。{もう一方の文書}側の未確定事項は `{もう一方}-open-questions.md` に置く（あれば）。

## 決定済みの事項（参考）

- {レビューなどで決まったこと}。{反映先: specification / ADR-N など}

## 実装・検証しながら確かめる事項

- [ ] {不確実な要素}: {いつ・どうやって確認するか}
  - 例: パフォーマンス要件を満たせるか → {どのテスト・計測で確認するか}

## PoC（概念実証）が必要な箇所

- {PoC項目}: {検証する内容と、判断基準}
- なし。（なければその旨を書く）
````
