from rules import RA, GD, FD, validate_pattern


def make_off_blocks(max_len=8):
    blocks = []

    for length in range(2, max_len + 1):
        blocks.append([GD] * length)

        for fd_count in range(1, min(2, length - 1) + 1):
            gd_count = length - fd_count
            blocks.append([FD] * fd_count + [GD] * gd_count)

    return blocks


def fd_allowed_after_ra_block(ra_len, fd_count):
    if ra_len in (3, 4):
        return fd_count <= 2
    if ra_len == 5:
        return fd_count <= 1
    if ra_len == 6:
        return fd_count == 0
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
        if not (3 <= previous_block_length <= 6):
            return False

        if pattern[0] == RA:
            current_start_ra = starting_block_length(pattern, "RA")
            return previous_block_length + current_start_ra <= 6

        return True

    if previous_type == "OFF days":
        if not (2 <= previous_block_length <= 8):
            return False

        if pattern[0] in (GD, FD):
            current_start_off = starting_block_length(pattern, "OFF")
            return previous_block_length + current_start_off <= 8

        return True

    return True


def generate_all_patterns(
    num_days,
    previous_type=None,
    previous_block_length=0
):
    legal_patterns = []
    off_blocks = make_off_blocks()

    def backtrack(pattern, next_block_type, gd_used, fd_used, last_ra_len=None):
        if len(pattern) > num_days:
            return

        if gd_used > 8 or fd_used > 4:
            return

        if len(pattern) == num_days:
            if gd_used == 8 and fd_used == 4 and validate_pattern(pattern):
                if previous_type is None or validate_carryover(
                    pattern,
                    previous_type,
                    previous_block_length
                ):
                    legal_patterns.append(pattern.copy())
            return

        remaining = num_days - len(pattern)

        if next_block_type == "RA":
            for ra_len in range(3, 7):
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