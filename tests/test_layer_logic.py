import unittest

from layer_logic import build_layer_layout, off_indexes_for_pattern
from rules import GD, RA


class LayerLogicTests(unittest.TestCase):
    def test_off_indexes_for_pattern(self):
        pattern = [RA, GD, GD, RA, GD]

        self.assertEqual([1, 2, 4], off_indexes_for_pattern(pattern))

    def test_build_layer_layout_uses_all_off_dates_once_in_layers_one_to_six(self):
        pattern = [GD] * 12 + [RA] * 18
        requirements = list(range(1, 31))
        requested_sizes = {
            1: 2,
            2: 2,
            3: 2,
            4: 2,
            5: 2,
        }

        layers, final_sizes = build_layer_layout(
            pattern,
            requirements,
            preferred_indexes=[],
            requested_sizes=requested_sizes
        )

        placed = []

        for layer_number in range(1, 7):
            placed.extend(layers[layer_number])
            self.assertEqual(final_sizes[layer_number], len(layers[layer_number]))

        self.assertEqual(list(range(12)), sorted(placed))
        self.assertEqual(list(range(12)), layers[7])

    def test_preferred_dates_are_placed_first(self):
        pattern = [GD] * 12 + [RA] * 18
        requirements = [100] * 30
        requested_sizes = {
            1: 1,
            2: 1,
            3: 1,
            4: 1,
            5: 1,
        }

        layers, _ = build_layer_layout(
            pattern,
            requirements,
            preferred_indexes=[8, 3, 5],
            requested_sizes=requested_sizes
        )

        self.assertEqual([8], layers[1])
        self.assertEqual([3], layers[2])
        self.assertEqual([5], layers[3])


if __name__ == "__main__":
    unittest.main()
