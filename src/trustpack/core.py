from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .i18n import translator

SEVERITY_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__",
    ".pytest_cache", "trustpack-evidence", ".trustpack",
}
DATA_EXTENSIONS = {".csv", ".tsv", ".jsonl", ".parquet", ".xlsx", ".sav"}
SOURCE_EXTENSIONS = {".py", ".js", ".mjs", ".ts", ".tsx", ".ipynb"}
PERSONAL_HINTS = {
    "name", "email", "phone", "mobile", "address", "birth", "resident", "ssn",
    "이름", "성명", "이메일", "전화", "휴대폰", "주소", "생년", "주민",
}


@dataclass
class Finding:
    check: str
    rule_id: str
    severity: str
    title: str
    message: str
    path: Optional[str] = None
    line: Optional[int] = None
    evidence: Optional[str] = None
    remediation: Optional[str] = None


@dataclass
class CheckResult:
    check: str
    title: str
    status: str
    findings: List[Finding] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanOptions:
    profile: str = "full"
    lang: str = "ko"
    config_path: Optional[Path] = None
    external_timeout: int = 60


def _iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _finding(check: str, rule_id: str, severity: str, title: str, message: str, **kwargs: Any) -> Finding:
    return Finding(check=check, rule_id=rule_id, severity=severity, title=title, message=message, **kwargs)


def check_community(root: Path, lang: str) -> CheckResult:
    t = translator(lang)
    files = {_relative(path, root).lower() for path in _iter_files(root)}
    findings: List[Finding] = []
    checks: Sequence[Tuple[str, bool, str, str]] = (
        ("TP101", any(name.startswith("readme") for name in files), "medium", "missing_readme"),
        ("TP102", any(Path(name).name.startswith(("license", "copying")) for name in files), "high", "missing_license"),
        ("TP103", any(name.startswith(".github/workflows/") and name.endswith((".yml", ".yaml")) for name in files), "medium", "missing_ci"),
        ("TP104", any("test" in Path(name).name or name.startswith(("tests/", "test/")) for name in files), "medium", "missing_tests"),
        ("TP105", any(Path(name).name.startswith("contributing") for name in files), "low", "missing_contributing"),
        ("TP106", any(Path(name).name.startswith("security") for name in files), "medium", "missing_security"),
    )
    for rule_id, passed, severity, message_key in checks:
        if not passed:
            findings.append(_finding("community", rule_id, severity, t("community_title"), t(message_key)))
    return CheckResult("community", t("community_title"), "pass" if not findings else "review", findings, {"signals_checked": len(checks)})


def _exact_version(value: str) -> bool:
    value = value.strip()
    return bool(re.fullmatch(r"(?:v)?\d+(?:\.\d+){1,3}(?:[-+][0-9A-Za-z.-]+)?", value))


