from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import SEVERITY_RANK, ScanOptions, scan_repository
from .i18n import translator
from .report import write_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="저장소의 신뢰·재현성·출처 증거를 하나의 번들로 만듭니다.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan", help="저장소를 검사하고 증거 번들을 생성합니다.")
    scan.add_argument("path", nargs="?", default=".", help="검사할 저장소 경로")
    scan.add_argument("--profile", choices=("full", "release", "research", "public-service"), default="full", help="검사 프로필")
    scan.add_argument("--output-dir", default="trustpack-evidence", help="결과 디렉터리")
    scan.add_argument("--config", type=Path, help="외부 검사기 어댑터 JSON 설정")
    scan.add_argument("--lang", choices=("ko", "en"), default="ko", help="보고서 언어(기본: 한국어)")
    scan.add_argument("--fail-on", choices=("none", "low", "medium", "high", "critical"), default="none", help="지정 심각도 이상이면 종료 코드 1")
    scan.add_argument("--json", action="store_true", help="요약을 표준 출력에 JSON으로 표시")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    t = translator(args.lang)
    try:
        report = scan_repository(Path(args.path), ScanOptions(profile=args.profile, lang=args.lang, config_path=args.config))
        output_dir = Path(args.output_dir).resolve()
        write_bundle(report, output_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    else:
        print(f"{t('scan_complete')} {report['summary']['score']}/100, findings={report['summary']['finding_count']}")
        print(t("report_written", path=output_dir))
    if args.fail_on != "none":
        threshold = SEVERITY_RANK[args.fail_on]
        if any(SEVERITY_RANK.get(item["severity"], 2) >= threshold for item in report["findings"]):
            return 1
    return 0

