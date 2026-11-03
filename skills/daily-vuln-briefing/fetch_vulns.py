#!/usr/bin/env python3
"""自分に関係する脆弱性を集めて JSON で標準出力する（daily-vuln-briefing 用）。状態ファイルは持たない。

  python3 fetch_vulns.py --config profiles/example.json

案件ごとの値（対象リポジトリ・スタック・しきい値）は --config のプロファイル JSON で渡す（profiles/example.json 参照）。

情報源は2つ。
- kev:   CISA KEV（悪用が確認された脆弱性）のうち、直近 kev_days 日に追加され、プロファイルの stack に該当するもの。
         実行の間隔より長く取るので、同じ項目が数回出る。
- audit: repos の今の依存を composer audit / npm audit にかけ、残っている脆弱性のうち
         audit_min_severity 以上のもの。直せば次回から自然に消える。
         監査するのは各リポジトリに lock ファイル（composer.lock / package-lock.json）がある側だけ。

composer は composer_runner（docker: composer:latest の一時コンテナ / local: ホストの composer / off）、
npm はホストの npm（--package-lock-only）で実行する。どちらも lock ファイルや依存は書き換えない。
取得に失敗した情報源は errors に入る（Docker が止まっていれば composer 側だけ失敗する）。
"""
import argparse
import json
import re
import shutil
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
UA = "Mozilla/5.0 (vuln-briefing)"

# NVD API（キーなしは 30 秒あたり 5 リクエスト）。KEV の CVSS にだけ使う
NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId="
NVD_INTERVAL = 6.5

SEV = {"low": 1, "medium": 2, "high": 3, "critical": 4}

# 以下は load_config() がプロファイルから埋める（未指定の項目は DEFAULTS）
DEFAULTS = {
    "kev_days": 1,  # 朝夕2回実行 + スリープ取りこぼしの吸収
    "audit_min_severity": "high",
    "composer_runner": "docker",
    "nvd_max_per_run": 8,
}
CFG = {}
REPOS = {}
STACK_RE = None


def load_config(path):
    """プロファイル JSON を読み、設定を検証してグローバルに反映する。"""
    global CFG, REPOS, STACK_RE
    path = Path(path).expanduser().resolve()
    raw = json.loads(path.read_text())
    CFG = {**DEFAULTS, **raw}
    if CFG["audit_min_severity"] not in SEV:
        raise ValueError(f"audit_min_severity は {sorted(SEV)} のどれか: {CFG['audit_min_severity']}")
    if CFG["composer_runner"] not in ("docker", "local", "off"):
        raise ValueError(f"composer_runner は docker / local / off のどれか: {CFG['composer_runner']}")
    CFG.setdefault("name", path.stem)
    CFG.setdefault("repos", [])
    CFG.setdefault("stack", [])
    # path は ~ と絶対パスに対応。相対パスはプロファイルの場所が基準
    REPOS = {r["name"]: (path.parent / Path(r["path"]).expanduser()).resolve() for r in CFG["repos"]}
    if CFG["stack"]:
        STACK_RE = re.compile(
            r"(?<![a-z0-9])(" + "|".join(re.escape(k.lower()) for k in CFG["stack"]) + r")(?![a-z0-9])", re.I)


def get(url):
    # macOS の python3 は証明書ストアが未設定のことがあるため、システムの curl を使う
    return subprocess.run(
        ["curl", "-fsSL", "-m", "30", "-A", UA, url],
        check=True, capture_output=True,
    ).stdout


# ---------- CISA KEV ----------

_nvd = {"calls": 0, "last": 0.0}


def nvd_cvss(cve_id):
    """NVD から CVSS を取る。上限超過・失敗・未採点なら None。"""
    if _nvd["calls"] >= CFG["nvd_max_per_run"]:
        return None
    wait = NVD_INTERVAL - (time.time() - _nvd["last"])
    if _nvd["calls"] and wait > 0:
        time.sleep(wait)
    _nvd["calls"] += 1
    _nvd["last"] = time.time()
    try:
        metrics = json.loads(get(NVD_URL + cve_id))["vulnerabilities"][0]["cve"]["metrics"]
    except Exception:
        return None
    for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30"):  # 新しい版を優先
        for m in metrics.get(key, []):
            d = m.get("cvssData", {})
            if "baseScore" in d:
                return {"score": d["baseScore"], "severity": d.get("baseSeverity"), "version": d.get("version")}
    return None


_kev_catalog = {}


def kev_catalog():
    if not _kev_catalog:
        _kev_catalog.update(json.loads(
            get("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json")))
    return _kev_catalog


