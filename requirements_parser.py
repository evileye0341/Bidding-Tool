import re


DEFAULT_REQUIREMENT = 100


def numbers_from_line(line):
    return [
        int(token)
        for token in re.findall(r"\d+", line)
    ]


def requirement_key_from_numbers(numbers):
    if len(numbers) >= 4 and numbers[0] > 31 and 1 <= numbers[1] <= 12:
        return ("date", numbers[1], numbers[2]), numbers[3]

    if len(numbers) >= 3 and 1 <= numbers[0] <= 12 and 1 <= numbers[1] <= 31:
        return ("date", numbers[0], numbers[1]), numbers[2]

    if len(numbers) >= 2:
        return ("day", numbers[0]), numbers[1]

    return None


def resolve_requirement_key(key, date_to_index, day_to_indexes):
    key_type = key[0]

    if key_type == "date":
        _, month_number, day_number = key
        return date_to_index.get((month_number, day_number))

    _, day_number = key
    matching_indexes = day_to_indexes.get(day_number, [])

    if len(matching_indexes) == 1:
        return matching_indexes[0]

    return None


def parse_reserve_requirements_detailed(text, dates, default=DEFAULT_REQUIREMENT):
    requirements = [default for _ in dates]
    warnings = []
    parsed_days = set()

    if not text.strip():
        return requirements, warnings, parsed_days

    date_to_index = {
        (current_date.month, current_date.day): i
        for i, current_date in enumerate(dates)
    }
    day_to_indexes = {}

    for i, current_date in enumerate(dates):
        day_to_indexes.setdefault(current_date.day, []).append(i)

    parsed = {}
    pending_day = None

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()

        if not line:
            continue

        numbers = numbers_from_line(line)

        if len(numbers) >= 2:
            requirement_key, required = requirement_key_from_numbers(numbers)
            pending_day = None
        elif len(numbers) == 1:
            number = numbers[0]

            if pending_day is None:
                if 1 <= number <= 31:
                    pending_day = ("day", number)
                else:
                    warnings.append(
                        f"Line {line_number} was ignored because {number} is not a valid day number."
                    )
                continue

            requirement_key, required = pending_day, number
            pending_day = None
        else:
            continue

        date_index = resolve_requirement_key(
            requirement_key,
            date_to_index,
            day_to_indexes
        )

        if date_index is None:
            label = (
                f"{requirement_key[1]}/{requirement_key[2]}"
                if requirement_key[0] == "date"
                else f"day {requirement_key[1]}"
            )
            warnings.append(
                f"Line {line_number} {label} is outside this bid period or ambiguous and was ignored."
            )
            continue

        parsed[date_index] = required
        parsed_days.add(dates[date_index].day)

    if pending_day is not None:
        warnings.append(
            f"Day {pending_day[1]} did not have a matching requirement value and was ignored."
        )

    for i, required in parsed.items():
        requirements[i] = required

    return requirements, warnings, parsed_days


def parse_reserve_requirements(text, dates, default=DEFAULT_REQUIREMENT):
    requirements, warnings, _ = parse_reserve_requirements_detailed(
        text,
        dates,
        default
    )

    return requirements, warnings
