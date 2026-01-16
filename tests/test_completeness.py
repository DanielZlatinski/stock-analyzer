import unittest

from core.models import CompletenessSection, DataQualityReport


class TestCompleteness(unittest.TestCase):
    def test_section_percent(self):
        section = CompletenessSection(name="prices")
        section.add(True)
        section.add(False)
        self.assertEqual(section.percent, 50.0)

    def test_report_overall_percent(self):
        report = DataQualityReport()
        report.section("prices").add(True)
        report.section("fundamentals").add(False)
        self.assertEqual(report.overall_percent, 50.0)


if __name__ == "__main__":
    unittest.main()
