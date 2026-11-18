import unittest

from docugosync.analyzer import analyze_snapshots
from docugosync.extractors import DocLine


class AnalyzerTests(unittest.TestCase):
    def test_renamed_flag(self):
        old = 'parser.add_argument("--old-mode")'
        new = 'parser.add_argument("--new-mode")'
        docs = [DocLine("README.md", 4, "Run with --old-mode to enable the mode.")]
        findings = analyze_snapshots({"app.py": old}, {"app.py": new}, docs)
        self.assertTrue(any(f.kind == "removed_or_renamed_flag" for f in findings))
        self.assertIn("--new-mode", findings[0].suggestion)

    def test_changed_default(self):
        old = "TIMEOUT = 30"
        new = "TIMEOUT = 60"
        docs = [DocLine("README.md", 8, "The TIMEOUT default is 30 seconds.")]
        findings = analyze_snapshots({"app.py": old}, {"app.py": new}, docs)
        self.assertTrue(any(f.kind == "changed_default" for f in findings))

    def test_new_undocumented_setting(self):
        old = "EXISTING = True"
        new = "EXISTING = True\nNEW_OPTION = False"
        docs = [DocLine("README.md", 1, "Configuration options are listed below.")]
        findings = analyze_snapshots({"app.py": old}, {"app.py": new}, docs)
        self.assertTrue(any(f.kind == "undocumented_configuration" for f in findings))


if __name__ == "__main__":
    unittest.main()
