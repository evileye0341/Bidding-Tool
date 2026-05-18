from datetime import timedelta

from rules import TOTAL_OFF_DAYS


def date_range(start_date, end_date):
    dates = []
    current = start_date

    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)

    return dates


def normalize_layer_sizes(requested_sizes):
    """
    Layers 1-5 are user adjustable.
    Layer 6 automatically becomes whatever is left so Layers 1-6 total 12.
    Layer 7 is locked and always contains all 12 dates.
    """

    final_sizes = {}

    used = 0

    for layer in range(1, 6):
        size = int(requested_sizes.get(layer, 0))

        if size < 0:
            size = 0

        if size > TOTAL_OFF_DAYS:
            size = TOTAL_OFF_DAYS

        final_sizes[layer] = size
        used += size

    remaining = TOTAL_OFF_DAYS - used

    if remaining < 0:
        remaining = 0

    final_sizes[6] = remaining

    return final_sizes


