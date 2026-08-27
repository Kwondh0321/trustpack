import json
import tempfile
import unittest
from pathlib import Path

from trustpack.core import ScanOptions, check_dependencies, check_forms, check_provenance, check_research, scan_repository
from trustpack.report import write_bundle


class TrustPackTests(unittest.TestCase):
    def test_dependency_and_community_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text(json.dumps({"dependencies": {"demo": "^1.2.0"}}), encoding="utf-8")
            report = scan_repository(root, ScanOptions(profile="release"))
            rules = {item["rule_id"] for item in report["findings"]}
            self.assertIn("TP101", rules)
            self.assertIn("TP201", rules)
            self.assertGreater(report["checks"][-1]["metrics"]["file_count"], 0)

    def test_exact_dependencies_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text(json.dumps({"dependencies": {"demo": "1.2.0"}}), encoding="utf-8")
            self.assertEqual(check_dependencies(root, "ko").findings, [])

    def test_research_detects_missing_seed_and_absolute_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "analysis.py").write_text("import random\nDATA='/Users/test/data.csv'\nprint(random.random())\n", encoding="utf-8")
            rules = {finding.rule_id for finding in check_research(root, "ko").findings}
            self.assertIn("TP302", rules)
            self.assertIn("TP303", rules)

    def test_form_privacy_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("<html><form><input name='email' required></form></html>", encoding="utf-8")
            rules = {finding.rule_id for finding in check_forms(root, "ko").findings}
            self.assertTrue({"TP401", "TP402", "TP403", "TP404"}.issubset(rules))

    def test_bundle_writes_korean_html(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            output = Path(directory) / "out"
            root.mkdir()
            (root / "README.md").write_text("# 예제", encoding="utf-8")
            report = scan_repository(root, ScanOptions(profile="release", lang="ko"))
            write_bundle(report, output)
            self.assertTrue((output / "trustpack.json").exists())
            self.assertIn("디지털 신뢰 증거", (output / "report.html").read_text(encoding="utf-8"))

    def test_shared_report_does_not_expose_absolute_target_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# 예제", encoding="utf-8")
            report = scan_repository(root, ScanOptions(profile="release"))
            self.assertEqual(report["target"]["path"], ".")
            self.assertNotIn(str(root), json.dumps(report, ensure_ascii=False))

    def test_previous_default_bundle_is_not_hashed_again(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generated = root / "trustpack-evidence"
            generated.mkdir()
            (generated / "trustpack.json").write_text("{}", encoding="utf-8")
            (root / "README.md").write_text("# 예제", encoding="utf-8")
            result = check_provenance(root, "ko")
            paths = {item["path"] for item in result.metrics["files"]}
            self.assertNotIn("trustpack-evidence/trustpack.json", paths)


if __name__ == "__main__":
    unittest.main()
