from datetime import timedelta


def date_range(start_date, end_date):
    dates = []
    current = start_date

    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)

    return dates


def pattern_to_blocks(pattern):
    if not pattern:
        return []

    blocks = []
    current_type = pattern[0]
    count = 1

    for day in pattern[1:]:
        if day == current_type:
            count += 1
        else:
            blocks.append((current_type, count))
            current_type = day
            count = 1

    blocks.append((current_type, count))
    return blocks


def format_pattern_compact(pattern):
    blocks = pattern_to_blocks(pattern)

    return " / ".join(
        f"{count}{day_type}" for day_type, count in blocks
    )