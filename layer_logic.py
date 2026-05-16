from rules import RA
from utils import normalize_layer_sizes


def off_indexes_for_pattern(pattern):
    return [
        i for i, day in enumerate(pattern)
        if day != RA
    ]


def build_layer_layout(pattern, requirements, preferred_indexes, requested_sizes):
    final_sizes = normalize_layer_sizes(requested_sizes)
    off_indexes = off_indexes_for_pattern(pattern)
    preferred_in_bid = [
        i for i in preferred_indexes
        if i in off_indexes
    ]

    layers = {
        1: [],
        2: [],
        3: [],
        4: [],
        5: [],
        6: [],
    }

    layer_scores = {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
    }

    used_dates = set()

    def layer_has_room(layer_number):
        return len(layers[layer_number]) < final_sizes[layer_number]

    def add_date_to_layer(idx, layer_number):
        layers[layer_number].append(idx)
        layer_scores[layer_number] += requirements[idx]
        used_dates.add(idx)

    for idx in preferred_in_bid:
        for layer_number in range(1, 7):
            if layer_has_room(layer_number):
                add_date_to_layer(idx, layer_number)
                break

    remaining_dates = [
        idx for idx in off_indexes
        if idx not in used_dates
    ]

    remaining_dates = sorted(
        remaining_dates,
        key=lambda i: requirements[i],
        reverse=True
    )

    for idx in remaining_dates:
        available_layers = [
            layer_number
            for layer_number in range(1, 7)
            if layer_has_room(layer_number)
        ]

        if not available_layers:
            break

        best_layer = min(
            available_layers,
            key=lambda layer_number: (
                layer_scores[layer_number] / max(1, final_sizes[layer_number]),
                layer_number
            )
        )

        add_date_to_layer(idx, best_layer)

    for idx in off_indexes:
        if idx not in used_dates:
            for layer_number in range(1, 7):
                if layer_has_room(layer_number):
                    add_date_to_layer(idx, layer_number)
                    break

    layers[7] = off_indexes

    return layers, final_sizes
