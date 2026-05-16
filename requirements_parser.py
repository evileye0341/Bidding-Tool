import re


DEFAULT_REQUIREMENT = 100


def numbers_from_line(line):
    return [
        int(token)
        for token in re.findall(r"\d+", line)
    ]


def day_requirement_from_numbers(numbers):
    if len(numbers) >= 4 and numbers[0] > 31 and 1 <= numbers[1] <= 12:
        return numbers[2], numbers[3]

    if len(numbers) >= 3 and 1 <= numbers[0] <= 12 and 1 <= numbers[1] <= 31:
        return numbers[1], numbers[2]

    if len(numbers) >= 2:
        return numbers[0], numbers[1]

    return None


def parse_reserve_requirements_detailed(text, dates, default=DEFAULT_REQUIREMENT):
    requirements = [default for _ in dates]
    warnings = []
    parsed_days = set()

    if not text.strip():
        return requirements, warnings, parsed_days

    valid_days = {current_date.day for current_date in dates}
    parsed = {}
    pending_day = None

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()

        if not line:
            continue

        numbers = numbers_from_line(line)

        if len(numbers) >= 2:
            day_number, required = day_requirement_from_numbers(numbers)
            pending_day = None
        elif len(numbers) == 1:
            number = numbers[0]

            if pending_day is None:
                if 1 <= number <= 31:
                    pending_day = number
                else:
                    warnings.append(
                        f"Line {line_number} was ignored because {number} is not a valid day number."
                    )
                continue

            day_number, required = pending_day, number
            pending_day = None
        else:
            continue

        if day_number not in valid_days:
            warnings.append(
                f"Line {line_number} day {day_number} is outside this bid period and was ignored."
            )
            continue

        parsed[day_number] = required
        parsed_days.add(day_number)

    if pending_day is not None:
        warnings.append(
            f"Day {pending_day} did not have a matching requirement value and was ignored."
        )

    for i, current_date in enumerate(dates):
        if current_date.day in parsed:
            requirements[i] = parsed[current_date.day]

    return requirements, warnings, parsed_days


def parse_reserve_requirements(text, dates, default=DEFAULT_REQUIREMENT):
    requirements, warnings, _ = parse_reserve_requirements_detailed(
        text,
        dates,
        default
    )

    return requirements, warnings