def check_dependencies(root: Path, lang: str) -> CheckResult:
    t = translator(lang)
    findings: List[Finding] = []
    package_path = root / "package.json"
    if package_path.exists():
        try:
            package = json.loads(package_path.read_text(encoding="utf-8"))
            for group in ("dependencies", "devDependencies", "optionalDependencies"):
                for name, value in package.get(group, {}).items():
                    if not _exact_version(str(value)):
                        findings.append(_finding(
                            "dependencies", "TP201", "medium", t("dependencies_title"),
                            t("unpinned_dependency", name=name, value=value), path="package.json",
                            evidence=f"{group}.{name}={value}",
                        ))
        except (OSError, json.JSONDecodeError):
            pass
    requirements = root / "requirements.txt"
    if requirements.exists():
        for line_number, raw in enumerate(requirements.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            value = raw.strip()
            if not value or value.startswith(("#", "-")):
                continue
            if "==" not in value or any(token in value for token in (">=", "<=", "~=", "!=", " @ ")):
                name = re.split(r"[<>=!~@\s]", value, maxsplit=1)[0]
                findings.append(_finding(
                    "dependencies", "TP202", "medium", t("dependencies_title"),
                    t("unpinned_dependency", name=name, value=value), path="requirements.txt", line=line_number,
                ))
    return CheckResult("dependencies", t("dependencies_title"), "pass" if not findings else "review", findings, {"unpinned": len(findings)})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_provenance(root: Path, lang: str) -> CheckResult:
    t = translator(lang)
    entries = []
    total_bytes = 0
    for path in sorted(_iter_files(root)):
        size = path.stat().st_size
        total_bytes += size
        entries.append({"path": _relative(path, root), "bytes": size, "sha256": _sha256(path)})
    metrics: Dict[str, Any] = {"file_count": len(entries), "total_bytes": total_bytes, "files": entries}
    git_dir = root / ".git"
    if git_dir.exists():
        try:
            metrics["git_head"] = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True, timeout=10
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            metrics["git_head"] = None
    return CheckResult("provenance", t("provenance_title"), "pass", [], metrics)


def _source_texts(root: Path) -> Iterable[Tuple[Path, str]]:
    for path in _iter_files(root):
        if any(part in {"test", "tests", "fixtures"} for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() not in SOURCE_EXTENSIONS or path.suffix.lower() == ".ipynb":
            continue
        if path.stat().st_size > 2 * 1024 * 1024:
            continue
        yield path, path.read_text(encoding="utf-8", errors="replace")


def check_research(root: Path, lang: str) -> CheckResult:
    t = translator(lang)
    findings: List[Finding] = []
    randomized = False
    seeded = False
    absolute_pattern = re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\\\)")
    for path, text in _source_texts(root):
        rel = _relative(path, root)
        if re.search(r"^\s*(?:import|from)\s+(?:random|numpy|torch|tensorflow)\b|(?:require\(|from\s+)[\"'](?:random|numpy|torch|tensorflow)", text, re.M):
            randomized = True
        if re.search(r"\b(seed|random_state|manual_seed|set_seed)\s*[=(]", text):
            seeded = True
        for match in absolute_pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            source_line = text.splitlines()[line - 1]
            if "re.compile" in source_line or "absolute_pattern" in source_line:
                continue
            findings.append(_finding("research", "TP302", "high", t("research_title"), t("absolute_path"), path=rel, line=line))
            break
    for notebook in (path for path in _iter_files(root) if path.suffix.lower() == ".ipynb"):
        try:
            payload = json.loads(notebook.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        counts = [cell.get("execution_count") for cell in payload.get("cells", []) if cell.get("cell_type") == "code" and cell.get("execution_count") is not None]
        if counts != sorted(counts) or len(counts) != len(set(counts)):
            findings.append(_finding("research", "TP301", "high", t("research_title"), t("notebook_order"), path=_relative(notebook, root)))
        notebook_text = json.dumps(payload, ensure_ascii=False)
        randomized = randomized or bool(re.search(r"\b(random|numpy\.random|np\.random|torch|tensorflow)\b", notebook_text))
        seeded = seeded or bool(re.search(r"\b(seed|random_state|manual_seed|set_seed)\s*[=(]", notebook_text))
        if absolute_pattern.search(notebook_text):
            findings.append(_finding("research", "TP302", "high", t("research_title"), t("absolute_path"), path=_relative(notebook, root)))
    if randomized and not seeded:
        findings.append(_finding("research", "TP303", "high", t("research_title"), t("missing_seed")))
    data_files = [path for path in _iter_files(root) if path.suffix.lower() in DATA_EXTENSIONS]
    doc_names = {_relative(path, root).lower() for path in _iter_files(root)}
    has_data_docs = any(any(token in name for token in ("data_card", "dataset", "data-source", "data_source", "citation.cff")) for name in doc_names)
    if data_files and not has_data_docs:
        findings.append(_finding("research", "TP304", "medium", t("research_title"), t("missing_data_source"), evidence=f"{len(data_files)} data files"))
    return CheckResult("research", t("research_title"), "pass" if not findings else "review", findings, {"data_files": len(data_files)})


class _FormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.has_lang = False
        self.has_title = False
        self.forms: List[Dict[str, Any]] = []
        self._form: Optional[Dict[str, Any]] = None

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        values = {key.lower(): (value or "") for key, value in attrs}
        if tag == "html" and values.get("lang"):
            self.has_lang = True
        elif tag == "title":
            self.has_title = True
        elif tag == "form":
            self._form = {"method": values.get("method", "get").lower(), "purpose": values.get("data-purpose", ""), "personal": [], "required_personal": []}
            self.forms.append(self._form)
        elif tag in {"input", "textarea", "select"} and self._form is not None:
            signature = " ".join(values.get(key, "") for key in ("name", "id", "autocomplete", "placeholder", "aria-label")).lower()
            personal = any(hint in signature for hint in PERSONAL_HINTS)
            if personal:
                self._form["personal"].append(signature)
                if "required" in values:
                    self._form["required_personal"].append(signature)

    def handle_endtag(self, tag: str) -> None:
        if tag == "form":
            self._form = None


def check_forms(root: Path, lang: str) -> CheckResult:
    t = translator(lang)
    findings: List[Finding] = []
    html_files = [path for path in _iter_files(root) if path.suffix.lower() in {".html", ".htm"}]
    for path in html_files:
        parser = _FormParser()
        try:
            parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        rel = _relative(path, root)
        if not parser.has_lang:
            findings.append(_finding("forms", "TP401", "medium", t("forms_title"), t("missing_lang"), path=rel))
        if not parser.has_title:
            findings.append(_finding("forms", "TP402", "low", t("forms_title"), t("missing_title"), path=rel))
        for index, form in enumerate(parser.forms, 1):
            if form["personal"] and form["method"] == "get":
                findings.append(_finding("forms", "TP403", "high", t("forms_title"), t("get_personal_form"), path=rel, evidence=f"form #{index}"))
            if form["required_personal"] and not form["purpose"]:
                findings.append(_finding("forms", "TP404", "medium", t("forms_title"), t("missing_form_purpose"), path=rel, evidence=f"form #{index}"))
    return CheckResult("forms", t("forms_title"), "pass" if not findings else "review", findings, {"html_files": len(html_files)})


def _normalize_external(name: str, payload: Any, lang: str) -> List[Finding]:
    t = translator(lang)
    raw_findings = payload.get("findings", []) if isinstance(payload, dict) else payload if isinstance(payload, list) else []
    findings = []
    for index, item in enumerate(raw_findings, 1):
        if not isinstance(item, dict):
            continue
        findings.append(Finding(
            check=f"external:{name}",
            rule_id=str(item.get("rule_id") or item.get("rule") or item.get("id") or f"EXT{index:03d}"),
            severity=str(item.get("severity", "medium")).lower(),
            title=str(item.get("title") or t("external_title")),
            message=str(item.get("message") or item.get("description") or json.dumps(item, ensure_ascii=False)),
            path=item.get("path") or item.get("file"),
            line=item.get("line"),
            evidence=item.get("evidence"),
            remediation=item.get("remediation") or item.get("suggestion"),
        ))
    return findings


def run_external_checks(root: Path, config: Dict[str, Any], options: ScanOptions) -> List[CheckResult]:
    t = translator(options.lang)
    results = []
    for adapter in config.get("adapters", []):
        name = str(adapter.get("name", "unnamed"))
        command = adapter.get("command")
        if not isinstance(command, list) or not command:
            continue
        try:
            completed = subprocess.run(
                [str(part).replace("{root}", str(root)) for part in command], cwd=root,
                capture_output=True, text=True, timeout=options.external_timeout, check=False,
            )
            payload = json.loads(completed.stdout)
            findings = _normalize_external(name, payload, options.lang)
            status = "pass" if completed.returncode == 0 and not findings else "review"
            results.append(CheckResult(f"external:{name}", f"{t('external_title')}: {name}", status, findings, {"exit_code": completed.returncode}))
        except subprocess.TimeoutExpired as exc:
            finding = _finding(f"external:{name}", "TPE01", "high", t("external_title"), t("external_failed", detail=f"timeout {exc.timeout}s"))
            results.append(CheckResult(f"external:{name}", f"{t('external_title')}: {name}", "error", [finding]))
        except (OSError, json.JSONDecodeError) as exc:
            finding = _finding(f"external:{name}", "TPE02", "high", t("external_title"), t("external_failed", detail=str(exc)))
            results.append(CheckResult(f"external:{name}", f"{t('external_title')}: {name}", "error", [finding]))
    return results


PROFILE_CHECKS = {
    "release": ("community", "dependencies", "provenance"),
    "research": ("community", "dependencies", "research", "provenance"),
    "public-service": ("community", "dependencies", "forms", "provenance"),
    "full": ("community", "dependencies", "research", "forms", "provenance"),
}


def scan_repository(root: Path, options: Optional[ScanOptions] = None) -> Dict[str, Any]:
    options = options or ScanOptions()
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(translator(options.lang)("invalid_root", path=root))
    config: Dict[str, Any] = {}
    if options.config_path:
        config = json.loads(options.config_path.read_text(encoding="utf-8"))
    functions = {
        "community": check_community,
        "dependencies": check_dependencies,
        "research": check_research,
        "forms": check_forms,
        "provenance": check_provenance,
    }
    selected = PROFILE_CHECKS.get(options.profile, PROFILE_CHECKS["full"])
    results = [functions[name](root, options.lang) for name in selected]
    results.extend(run_external_checks(root, config, options))
    findings = [asdict(finding) for result in results for finding in result.findings]
    score = max(0, 100 - sum({"low": 2, "medium": 5, "high": 12, "critical": 25}.get(item["severity"], 5) for item in findings))
    return {
        "schema_version": "1.0",
        "tool": {"name": "trustpack", "version": "0.1.0"},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "language": options.lang,
        "profile": options.profile,
        # 공유 가능한 증거 번들에 개발자 컴퓨터의 절대경로를 기록하지 않는다.
        "target": {"name": root.name, "path": "."},
        "summary": {
            "score": score,
            "finding_count": len(findings),
            "by_severity": {severity: sum(1 for item in findings if item["severity"] == severity) for severity in SEVERITY_RANK},
        },
        "checks": [asdict(result) for result in results],
        "findings": findings,
    }