def kev_url(cve_id):
    return f"https://www.cisa.gov/known-exploited-vulnerabilities-catalog?field_cve={cve_id}"


def github_api(path):
    # 認証済みの gh があればそれを使う（未認証 curl は 1 時間 60 回までの制限がある）
    if shutil.which("gh"):
        r = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            return json.loads(r.stdout)
    return json.loads(get("https://api.github.com/" + path))


def ghsa_cvss(ghsa_id=None, cve_id=None):
    """GitHub Advisory API から CVSS を取る。失敗・未採点なら None。"""
    try:
        a = github_api(f"advisories/{ghsa_id}") if ghsa_id else github_api(f"advisories?cve_id={cve_id}")[0]
    except Exception:
        return None
    sev = a.get("cvss_severities") or {}
    for key, ver in (("cvss_v4", "4.0"), ("cvss_v3", "3.x")):  # 未採点は score 0.0 で返ることがあるので 0 は「なし」
        score = (sev.get(key) or {}).get("score")
        if score:
            return {"score": score, "severity": a.get("severity"), "version": ver}
    score = (a.get("cvss") or {}).get("score")
    return {"score": score, "severity": a.get("severity"), "version": None} if score else None


def kev():
    since = (datetime.now(timezone.utc) - timedelta(days=CFG["kev_days"])).strftime("%Y-%m-%d")
    out = []
    if STACK_RE is None:
        return out  # stack が空なら KEV は見ない
    for v in kev_catalog()["vulnerabilities"]:
        if v["dateAdded"] < since:
            continue
        text = f'{v["vendorProject"]} {v["product"]} {v["vulnerabilityName"]}'
        hits = sorted({m.group(1).lower() for m in STACK_RE.finditer(text)})
        if not hits:
            continue
        out.append({
            "id": v["cveID"],
            "title": f'{v["vendorProject"]} {v["product"]}: {v["vulnerabilityName"]}',
            "summary": v["shortDescription"], "action": v["requiredAction"],
            "url": f'https://nvd.nist.gov/vuln/detail/{v["cveID"]}',
            "kev_url": kev_url(v["cveID"]),
            "stack": hits, "date": v["dateAdded"],
            "ransomware": v.get("knownRansomwareCampaignUse") == "Known",
            "cvss": nvd_cvss(v["cveID"]),
        })
    return out


# ---------- 依存の監査（composer audit / npm audit） ----------

def load_inventory():
    """導入中のバージョン表示用。{"composer": {name: [{repo, version, dev}]}, "npm": {...}}"""
    inv = {"composer": {}, "npm": {}}
    for repo, root in REPOS.items():
        try:
            lock = json.loads((root / "composer.lock").read_text())
            for key, dev in (("packages", False), ("packages-dev", True)):
                for p in lock.get(key, []):
                    inv["composer"].setdefault(p["name"].lower(), []).append(
                        {"repo": repo, "version": p["version"].lstrip("v"), "dev": dev})
        except Exception:
            pass  # 読めなければ installed が空になるだけ。audit 側のエラーで分かる
        try:
            lock = json.loads((root / "package-lock.json").read_text())
            for path, p in lock.get("packages", {}).items():
                if not path or p.get("link") or "version" not in p:
                    continue
                name = path.rsplit("node_modules/", 1)[-1].lower()
                inv["npm"].setdefault(name, []).append(
                    {"repo": repo, "version": p["version"], "dev": bool(p.get("dev"))})
        except Exception:
            pass
    return inv


def run_json(cmd, cwd=None):
    # audit は脆弱性があると終了コード 1 を返すため、終了コードではなく出力の中身で成否を判断する
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=180)
    try:
        return json.loads(r.stdout)
    except ValueError:
        raise RuntimeError(((r.stderr or r.stdout).strip().splitlines() or ["出力なし"])[-1][:200])


def composer_audit(root):
    args = ["composer", "audit", "--locked", "--format=json", "--no-interaction"]
    if CFG["composer_runner"] == "local":
        d = run_json(args, cwd=str(root))
    else:
        d = run_json(["docker", "run", "--rm",
                      "-v", f"{root}/composer.json:/app/composer.json:ro",
                      "-v", f"{root}/composer.lock:/app/composer.lock:ro",
                      "-w", "/app", "composer:latest"] + args)
    adv = d.get("advisories") or {}
    out = []
    for pkg, items in (adv.items() if isinstance(adv, dict) else []):
        for a in items:
            out.append({"package": pkg.lower(), "id": a.get("cve") or a.get("advisoryId"), "cve": a.get("cve"),
                        "severity": (a.get("severity") or "").lower(), "title": a.get("title"),
                        "range": a.get("affectedVersions"), "url": a.get("link")})
    return out


