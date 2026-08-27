from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict


def write_bundle(report: Dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "trustpack.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    language = report.get("language", "ko")
    ko = language == "ko"
    labels = {
        "title": "TrustPack 디지털 신뢰 증거" if ko else "TrustPack Digital Trust Evidence",
        "score": "신뢰 준비 점수" if ko else "Trust readiness score",
        "findings": "검토 항목" if ko else "Findings",
        "path": "위치" if ko else "Location",
        "none": "발견된 검토 항목이 없습니다." if ko else "No review findings were detected.",
        "generated": "생성 시각" if ko else "Generated",
        "severity": "심각도" if ko else "Severity",
    }
    rows = []
    for finding in report["findings"]:
        location = finding.get("path") or "-"
        if finding.get("line"):
            location += f":{finding['line']}"
        rows.append(
            "<tr>"
            f"<td><span class='severity {html.escape(finding['severity'])}'>{html.escape(finding['severity'].upper())}</span></td>"
            f"<td><strong>{html.escape(finding['rule_id'])}</strong><br>{html.escape(finding['message'])}</td>"
            f"<td>{html.escape(location)}</td>"
            "</tr>"
        )
    body = "".join(rows) if rows else f"<tr><td colspan='3'>{labels['none']}</td></tr>"
    page = f"""<!doctype html>
<html lang="{html.escape(language)}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{labels['title']}</title><style>
body{{font-family:system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 20px;color:#172033;background:#f7f8fb}}
header,.card{{background:white;border:1px solid #dfe3ea;border-radius:14px;padding:24px;margin-bottom:18px}}h1{{margin-top:0}}
.score{{font-size:2.8rem;font-weight:800;color:#17594a}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:12px;border-bottom:1px solid #e7e9ee;text-align:left;vertical-align:top}}
.severity{{font-size:.75rem;font-weight:800;padding:4px 8px;border-radius:999px;background:#e9edf5}}.high,.critical{{background:#ffe0df;color:#8e1913}}.medium{{background:#fff0c2;color:#6c4e00}}
</style></head><body><header><h1>{labels['title']}</h1><p>{html.escape(report['target']['name'])}</p>
<div class="score">{report['summary']['score']}/100</div><p>{labels['score']}</p><small>{labels['generated']}: {html.escape(report['generated_at'])}</small></header>
<section class="card"><h2>{labels['findings']} ({report['summary']['finding_count']})</h2><table><thead><tr><th>{labels['severity']}</th><th>{labels['findings']}</th><th>{labels['path']}</th></tr></thead><tbody>{body}</tbody></table></section>
</body></html>"""
    (output_dir / "report.html").write_text(page, encoding="utf-8")
