# Design Test-Plan Template（テスト設計テンプレート）

`design-test-plan.md` を作るときのひな形。構成の考え方は [document-structure](document-structure.md) の「design-test-plan.md」を参照。

> `project-design-hub` が示すテスト規約・スキルがあればそれに従う。示されなければ、クラス設計の契約の各行から1ケース以上を導く。正常系・境界値・異常系を含める。

````markdown
# テスト設計（design）: {機能名}

対象: [design-class-design.md](./design-class-design.md)（クラス設計）の各クラスの契約と、[specification.md](./specification.md) の受け入れ条件（AC）から導いたテスト。方針: {テスト規約・スキル}。

## 1. 作るテスト（ファイルツリー）

凡例: ★ 新規 / ✎ 既存を修正 / 無印 既存（回帰確認のみ）。「対象」は design-class-design.md の見出し（クラス）に対応する。

```text
tests/
├── Unit/
│   └── {Context}/{ClassName}Test.{ext}        ★ 対象: {ClassName}
└── Feature/
    ├── {Context}/{Endpoint}Test.{ext}         ★ 対象: {Controller::action} 経由で
    │                                                  {UseCase} / {Repository} / {Request} / {Resource}
    └── {Existing}Test.{ext}                     回帰: {何が変わらないことを確認するか}

{フロントエンドのテスト置き場}/                  （画面側。クラス設計の対象外）
└── {Component}.spec.{ext}                     ★
```

## 2. Unit

契約の事前条件・事後条件・不変条件から、正常系・境界値・異常系を導く。モックは純粋なクラスでは使わない。

### `{Context}/{ClassName}Test.{ext}` ★

- **対象**: `{ClassName::method()}`（design-class-design.md の「{層} / {ClassName}」）

| ケース | 期待 |
|-------|------|
| {正常系} | {…} |
| {境界値} | {…} |
| {異常系} | {例外・エラー} |

## 3. Feature（結合）

HTTP などの入口から、Controller・UseCase・Repository・Resource を貫通して検証する。受け入れ条件が仕様の根拠。

### `{Context}/{Endpoint}Test.{ext}` ★

- **対象**: {貫通するクラスを列挙}
- **対応するAC**: {AC-001〜AC-0xx}

| 観点 | 主なAC | 検証するクラスの契約 |
|------|-------|--------------------|
| {例: 公開のみ・削除済み除外} | {AC-001} | {UseCase: …／Repository: …} |

- {レスポンス構造・境界値・並び順など、特に注意する検証方法}

## 4. {フロントエンド等}（クラス設計の対象外）

### `{Component}.spec.{ext}` ★
- **対応するAC**: {AC-0xx}（{検証する内容}）

## 5. クラスからテストへの対応確認

design-class-design.md の全クラスから、導けるテストがあることを確認する。

| クラス（design-class-design.md の見出し） | Unit | Feature（AC） |
|----------------------------------------|------|--------------|
| `{path/ClassName}` | `{ClassNameTest}` | {AC-001} |

導けない行はない。（導けない行があれば、その契約が曖昧なので、クラス設計を直す）
````

## 書き方のポイント

- テストツリーの行と、見出しを**1対1**にする。各見出しに「対象」（クラス設計のどのクラスか）を必ず書く。
- クラス設計の全クラスが、「5. クラスからテストへの対応確認」のいずれかの行に現れること。
- 受け入れ条件（AC）は、どのテストファイルが検証するかを必ず1つ以上割り当てる。