def npm_audit(root):
    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("npm が PATH に無い")
    d = run_json([npm, "audit", "--json", "--package-lock-only"], cwd=str(root))
    out, seen = [], set()
    for name, v in (d.get("vulnerabilities") or {}).items():
        for x in v.get("via", []):
            if not isinstance(x, dict):
                continue  # 文字列は「他のパッケージ経由」の印。実体は経由先の側で拾う
            pkg, ghsa = (x.get("name") or name).lower(), (x.get("url") or "").rsplit("/", 1)[-1]
            if (pkg, ghsa) in seen:
                continue
            seen.add((pkg, ghsa))
            out.append({"package": pkg, "id": ghsa, "cve": None,
                        "severity": (x.get("severity") or "").lower(), "title": x.get("title"),
                        "range": x.get("range"), "fix": v.get("fixAvailable"),
                        "url": x.get("url"), "ghsa": ghsa})
    return out


def audit(inv):
    errors, raw = [], []
    for repo, root in REPOS.items():
        targets = [("composer", "composer.lock", composer_audit), ("npm", "package-lock.json", npm_audit)]
        for eco, lock, fn in targets:
            if eco == "composer" and CFG["composer_runner"] == "off":
                continue
            if not (root / lock).exists():
                continue  # その言語を使っていないリポジトリ
            try:
                raw += [dict(r, repo=repo, ecosystem=eco) for r in fn(root)]
            except Exception as e:
                errors.append(f"audit {repo}/{eco}: {type(e).__name__}: {e}")

    kev_ids = set()
    try:
        kev_ids = {v["cveID"] for v in kev_catalog()["vulnerabilities"]}
    except Exception:
        pass  # KEV 掲載の印が付かないだけ

    groups, low = {}, 0
    for r in raw:
        r["severity"] = {"moderate": "medium"}.get(r["severity"], r["severity"])
        if SEV.get(r["severity"], 0) < SEV[CFG["audit_min_severity"]] and r["cve"] not in kev_ids:
            low += 1
            continue
        groups.setdefault((r["repo"], r["ecosystem"], r["package"]), []).append(r)

    findings = []
    for (repo, eco, pkg), rs in groups.items():
        rs.sort(key=lambda r: (-SEV.get(r["severity"], 0), r["id"] or ""))
        locked = [e for e in inv.get(eco, {}).get(pkg, []) if e["repo"] == repo]
        findings.append({
            "repo": repo, "ecosystem": eco, "package": pkg,
            "installed": sorted({e["version"] for e in locked}),
            "dev": bool(locked) and all(e["dev"] for e in locked),
            "severity": rs[0]["severity"], "count": len(rs),
            "kev": sorted({r["cve"] for r in rs if r["cve"] in kev_ids}),
            "fix": rs[0].get("fix"),
            "advisories": [{k: r.get(k) for k in ("id", "cve", "severity", "title", "range", "url")} for r in rs[:5]],
        })
        f = findings[-1]
        f["kev_urls"] = [kev_url(c) for c in f["kev"]]
        top = rs[0]  # 代表（最も深刻なもの）の CVSS だけ引く
        f["cvss"] = ghsa_cvss(ghsa_id=top.get("ghsa")) if top.get("ghsa") else (
            ghsa_cvss(cve_id=top["cve"]) if top.get("cve") else None)
    findings.sort(key=lambda f: (not f["kev"], -SEV.get(f["severity"], 0), f["repo"], f["package"]))
    return {"findings": findings, "below_min_severity": low, "errors": errors}


def main():
    ap = argparse.ArgumentParser(description="脆弱性ブリーフィング用の情報を JSON で出力する")
    ap.add_argument("--config", required=True, help="プロファイル JSON のパス（profiles/example.json 参照）")
    load_config(ap.parse_args().config)
    errors = []
    kev_items, audit_result = [], None
    try:
        kev_items = kev()
    except Exception as e:  # 1ソースの失敗で全体を止めない
        errors.append(f"CISA KEV: {type(e).__name__}: {e}")
    try:
        audit_result = audit(load_inventory())
    except Exception as e:
        errors.append(f"audit: {type(e).__name__}: {e}")
    print(json.dumps({"profile": CFG["name"], "repos": list(REPOS), "errors": errors, "kev": kev_items, "audit": audit_result}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
