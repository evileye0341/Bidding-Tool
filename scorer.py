from rules import RA


def rank_day_difficulty(requirements):
    """
    Higher reserve requirement = harder day to hold off.

    Returns:
    - 1 = easiest day off
    - num_days = hardest day off
    """

    sorted_days = sorted(
        range(len(requirements)),
        key=lambda i: requirements[i]
    )

    ranks = [0] * len(requirements)

    for rank, day_index in enumerate(sorted_days, start=1):
        ranks[day_index] = rank

    return ranks


def seniority_percentile(seniority_rank, total_reserves):
    """
    0.0 = most senior
    1.0 = most junior
    """

    seniority_rank = max(1, int(seniority_rank))
    total_reserves = max(1, int(total_reserves))

    if total_reserves == 1:
        return 0.0

    if seniority_rank > total_reserves:
        seniority_rank = total_reserves

    return (seniority_rank - 1) / (total_reserves - 1)


def strategy_score_pattern(pattern, requirements, seniority_rank, total_reserves):
    """
    Used by the Generate Bids tool.

    Lower score = better strategic bid to REQUEST.

    This is preference/strategy based:
    - More senior users can aim for harder/high-value days off.
    - More junior users are pushed toward easier/more realistic days.
    """

    difficulty_ranks = rank_day_difficulty(requirements)
    seniority = seniority_percentile(seniority_rank, total_reserves)
    num_days = len(requirements)

    # Most senior target = hardest days.
    # Most junior target = easiest days.
    target_rank = 1 + ((1 - seniority) * (num_days - 1))

    off_ranks = [
        difficulty_ranks[i]
        for i, day in enumerate(pattern)
        if day != RA
    ]

    if not off_ranks:
        return 999999999

    average_rank = sum(off_ranks) / len(off_ranks)
    hardest_rank = max(off_ranks)

    score = 0

    # Main strategy: match the bid's overall difficulty to the user's seniority.
    score += abs(average_rank - target_rank) ** 2 * 100

    for rank in off_ranks:
        # Penalize days far from the strategic target.
        score += abs(rank - target_rank) ** 2

        # Junior users get punished heavily for asking too hard.
        if rank > target_rank:
            score += ((rank - target_rank) ** 3) * (1 + seniority * 25)

        # Senior users should not be shown only easy bids.
        if rank < target_rank:
            score += ((target_rank - rank) ** 2) * (1 - seniority) * 10

    # Very junior users should avoid one-off very hard days.
    score += hardest_rank * seniority * 20

    # Senior users should favor stronger/harder bids.
    score -= average_rank * (1 - seniority) * 50

    return score


def award_score_pattern(pattern, requirements, seniority_rank, total_reserves):
    """
    Used by the Manual Checker.

    Lower score = mathematically easier/stronger bid to be AWARDED.

    This is not about what a senior person might want.
    It measures raw award strength:
    - Easy days are always easier to win.
    - Hard days are always harder to win.
    - Junior seniority makes hard days more damaging.
    """

    difficulty_ranks = rank_day_difficulty(requirements)
    seniority = seniority_percentile(seniority_rank, total_reserves)

    score = 0

    for i, day in enumerate(pattern):
        if day == RA:
            continue

        day_rank = difficulty_ranks[i]

        # Base difficulty for everyone.
        score += day_rank

        # Junior penalty for hard days.
        score += (day_rank ** 2) * seniority

        # Extra penalty for very junior users on the hardest days.
        score += (day_rank ** 3) * (seniority ** 2) * 0.05

    return score


def sort_strategy_patterns(patterns, requirements, seniority_rank, total_reserves):
    """
    Sorts bids for the Generate Bids tool.
    """

    return sorted(
        patterns,
        key=lambda pattern: strategy_score_pattern(
            pattern,
            requirements,
            seniority_rank,
            total_reserves
        )
    )


def sort_award_patterns(patterns, requirements, seniority_rank, total_reserves):
    """
    Sorts bids for the Manual Checker.
    """

    return sorted(
        patterns,
        key=lambda pattern: award_score_pattern(
            pattern,
            requirements,
            seniority_rank,
            total_reserves
        )
    )


def chance_label_for_displayed_order(result_rank, displayed_total):
    """
    Used for generated bid results.

    This describes where a bid sits among the bids currently displayed.
    """

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