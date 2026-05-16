from rules import (
    RA,
    GD,
    FD,
    REQUIRED_GD_DAYS,
    REQUIRED_FD_DAYS,
    MIN_RA_BLOCK,
    MAX_RA_BLOCK,
    MIN_OFF_BLOCK,
    MAX_OFF_BLOCK,
    MAX_FD_AFTER_SHORT_RA_BLOCK,
    MAX_FD_AFTER_FIVE_RA_BLOCK,
    MAX_FD_AFTER_SIX_RA_BLOCK,
    validate_pattern,
)


def make_off_blocks(max_len=MAX_OFF_BLOCK):
    blocks = []

    for length in range(MIN_OFF_BLOCK, max_len + 1):
        blocks.append([GD] * length)

        for fd_count in range(1, min(MAX_FD_AFTER_SHORT_RA_BLOCK, length - 1) + 1):
            gd_count = length - fd_count
            blocks.append([FD] * fd_count + [GD] * gd_count)

    return blocks


def fd_allowed_after_ra_block(ra_len, fd_count):
    if ra_len in (3, 4):
        return fd_count <= MAX_FD_AFTER_SHORT_RA_BLOCK
    if ra_len == 5:
        return fd_count <= MAX_FD_AFTER_FIVE_RA_BLOCK
    if ra_len == 6:
        return fd_count == MAX_FD_AFTER_SIX_RA_BLOCK
    return False


def starting_block_length(pattern, block_type):
    count = 0

    if block_type == "RA":
        for day in pattern:
            if day == RA:
                count += 1
            else:
                break

    if block_type == "OFF":
        for day in pattern:
            if day in (GD, FD):
                count += 1
            else:
                break

    return count


def validate_carryover(pattern, previous_type, previous_block_length):
    if not pattern:
        return False

    if previous_type == "ON days":
        if not (MIN_RA_BLOCK <= previous_block_length <= MAX_RA_BLOCK):
            return False

        if pattern[0] == RA:
            current_start_ra = starting_block_length(pattern, "RA")
            return previous_block_length + current_start_ra <= MAX_RA_BLOCK

        return True

    if previous_type == "OFF days":
        if not (MIN_OFF_BLOCK <= previous_block_length <= MAX_OFF_BLOCK):
            return False

        if pattern[0] in (GD, FD):
            current_start_off = starting_block_length(pattern, "OFF")
            return previous_block_length + current_start_off <= MAX_OFF_BLOCK

        return True

    return True


def off_day_key(pattern):
    return tuple(i for i, day in enumerate(pattern) if day != RA)


def unique_off_day_patterns(patterns):
    """
    Collapse duplicate bids that have the same 12 off dates.
    Keeps the first legal FD/GD assignment found for display.
    """
    seen = set()
    unique = []

    for pattern in patterns:
        key = off_day_key(pattern)

        if key not in seen:
            seen.add(key)
            unique.append(pattern)

    return unique


def generate_all_patterns(num_days, previous_type=None, previous_block_length=0):
    legal_patterns = []
    off_blocks = make_off_blocks()

    def backtrack(pattern, next_block_type, gd_used, fd_used, last_ra_len=None):
        if len(pattern) > num_days:
            return

        if gd_used > REQUIRED_GD_DAYS or fd_used > REQUIRED_FD_DAYS:
            return

        if len(pattern) == num_days:
            if gd_used == REQUIRED_GD_DAYS and fd_used == REQUIRED_FD_DAYS and validate_pattern(pattern):
                if previous_type is None or validate_carryover(
                    pattern,
                    previous_type,
                    previous_block_length
                ):
                    legal_patterns.append(pattern.copy())
            return

        remaining = num_days - len(pattern)

        if next_block_type == "RA":
            for ra_len in range(MIN_RA_BLOCK, MAX_RA_BLOCK + 1):
                if ra_len <= remaining:
                    backtrack(
                        pattern + [RA] * ra_len,
                        "OFF",
                        gd_used,
                        fd_used,
                        last_ra_len=ra_len
                    )

        else:
            for block in off_blocks:
                if len(block) > remaining:
                    continue

                fd_count = block.count(FD)
                gd_count = block.count(GD)

                if last_ra_len is not None:
                    if not fd_allowed_after_ra_block(last_ra_len, fd_count):
                        continue

                if len(pattern) == 0 and block[0] == FD:
                    continue

                backtrack(
                    pattern + block,
                    "RA",
                    gd_used + gd_count,
                    fd_used + fd_count,
                    last_ra_len=None
                )

    backtrack([], "RA", 0, 0)
    backtrack([], "OFF", 0, 0)

    return legal_patterns


def generate_unique_off_day_patterns(num_days, previous_type=None, previous_block_length=0):
    patterns = generate_all_patterns(
        num_days,
        previous_type=previous_type,
        previous_block_length=previous_block_length
    )

    return unique_off_day_patterns(patterns)


def filter_patterns_by_requested_off_dates(patterns, requested_indexes):
    if not requested_indexes:
        return patterns

    filtered = []

    for pattern in patterns:
        if all(
            0 <= idx < len(pattern) and pattern[idx] != RA
            for idx in requested_indexes
        ):
            filtered.append(pattern)

    return filtered
