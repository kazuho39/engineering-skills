# 🛡️ 脆弱性ブリーフィング {profile} {YYYY-MM-DD} {朝|夕}

## 🚨 KEV
### {CVE-ID} {製品名}
{何が起きるか} / 対処: {action}
CVSS {score}（{severity}） / 🔒ランサムウェア利用あり
NVD: {url}
KEV: {kev_url}

（該当が無いときは、見出しの下に `該当なし` とだけ書く）

## 📦 依存の未解消
### {repo}
#### {package} {installed} — {severity} {count}件
CVSS {score}（{severity}）
代表: {title}
対処: {対処}
詳細: {advisories[0].url}
🔴 KEV 掲載（悪用確認済み）: {kev_urls}

ほか N パッケージ: {名前の羅列}
high 未満は {below_min_severity} 件

（該当が無いときは、見出しの下に `該当なし` とだけ書く）
