from rules import RA


def rank_day_difficulty(requirements):
    sorted_days = sorted(
        range(len(requirements)),
        key=lambda i: requirements[i]
    )

    ranks = [0] * len(requirements)

    for rank, day_index in enumerate(sorted_days, start=1):
        ranks[day_index] = rank

    return ranks


def seniority_percentile(seniority_rank, total_reserves):
    seniority_rank = max(1, int(seniority_rank))
    total_reserves = max(1, int(total_reserves))

    if total_reserves == 1:
        return 0.0

    if seniority_rank > total_reserves:
        seniority_rank = total_reserves

    return (seniority_rank - 1) / (total_reserves - 1)


def off_indexes(pattern):
    return [i for i, day in enumerate(pattern) if day != RA]


def off_block_lengths(pattern):
    lengths = []
    i = 0

    while i < len(pattern):
        if pattern[i] != RA:
            count = 0
            while i < len(pattern) and pattern[i] != RA:
                count += 1
                i += 1
            lengths.append(count)
        else:
            i += 1

    return lengths


def weekend_off_count(pattern, dates):
    return sum(
        1 for i, day in enumerate(pattern)
        if day != RA and dates[i].weekday() in (5, 6)
    )


def weekday_off_count(pattern, dates):
    return sum(
        1 for i, day in enumerate(pattern)
        if day != RA and dates[i].weekday() in (0, 1, 2, 3, 4)
    )


def strategy_score_pattern(pattern, requirements, seniority_rank, total_reserves):
    """
    Used by Generate Bids as the default strategy ranking.

    Lower score = better strategic bid to REQUEST.
    """
    difficulty_ranks = rank_day_difficulty(requirements)
    seniority = seniority_percentile(seniority_rank, total_reserves)
    num_days = len(requirements)

    target_rank = 1 + ((1 - seniority) * (num_days - 1))

    ranks = [
        difficulty_ranks[i]
        for i, day in enumerate(pattern)
        if day != RA
    ]

    if not ranks:
        return 999999999

    average_rank = sum(ranks) / len(ranks)
    hardest_rank = max(ranks)

    score = 0
    score += abs(average_rank - target_rank) ** 2 * 100

    for rank in ranks:
        score += abs(rank - target_rank) ** 2

        if rank > target_rank:
            score += ((rank - target_rank) ** 3) * (1 + seniority * 25)

        if rank < target_rank:
            score += ((target_rank - rank) ** 2) * (1 - seniority) * 10

    score += hardest_rank * seniority * 20
    score -= average_rank * (1 - seniority) * 50

    return score


def sort_strategy_patterns(patterns, requirements, seniority_rank, total_reserves):
    return sorted(
        patterns,
        key=lambda pattern: strategy_score_pattern(
            pattern,
            requirements,
            seniority_rank,
            total_reserves
        )
    )

def sort_patterns_by_preference(
    patterns,
    requirements,
    seniority_rank,
    total_reserves,
    dates,
    preference
):
    """
    Sorting preferences are not legal rules.
    They only reorder already-legal unique off-day bids.
    """

    if preference == "Best chance / seniority strategy":
        return sort_strategy_patterns(
            patterns,
            requirements,
            seniority_rank,
            total_reserves
        )

    if preference == "Most weekends off":
        return sorted(
            patterns,
            key=lambda pattern: (
                -weekend_off_count(pattern, dates),
                strategy_score_pattern(pattern, requirements, seniority_rank, total_reserves)
            )
        )

    if preference == "Most weekdays off":
        return sorted(
            patterns,
            key=lambda pattern: (
                -weekday_off_count(pattern, dates),
                strategy_score_pattern(pattern, requirements, seniority_rank, total_reserves)
            )
        )

    if preference == "Longest off blocks":
        return sorted(
            patterns,
            key=lambda pattern: (
                -max(off_block_lengths(pattern), default=0),
                -sum(off_block_lengths(pattern)),
                strategy_score_pattern(pattern, requirements, seniority_rank, total_reserves)
            )
        )

    if preference == "Shortest off blocks":
        return sorted(
            patterns,
            key=lambda pattern: (
                max(off_block_lengths(pattern), default=0),
                sum(length ** 2 for length in off_block_lengths(pattern)),
                strategy_score_pattern(pattern, requirements, seniority_rank, total_reserves)
            )
        )

    return sort_strategy_patterns(
        patterns,
        requirements,
        seniority_rank,
        total_reserves
    )


def chance_label_for_displayed_order(result_rank, displayed_total):
    if displayed_total <= 0:
        return "Unknown", "No displayed bid comparison available."

    if displayed_total == 1:
        return "Most likely to be awarded", "This is the strongest displayed legal bid for the current inputs."

    percentile = result_rank / displayed_total

    if result_rank == 1:
        return "Most likely to be awarded", "This is the strongest displayed legal bid for the current inputs."
    elif percentile <= 0.25:
        return "Very likely to be awarded", "This is near the top of the displayed bid options."
    elif percentile <= 0.50:
        return "Likely to be awarded", "This is in the stronger half of the displayed bid options."
    elif percentile <= 0.75:
        return "Less likely to be awarded", "This is in the lower half of the displayed bid options."
    elif result_rank == displayed_total:
        return "Least likely to be awarded", "This is the weakest displayed bid option, though it may still be legal."
    else:
        return "Less likely to be awarded", "This is one of the less likely displayed bid options."
