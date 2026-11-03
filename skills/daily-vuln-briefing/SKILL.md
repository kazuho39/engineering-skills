---
name: daily-vuln-briefing
description: 公開されている脆弱性情報（CISA KEV）と、プロファイルで指定したリポジトリの依存の audit（composer audit / npm audit）から、そのプロファイルに関係するものを集めて日本語のブリーフィング本文にまとめる。投稿や保存はしない（出力先はタスク側で決める）。スケジュールタスク専用。引数: プロファイル JSON のパス。
disable-model-invocation: true
---

プロファイル（対象リポジトリ・スタックを書いた JSON）に関係する脆弱性を集め、更新すべきか判断できるブリーフィング本文を作る。状態ファイルは持たず、実行のたびに今の状況をそのまま出す。ニュース記事は対象外。

**引数**: プロファイル JSON のパス（呼び出し側のタスクが渡す。例: `profiles/example.json`）。相対パスはこのスキルのディレクトリが基準。書式は `profiles/example.json` を見る。

## Steps

### 1. 取得
```bash
cd {このスキルのディレクトリ} && python3 fetch_vulns.py --config {プロファイルのパス}
```
出力 JSON: `{ profile, repos, errors, kev, audit }`

- `profile`: プロファイル名（見出しに使う）。`repos`: 監査したリポジトリ名

- `kev`: 直近に CISA KEV へ追加され、自スタックに該当するもの。実行の間隔より長く取るので、同じ項目が数回出る。`id`(CVE), `title`, `summary`, `action`, `url`(NVD), `kev_url`(KEV カタログ), `stack`, `date`, `ransomware`(true なら悪用でランサムウェア利用あり), `cvss`(`{score, severity}` または null)
- `audit`: 今の依存に残っている脆弱性のうち high 以上（または KEV 掲載）。null なら未実施
  - `findings`: パッケージ単位。`repo`, `ecosystem`, `package`, `installed`, `dev`(開発用依存のみか), `severity`(最大), `count`, `cvss`(代表の `{score, severity}` または null), `kev`(KEV 掲載の CVE), `kev_urls`(その KEV カタログ), `fix`(npm のみ: `true` = `npm audit fix` で可 / `false` = 修正版なし / `{name, version}` = メジャー更新が必要), `advisories`(`id`, `cve`, `severity`, `title`, `range`, `url`。先頭が代表)
  - `below_min_severity`: high 未満の件数
  - `errors`: 監査の失敗（例: Docker が停止していて composer が実行できない）。lock ファイルが無い言語は監査しない（失敗にはならない）
- `errors`: 取得元の失敗

### 2. まとめる
本文を日本語の Markdown で作る。英語の情報も日本語で要約し、出力に書かれていないことは推測で補わない。形（見出しの階層・各項目の行）は [template.md](template.md) に従う。`{...}` は出力の値で埋める。

- **見出し**: `{profile}` は出力の `profile`
- **朝|夕**: `date +%H` が 12 未満なら朝、それ以外は夕
- **セクション**: `## 🚨 KEV` と `## 📦 依存の未解消` の2つは、常に見出しを出す。該当が無いセクションは、見出しの下に `該当なし` とだけ書く
- **KEV**: `kev` を1項目ずつ。`cvss` が null なら「CVSS 未採点」（数値を推測しない）。`ransomware` が true のときだけ「ランサムウェア利用あり」を添える。`stack` が単なる言及で自分に無関係そうなら除いてよい（全部除いたら `該当なし`）
- **依存の未解消**: `audit.findings` を repo ごとにまとめ、repo 内は KEV 掲載 → CVSS の高い順
  - `cvss` が null なら「CVSS 未採点」。`kev` が空なら KEV の行は出さない。`dev: true` は見出しの末尾に「（開発用依存）」を足す
  - 対処は `fix` と `advisories[0].range` に書かれていることだけを使う。npm: `fix` が true なら「`npm audit fix` で修正可」、オブジェクトなら「メジャー更新が必要（{name} {version}）」、false なら「修正版なし」。composer は修正版が出力に無いので「修正版は要確認」
  - 全体で9パッケージ以上あるときは、上位8までを詳しく書き、残りは「ほか N パッケージ: {名前の羅列}」の1行にする
  - `audit` が null（未実施）なら、`該当なし` ではなく `未実施（取得失敗）` と書く
- リンクは bare URL で書く

### 3. 出力
- 上の形の本文を最終出力にする。`errors` と `audit.errors` が空でなければ、末尾に `（取得失敗: ソース名）` を追記する（例: `audit: {repo}/composer（Docker 停止）`）
- 2つのセクションがどちらも `該当なし` でエラーも無いときは、本文は作らず `該当なし` とだけ出力する

## Notes
- 取得元は CISA KEV と composer / npm の audit のみ。KEV はプロファイルの `stack` のキーワードに該当するものだけで、ニュース・注意喚起の類は見ない
- 公開済みの脆弱性が依存に残っているかは audit が見る。直して lock ファイルを更新すれば、次回から自動で出なくなる（対応済みの記録は不要）
- CVSS: KEV は NVD API（キーなしのため 1 回の実行で最大 8 件、約 6.5 秒間隔。超過分や未採点は null）。audit は代表の脆弱性だけ GitHub Advisory API から取る（認証済みの `gh` を優先。無ければ未認証で 1 時間 60 回まで）
- composer の audit は `composer_runner` に従う（既定は Docker の `composer:latest` 一時コンテナ。`local` / `off` も可）、npm の audit はホストの npm（`--package-lock-only`）で実行する。どちらも読み取りのみで、lock ファイルや依存は書き換えない。`npm audit fix` は実行しない
- 監査の対象はプロファイルの `repos` の lock ファイル（`composer.lock` / `package-lock.json` があるものだけ）
- プロファイルの項目: `name`, `repos`（`name`・`path`）, `stack`, `kev_days`(1), `audit_min_severity`(high), `composer_runner`(docker), `nvd_max_per_run`(8)。括弧は既定値。新しい案件は `profiles/` に JSON を足し、タスク側でそのパスを渡す
