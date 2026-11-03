# daily-vuln-briefing

CISA KEV と、リポジトリの依存の audit（composer / npm）から、プロファイルに関係する脆弱性をまとめる。状態ファイルは持たない。Slack などへの投稿は scheduled task 側で決める。
Claude が自動で起動しない設定（`disable-model-invocation: true`）で、scheduled task から呼ぶ前提。

## 前提

| 必要なもの | 用途 | 無いとき |
|---|---|---|
| `python3`、`curl` | スクリプト、取得 | 動かない |
| `npm` | npm audit | npm 側が取得失敗になる |
| Docker | composer audit（`composer_runner: docker`） | composer 側が取得失敗になる |
| `gh`（ログイン済み・任意） | 依存の CVSS 取得 | 未認証 curl に切り替わる（1時間60回まで） |

対象リポジトリに `composer.lock` / `package-lock.json` があること（無い言語は監査しない）。

## セットアップ

1. `profiles/example.json` を `profiles/<案件名>.json` にコピーし、`repos` と `stack` を書き換える。
2. 動作を確認する。JSON が出れば成功。
   ```bash
   python3 fetch_vulns.py --config profiles/<案件名>.json
   ```
3. [task-template.md](task-template.md) をもとに scheduled task を作る。差し替えるのはタスク名・プロファイルのパス・投稿先だけ。

## プロファイルの項目

| 項目 | 必須 | 既定値 | 内容 |
|---|---|---|---|
| `name` | | ファイル名 | 見出しに出る呼び名 |
| `repos` | ✔ | なし | 監査するリポジトリ。`name` と `path` |
| `stack` | ✔ | なし | KEV を絞るキーワード |
| `kev_days` | | 1 | KEV の追加日を何日前まで見るか |
| `audit_min_severity` | | high | audit で通知する最低の深刻度（low / medium / high / critical） |
| `composer_runner` | | docker | docker / local / off |
| `nvd_max_per_run` | | 8 | 1回の実行で KEV の CVSS を引く上限 |

- `path` は `~`、絶対パス、プロファイルからの相対パスが使える。
- `stack` はベンダー名・製品名・脆弱性名との単語一致。広い語（`aws` など）は無関係な製品にも当たる。
- 外部案件の `name` は、案件名を含めない呼び名（`my-project` など）にする。

## 困ったとき

- 取得失敗は出力の `errors` に出る（Docker 停止など）。
- 両セクションとも `該当なし` で投稿されないのは正常な動作。

## 詳細

手順は [SKILL.md](SKILL.md)、通知の形式は [template.md](template.md)。
