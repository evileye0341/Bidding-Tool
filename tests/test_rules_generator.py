import unittest

from generator import (
    filter_patterns_by_requested_off_dates,
    generate_all_patterns,
    generate_unique_off_day_patterns,
    validate_carryover,
)
from rules import FD, GD, RA, validate_pattern, validate_pattern_with_reasons


VALID_30_DAY_PATTERN = (
    [RA, RA, RA]
    + [FD, FD, GD, GD]
    + [RA, RA, RA]
    + [FD, FD, GD, GD]
    + [RA, RA, RA]
    + [GD, GD]
    + [RA, RA, RA]
    + [GD, GD]
    + [RA, RA, RA, RA, RA, RA]
)


class RulesTests(unittest.TestCase):
    def test_valid_pattern_passes(self):
        self.assertTrue(validate_pattern(VALID_30_DAY_PATTERN))

    def test_exact_gd_count_is_required(self):
        pattern = VALID_30_DAY_PATTERN.copy()
        pattern[5] = RA

        is_valid, reasons = validate_pattern_with_reasons(pattern)

        self.assertFalse(is_valid)
        self.assertTrue(any("exactly 8 GD" in reason for reason in reasons))

    def test_exact_fd_count_is_required(self):
        pattern = VALID_30_DAY_PATTERN.copy()
        pattern[3] = GD

        is_valid, reasons = validate_pattern_with_reasons(pattern)

        self.assertFalse(is_valid)
        self.assertTrue(any("exactly 4 FD" in reason for reason in reasons))

    def test_fd_cannot_follow_gd_in_same_off_block(self):
        pattern = VALID_30_DAY_PATTERN.copy()
        pattern[3:7] = [FD, GD, FD, GD]

        is_valid, reasons = validate_pattern_with_reasons(pattern)

        self.assertFalse(is_valid)
        self.assertTrue(any("comes after GD" in reason for reason in reasons))

    def test_on_block_bounds_are_enforced(self):
        pattern = VALID_30_DAY_PATTERN.copy()
        pattern[-7:] = [RA] * 7

        is_valid, reasons = validate_pattern_with_reasons(pattern)

        self.assertFalse(is_valid)
        self.assertTrue(any("ON blocks must" in reason for reason in reasons))

    def test_off_block_bounds_are_enforced(self):
        pattern = VALID_30_DAY_PATTERN.copy()
        pattern[3:7] = [GD, RA, RA, RA]

        is_valid, reasons = validate_pattern_with_reasons(pattern)

        self.assertFalse(is_valid)
        self.assertTrue(any("OFF blocks must" in reason for reason in reasons))


class CarryoverTests(unittest.TestCase):
    def test_on_carryover_allows_total_up_to_six(self):
        self.assertTrue(
            validate_carryover(VALID_30_DAY_PATTERN, "ON days", 3)
        )

    def test_on_carryover_rejects_total_over_six(self):
        self.assertFalse(
            validate_carryover(VALID_30_DAY_PATTERN, "ON days", 4)
        )

    def test_off_carryover_allows_total_up_to_eight(self):
        pattern = [GD, GD, GD, GD] + [RA, RA, RA]

        self.assertTrue(
            validate_carryover(pattern, "OFF days", 4)
        )

    def test_off_carryover_rejects_total_over_eight(self):
        pattern = [GD, GD, GD, GD] + [RA, RA, RA]

        self.assertFalse(
            validate_carryover(pattern, "OFF days", 5)
        )


class GeneratorTests(unittest.TestCase):
    def test_generation_baseline_counts_for_thirty_day_period(self):
        exact_patterns = generate_all_patterns(
            30,
            previous_type="ON days",
            previous_block_length=3
        )
        unique_patterns = generate_unique_off_day_patterns(
            30,
            previous_type="ON days",
            previous_block_length=3
        )

        self.assertEqual(10289, len(exact_patterns))
        self.assertEqual(2483, len(unique_patterns))

    def test_generation_baseline_counts_for_thirty_one_day_period(self):
        exact_patterns = generate_all_patterns(
            31,
            previous_type="ON days",
            previous_block_length=3
        )
        unique_patterns = generate_unique_off_day_patterns(
            31,
            previous_type="ON days",
            previous_block_length=3
        )

        self.assertEqual(13558, len(exact_patterns))
        self.assertEqual(3033, len(unique_patterns))

    def test_requested_days_filter_requires_each_requested_day_off(self):
        patterns = [
            [RA, GD, GD],
            [GD, GD, RA],
            [RA, RA, GD],
        ]

        filtered = filter_patterns_by_requested_off_dates(patterns, [1])

        self.assertEqual([[RA, GD, GD], [GD, GD, RA]], filtered)


if __name__ == "__main__":
    unittest.main()
