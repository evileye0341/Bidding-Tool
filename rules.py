RA = "RA"
GD = "GD"
FD = "FD"


def is_off(day):
    return day in (GD, FD)


def count_days(pattern, day_type):
    return pattern.count(day_type)


def validate_pattern_with_reasons(pattern):
    reasons = []

    if not pattern:
        reasons.append("Pattern is empty.")
        return False, reasons

    if count_days(pattern, GD) != 8:
        reasons.append(f"Must have exactly 8 GD. This pattern has {count_days(pattern, GD)}.")

    if count_days(pattern, FD) != 4:
        reasons.append(f"Must have exactly 4 FD. This pattern has {count_days(pattern, FD)}.")

    if pattern[0] == FD:
        reasons.append("The first day of the contractual month cannot be FD.")

    for i, day in enumerate(pattern):
        if day == FD:
            if i == 0:
                continue
            if pattern[i - 1] not in (RA, FD):
                reasons.append(f"FD on day {i + 1} must follow RA or FD.")

    i = 0
    while i < len(pattern):
        if pattern[i] == RA:
            start = i
            count = 0
            while i < len(pattern) and pattern[i] == RA:
                count += 1
                i += 1

            if not (3 <= count <= 6):
                reasons.append(
                    f"ON block from day {start + 1} to day {i} is {count} days. ON blocks must be 3–6 days."
                )
        else:
            i += 1

    i = 0
    while i < len(pattern):
        if is_off(pattern[i]):
            start = i
            block = []
            while i < len(pattern) and is_off(pattern[i]):
                block.append(pattern[i])
                i += 1

            if not (2 <= len(block) <= 8):
                reasons.append(
                    f"OFF block from day {start + 1} to day {i} is {len(block)} days. OFF blocks must be 2–8 days."
                )

            if FD in block:
                if GD not in block:
                    reasons.append(
                        f"OFF block from day {start + 1} to day {i} has FD but no GD."
                    )

                seen_gd = False
                for offset, d in enumerate(block):
                    if d == GD:
                        seen_gd = True
                    if d == FD and seen_gd:
                        reasons.append(
                            f"FD on day {start + offset + 1} comes after GD in the same OFF block."
                        )
        else:
            i += 1

    if is_off(pattern[-1]):
        i = len(pattern) - 1
        block = []
        while i >= 0 and is_off(pattern[i]):
            block.append(pattern[i])
            i -= 1

        if FD in block:
            reasons.append("The final OFF block reaches the last day of the month and cannot contain FD.")

    # FD allowed based on previous RA block
    i = 0
    last_ra_len = None

    while i < len(pattern):
        if pattern[i] == RA:
            count = 0
            while i < len(pattern) and pattern[i] == RA:
                count += 1
                i += 1
            last_ra_len = count

        elif is_off(pattern[i]):
            block = []
            while i < len(pattern) and is_off(pattern[i]):
                block.append(pattern[i])
                i += 1

            fd_count = block.count(FD)

            if fd_count > 0 and last_ra_len is not None:
                if last_ra_len in (3, 4) and fd_count > 2:
                    reasons.append(f"After {last_ra_len} RA days, only up to 2 FD are allowed.")
                elif last_ra_len == 5 and fd_count > 1:
                    reasons.append("After 5 RA days, only up to 1 FD is allowed.")
                elif last_ra_len == 6 and fd_count > 0:
                    reasons.append("After 6 RA days, FD is not allowed. The next off day must be GD.")
        else:
            i += 1

    return len(reasons) == 0, reasons


def validate_pattern(pattern):
    is_valid, _ = validate_pattern_with_reasons(pattern)
    return is_valid