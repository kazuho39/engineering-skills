# engineering-skills

設計・仕様策定を支援する、プロジェクトに依存しない汎用の [Claude Code](https://claude.com/claude-code) スキル集です。
特定のフレームワークやプロジェクトの規約を前提とせず、案件ごとの違いは差し込み口（`project-design-hub`）で吸収します。

> このリポジトリは**書き出し専用**です。スキルの実体は個人開発プロジェクト側で育て、スクリプトで一方向に書き出しています。このリポジトリのファイルを直接編集しても、次回の書き出しで上書きされます。

## スキル一覧

| スキル | 内容 |
|---|---|
| [`dig`](skills/dig/SKILL.md) | プラン・設計・技術的意思決定を、共通理解に達するまで一問ずつ深掘りし、議論を dig log に記録する |
| [`contract-first-design`](skills/contract-first-design/SKILL.md) | 実装前に、事前条件・事後条件・不変条件（契約表）と、副作用の隔離・イミュータブル設計で仕様を固める |
| [`ddd-class-design`](skills/ddd-class-design/SKILL.md) | 値オブジェクト・エンティティ・Repository を中心とした DDD のクラス設計を支援する（実装例は PHP） |
| [`spec-driven-development`](skills/spec-driven-development/SKILL.md) | 要件（specification）と技術設計（design）を段階的に作る仕様駆動開発フロー。入口を短く保ち、クラス設計・テスト設計・ADR・未確定事項を別ファイルに分ける（[構成の定義](skills/spec-driven-development/references/document-structure.md)） |

## コマンドとエージェント

| 種別 | 名前 | 内容 |
|---|---|---|
| コマンド | [`dev-flow`](commands/dev-flow.md) | 作成済みの specification / design を起点に、実装（developer）→ レビュー（reviewer）→ QA（qa）を自動で通す。テストファースト |
| エージェント | [`developer`](agents/developer.md) / [`reviewer`](agents/reviewer.md) / [`qa`](agents/qa.md) | `dev-flow` が起動する汎用のサブエージェント。プロジェクト固有の規約が要る場合は、コピーして書き換える |

### スキル間の関係

```
spec-driven-development
  ├─ dig                    … 不明点の深掘り（あれば使う）
  ├─ contract-first-design  … クラス設計の契約表（あれば使う）
  └─ project-design-hub     … プロジェクト固有の設計規約（あれば使う。無ければ既定で進む）

dev-flow（コマンド）         … spec-driven-development の成果物（specification / design）を入力にする
  └─ project-design-hub     … テスト実行コマンド・実装規約・レビュー観点（あれば使う）
```

各スキルは、他のスキルが無くても単体で動くように書かれています。「あれば使う、無ければ本文の既定に従う」という関係です。
`ddd-class-design` は他のスキルに依存しません。

## 使い方

### 1. スキルを導入する

すべてのプロジェクトで使うなら、ユーザー全体のスキルとして置きます。

```bash
git clone <このリポジトリの URL> engineering-skills
mkdir -p ~/.claude/skills
cp -R engineering-skills/skills/* ~/.claude/skills/
```

特定のプロジェクトだけで使うなら、そのプロジェクトの `.claude/skills/` に必要なスキルだけをコピーします。

```bash
mkdir -p <プロジェクト>/.claude/skills
cp -R engineering-skills/skills/dig <プロジェクト>/.claude/skills/
```

`dev-flow` を使う場合は、コマンドとエージェントもコピーします（`dev-flow` は `developer` / `reviewer` / `qa` のエージェントを起動します）。

```bash
mkdir -p <プロジェクト>/.claude/commands <プロジェクト>/.claude/agents
cp engineering-skills/commands/dev-flow.md <プロジェクト>/.claude/commands/
cp engineering-skills/agents/*.md <プロジェクト>/.claude/agents/
```

更新するときは、このリポジトリを `git pull` して、同じ手順でコピーし直します。

### 2. プロジェクト固有の設計規約をつなぐ（`project-design-hub`）

`spec-driven-development` は、設計の各場面でプロジェクト固有の規約を `project-design-hub` というスキルに問い合わせます。無ければ本文の既定で進むので、最初は作らなくても使えます。

案件の規約（技術スタック、レイヤー配置、テスト規約、命名規則、出力先など）に合わせたいときは、雛形をコピーして埋めます。

```bash
mkdir -p <プロジェクト>/.claude/skills/project-design-hub
cp engineering-skills/templates/project-design-hub/SKILL.md <プロジェクト>/.claude/skills/project-design-hub/
```

雛形の `TODO` を、そのプロジェクトの実情で埋めます。ハブは「どの場面で、どのスキル・規約を使うか」の振り分け表です。設計の中身は書かず、既存のスキルや規約へのリンクだけを持たせます。

## 構成

```
skills/       書き出された汎用スキル（直接編集しない）
templates/    プロジェクトごとに複製して使う雛形
  └─ project-design-hub/
```

`templates/` はスキルとして自動では有効になりません。コピーして初めて使われます。

## 設計方針

- **汎用スキルは固有スキルを知らない**: 依存の向きは「固有 → 汎用」のみ。汎用側にプロジェクト名や他スキルへの参照を書かない
- **規約は「あれば従う、なければ既定」**: プロジェクトに規約があればそれに従い、無ければ本文の既定で進める
- **コード例は PHP**: 言語非依存の考え方を、動く例で示しています。他言語では読み替えてください
