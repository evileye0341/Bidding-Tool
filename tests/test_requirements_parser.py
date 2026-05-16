import unittest
from datetime import date

from requirements_parser import (
    DEFAULT_REQUIREMENT,
    parse_reserve_requirements,
    parse_reserve_requirements_detailed,
)
from utils import date_range


class RequirementsParserTests(unittest.TestCase):
    def test_empty_text_returns_defaults(self):
        dates = date_range(date(2026, 6, 1), date(2026, 6, 3))

        requirements, warnings = parse_reserve_requirements("", dates)

        self.assertEqual([DEFAULT_REQUIREMENT] * 3, requirements)
        self.assertEqual([], warnings)

    def test_parses_day_requirement_pairs_on_same_line(self):
        dates = date_range(date(2026, 6, 1), date(2026, 6, 3))

        requirements, warnings = parse_reserve_requirements(
            "1 313\n2 353\n3 342",
            dates
        )

        self.assertEqual([313, 353, 342], requirements)
        self.assertEqual([], warnings)

    def test_parses_day_requirement_pairs_on_separate_lines(self):
        dates = date_range(date(2026, 6, 1), date(2026, 6, 3))

        requirements, warnings = parse_reserve_requirements(
            "1\n313\n2\n353\n3\n342",
            dates
        )

        self.assertEqual([313, 353, 342], requirements)
        self.assertEqual([], warnings)

    def test_ignores_text_between_day_and_requirement(self):
        dates = date_range(date(2026, 6, 19), date(2026, 6, 20))

        requirements, warnings = parse_reserve_requirements(
            "19\nOFF\nPrefer\n232\n20\n292",
            dates
        )

        self.assertEqual([232, 292], requirements)
        self.assertEqual([], warnings)

    def test_warns_about_out_of_period_day(self):
        dates = date_range(date(2026, 6, 1), date(2026, 6, 3))

        requirements, warnings = parse_reserve_requirements(
            "4 400",
            dates
        )

        self.assertEqual([DEFAULT_REQUIREMENT] * 3, requirements)
        self.assertEqual(1, len(warnings))

    def test_parses_slash_dates(self):
        dates = date_range(date(2026, 6, 1), date(2026, 6, 2))

        requirements, warnings = parse_reserve_requirements(
            "6/1 313\n6/2 353",
            dates
        )

        self.assertEqual([313, 353], requirements)
        self.assertEqual([], warnings)

    def test_detailed_parser_reports_pasted_day_even_when_value_matches_default(self):
        dates = date_range(date(2026, 6, 1), date(2026, 6, 2))

        requirements, warnings, parsed_days = parse_reserve_requirements_detailed(
            "1 100",
            dates
        )

        self.assertEqual([100, DEFAULT_REQUIREMENT], requirements)
        self.assertEqual([], warnings)
        self.assertEqual({1}, parsed_days)


if __name__ == "__main__":
    unittest.main()
