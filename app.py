import streamlit as st
from datetime import date, timedelta

from generator import (
    generate_all_patterns,
    generate_unique_off_day_patterns,
    filter_patterns_by_requested_off_dates,
)

from scorer import (
    sort_patterns_by_preference,
    chance_label_for_displayed_order,
)

from rules import RA
from utils import date_range


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Reserve Bid Finder",
    page_icon="📅",
    layout="wide"
)

st.markdown(
    """
    <style>
    div.stButton > button[kind="primary"] {
        background-color: #1f77ff !important;
        border-color: #1f77ff !important;
        color: white !important;
    }

    div.stButton > button[kind="secondary"] {
        background-color: white !important;
        border-color: #dddddd !important;
        color: black !important;
    }

    div.stButton > button {
        min-height: 95px;
        white-space: pre-line;
        border-radius: 10px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Reserve Bid Finder")
st.write("Generate legal reserve bids based on GD, FD, and RA rules.")


# =========================================================
# RESET APP
# =========================================================

def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()


# =========================================================
# DATE HELPERS
# =========================================================

def first_day_next_month():
    today = date.today()

    if today.month == 12:
        return date(today.year + 1, 1, 1)

    return date(today.year, today.month + 1, 1)


def last_day_same_month(start):
    if start.month == 12:
        next_month = date(start.year + 1, 1, 1)
    else:
        next_month = date(start.year, start.month + 1, 1)

    return next_month - timedelta(days=1)


# =========================================================
# CALENDAR HELPERS
# =========================================================

def toggle_requested_day(idx):
    key = f"requested_{idx}"
    st.session_state[key] = not st.session_state.get(key, False)


def format_date_list(dates, indexes):
    if not indexes:
        return "blank"

    return ", ".join(
        dates[i].strftime("%b %d")
        for i in indexes
    )


# =========================================================
# REQUEST OFF CALENDAR
# =========================================================

def reserve_request_calendar_grid(dates, requirements):
    selected_indexes = []

    weekday_headers = st.columns(7)

    for col, label in zip(
        weekday_headers,
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    ):
        col.markdown(f"**{label}**")

    start_weekday = dates[0].weekday()

    cells = [None] * start_weekday + list(range(len(dates)))

    while len(cells) % 7 != 0:
        cells.append(None)

    for week_start in range(0, len(cells), 7):

        cols = st.columns(7)

        for i in range(7):

            idx = cells[week_start + i]

            with cols[i]:

                if idx is None:
                    st.write("")
                    continue

                current_date = dates[idx]

                selected_key = f"requested_{idx}"

                if selected_key not in st.session_state:
                    st.session_state[selected_key] = False

                selected = st.session_state[selected_key]

                button_label = (
                    f"{current_date.strftime('%b %d')}\n"
                    f"{current_date.strftime('%a')}\n"
                    f"Req: {requirements[idx]}"
                )

                if st.button(
                    button_label,
                    key=f"day_button_{idx}",
                    type="primary" if selected else "secondary",
                    use_container_width=True
                ):
                    toggle_requested_day(idx)
                    st.rerun()

                if st.session_state[selected_key]:
                    selected_indexes.append(idx)

    return selected_indexes


# =========================================================
# RENDER BID CALENDAR
# =========================================================

def render_bid_calendar(dates, pattern, requirements=None):
    weekday_headers = st.columns(7)

    for col, label in zip(
        weekday_headers,
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    ):
        col.markdown(f"**{label}**")

    start_weekday = dates[0].weekday()

    cells = [None] * start_weekday + list(range(len(dates)))

    while len(cells) % 7 != 0:
        cells.append(None)

    for week_start in range(0, len(cells), 7):

        cols = st.columns(7)

        for i in range(7):

            idx = cells[week_start + i]

            with cols[i]:

                if idx is None:
                    st.write("")
                    continue

                current_date = dates[idx]
                day = pattern[idx]

                if day == RA:
                    bg = "#ffffff"
                    border = "#dddddd"
                    weight = "normal"
                else:
                    bg = "#ffe680"
                    border = "#d6a800"
                    weight = "bold"

                req_line = ""

                if requirements is not None:
                    req_line = f"<br><small>Req: {requirements[idx]}</small>"

                st.markdown(
                    f"""
                    <div style="
                        border: 2px solid {border};
                        border-radius: 10px;
                        padding: 10px;
                        margin-bottom: 8px;
                        min-height: 90px;
                        background-color: {bg};
                        color: #000000;
                    ">
                        <strong>{current_date.strftime('%b %d')}</strong><br>
                        {current_date.strftime('%a')}<br>
                        <span style="font-weight:{weight};">{day}</span>
                        {req_line}
                    </div>
                    """,
                    unsafe_allow_html=True
                )


# =========================================================
# SEND TO LAYER BUILDER
# =========================================================

def send_bid_to_layer_builder(
    pattern,
    preferred_indexes,
    requirements
):
    st.session_state["layer_bid_pattern"] = pattern
    st.session_state["layer_preferred_indexes"] = preferred_indexes
    st.session_state["layer_requirements"] = requirements


# =========================================================
# NORMALIZE LAYER SIZES
# =========================================================

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

        if size > 12:
            size = 12

        final_sizes[layer] = size
        used += size

    remaining = 12 - used

    if remaining < 0:
        remaining = 0

    final_sizes[6] = remaining

    return final_sizes


# =========================================================
# 7 LAYER BUILDER
# =========================================================

def build_suggested_layers(
    dates,
    pattern,
    requirements,
    preferred_indexes
):
    st.header("7-Layer Bid Builder")

    off_indexes = [
        i for i, day in enumerate(pattern)
        if day != RA
    ]

    if len(off_indexes) != 12:
        st.error(
            "This tool expects a final bid with exactly 12 off days."
        )
        return

    preferred_in_bid = [
        i for i in preferred_indexes
        if i in off_indexes
    ]

    nonpreferred = [
        i for i in off_indexes
        if i not in preferred_in_bid
    ]

    st.write("Layer 7 will always be the full 12-day bid.")

    st.write(
        f"Final bid off days: "
        f"**{format_date_list(dates, off_indexes)}**"
    )

    ordered_priority_dates = []

    # =====================================================
    # PREFERRED DATE PRIORITY
    # =====================================================

    if preferred_in_bid:

        st.subheader("Preferred Date Priority")

        st.write(
            "Choose the order of importance for your preferred dates."
        )

        available_priority_labels = [
            dates[i].strftime("%b %d")
            for i in preferred_in_bid
        ]

        for priority_number in range(len(preferred_in_bid)):

            already_selected = [
                dates[idx].strftime("%b %d")
                for idx in ordered_priority_dates
            ]

            remaining_options = [
                label
                for label in available_priority_labels
                if label not in already_selected
            ]

            selected_label = st.selectbox(
                f"Priority #{priority_number + 1}",
                remaining_options,
                key=f"priority_select_{priority_number}"
            )

            for idx in preferred_in_bid:

                if dates[idx].strftime("%b %d") == selected_label:

                    if idx not in ordered_priority_dates:
                        ordered_priority_dates.append(idx)

    else:

        st.info(
            "No preferred dates were selected. "
            "Layers will auto-fill easiest dates first."
        )

        # =====================================================
    # LAYER SIZE CONTROLS
    # =====================================================

    st.subheader("Layer Sizes")

    st.write(
        "Enter requested sizes for Layers 1-5. "
        "Layer 6 automatically becomes whatever is left so Layers 1-6 always use all 12 dates. "
        "Layer 7 is locked and always shows the full 12-day bid."
    )

    requested_sizes = {}

    for layer_number in range(1, 6):

        requested_sizes[layer_number] = st.number_input(
            f"Layer {layer_number} requested size",
            min_value=0,
            max_value=12,
            value=2,
            step=1,
            key=f"layer_size_{layer_number}"
        )

    final_sizes = normalize_layer_sizes(requested_sizes)

    st.write(f"**Layer 6 auto-calculated size:** {final_sizes[6]}")
    st.write("**Layer 7 locked size:** 12")

    st.write(
        "**Actual Layer Sizes:** "
        + " / ".join(
            f"L{layer}: {final_sizes[layer]}"
            for layer in range(1, 7)
        )
        + " / L7: 12 locked"
    )

    # =====================================================
    # SORT DATES
    # =====================================================

    sorted_remaining_dates = sorted(
        nonpreferred,
        key=lambda i: requirements[i]
    )

    ordered_dates = []

    # Priority dates first
    for idx in ordered_priority_dates:

        if idx not in ordered_dates:
            ordered_dates.append(idx)

    # Then easiest remaining dates
    for idx in sorted_remaining_dates:

        if idx not in ordered_dates:
            ordered_dates.append(idx)

    # Safety: make sure all 12 off dates are included exactly once.
    for idx in off_indexes:
        if idx not in ordered_dates:
            ordered_dates.append(idx)

    ordered_dates = ordered_dates[:12]

    # =====================================================
    # BUILD LAYERS
    # =====================================================

    layers = {}

    cursor = 0

    for layer_number in range(1, 7):

        size = final_sizes[layer_number]

        layer = ordered_dates[cursor:cursor + size]

        layers[layer_number] = layer

        cursor += size

    # Layer 7 always full bid
    layers[7] = off_indexes

    # =====================================================
    # DISPLAY
    # =====================================================

    st.subheader("Suggested 7-Layer Bid Layout")

    for layer_number in range(1, 8):

        st.write(
            f"**Layer {layer_number}:** "
            f"{format_date_list(dates, layers[layer_number])}"
        )

    st.caption(
        "Layers 1-6 always use all 12 dates exactly once. "
        "Layer 7 always contains the full 12-day bid. "
        "Preferred dates are placed first in the user-selected priority order. "
        "Remaining dates are filled from easiest-to-award to hardest-to-award."
    )


# =========================================================
# MANUAL CHECKER
# =========================================================

def manual_off_calendar_checker(
    dates,
    previous_type,
    previous_block_length,
    requirements
):
    st.header("Manual Legality Checker")

    st.write(
        "Click dates to mark them as off."
    )

    selected_indexes = []

    weekday_headers = st.columns(7)

    for col, label in zip(
        weekday_headers,
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    ):
        col.markdown(f"**{label}**")

    start_weekday = dates[0].weekday()

    cells = [None] * start_weekday + list(range(len(dates)))

    while len(cells) % 7 != 0:
        cells.append(None)

    for week_start in range(0, len(cells), 7):

        cols = st.columns(7)

        for i in range(7):

            idx = cells[week_start + i]

            with cols[i]:

                if idx is None:
                    st.write("")
                    continue

                current_date = dates[idx]

                key = f"manual_off_{idx}"

                if key not in st.session_state:
                    st.session_state[key] = False

                selected = st.session_state[key]

                status = "OFF" if selected else "RA"

                button_label = (
                    f"{current_date.strftime('%b %d')}\n"
                    f"{current_date.strftime('%a')}\n"
                    f"{status}"
                )

                if st.button(
                    button_label,
                    key=f"manual_day_button_{idx}",
                    type="primary" if selected else "secondary",
                    use_container_width=True
                ):
                    st.session_state[key] = not st.session_state[key]
                    st.rerun()

                if st.session_state[key]:
                    selected_indexes.append(idx)

    selected_count = len(selected_indexes)

    st.write(f"Selected off days: **{selected_count} / 12**")

    if selected_count < 12:
        st.info(
            f"Select {12 - selected_count} more off day(s)."
        )
        return

    if selected_count > 12:
        st.error(
            "A legal bid must have exactly 12 off days."
        )
        return

    with st.spinner("Checking legality..."):

        all_legal_patterns = generate_unique_off_day_patterns(
            len(dates),
            previous_type=previous_type,
            previous_block_length=previous_block_length
        )

        selected_set = set(selected_indexes)

        matching_patterns = []

        for pattern in all_legal_patterns:

            off_set = {
                i for i, day in enumerate(pattern)
                if day != RA
            }

            if off_set == selected_set:
                matching_patterns.append(pattern)

    if not matching_patterns:

        st.error(
            "This manual bid is illegal."
        )

        return

    legal_pattern = matching_patterns[0]

    st.success("This manual bid is legal.")

    render_bid_calendar(
        dates,
        legal_pattern,
        requirements
    )

    if st.button("Use this manual bid in 7-Layer Builder"):

        send_bid_to_layer_builder(
            legal_pattern,
            selected_indexes,
            requirements
        )

        st.success(
            "Manual bid sent to 7-Layer Bid Builder."
        )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("Bid Period")

    if st.button("Reset App / Start Over"):
        reset_app()

    default_start = first_day_next_month()
    default_end = last_day_same_month(default_start)

    bid_label = st.text_input(
        "Bid period label",
        value=default_start.strftime("%B %Y")
    )

    start_date = st.date_input(
        "Start date",
        value=default_start
    )

    end_date = st.date_input(
        "End date",
        value=default_end
    )

    st.header("Carryover")

    previous_type = st.radio(
        "Previous bid period ended with:",
        ["ON days", "OFF days"]
    )

    if previous_type == "ON days":

        previous_block_length = st.number_input(
            "Previous ON block length",
            min_value=3,
            max_value=6,
            value=3,
            step=1
        )

    else:

        previous_block_length = st.number_input(
            "Previous OFF block length",
            min_value=2,
            max_value=8,
            value=2,
            step=1
        )

    st.header("Seniority")

    total_reserves = st.number_input(
        "Total reserves",
        min_value=1,
        value=498,
        step=1
    )

    seniority_rank = st.number_input(
        "Your reserve rank",
        min_value=1,
        value=346,
        step=1
    )

    if seniority_rank > total_reserves:
        st.error(
            "Your reserve rank cannot be greater than total reserves."
        )
        st.stop()

    max_results = st.number_input(
        "Maximum bids to display",
        min_value=1,
        max_value=500,
        value=25,
        step=1
    )


# =========================================================
# MAIN
# =========================================================

if start_date > end_date:
    st.error("Start date must be before end date.")
    st.stop()

dates = date_range(start_date, end_date)

num_days = len(dates)

st.subheader(
    f"{bid_label}: {start_date} to {end_date}"
)

st.write(
    f"Bid period length: **{num_days} days**"
)

st.info(
    f"Carryover applied: Previous bid period ended with "
    f"{previous_block_length} consecutive "
    f"{previous_type.lower()}."
)

if num_days < 12:
    st.error(
        "Bid period must be at least 12 days "
        "because every month requires 8 GD and 4 FD."
    )
    st.stop()


tab_generate, tab_checker, tab_layers = st.tabs(
    [
        "Generate Bids",
        "Manual Legality Checker",
        "7-Layer Bid Builder"
    ]
)


# =========================================================
# GENERATE TAB
# =========================================================

with tab_generate:

    st.header("Reserve Requirements")

    bulk_text = st.text_area(
        "Paste reserve requirements",
        height=160
    )

    requirements = [100 for _ in dates]

    if bulk_text.strip():

        import re

        numbers = [
            int(x)
            for x in re.findall(r"\d+", bulk_text)
        ]

        parsed = {}

        if len(numbers) >= 2 and len(numbers) % 2 == 0:

            for i in range(0, len(numbers), 2):

                day_number = numbers[i]
                required = numbers[i + 1]

                parsed[day_number] = required

            for i, current_date in enumerate(dates):

                if current_date.day in parsed:
                    requirements[i] = parsed[current_date.day]

    st.header("Requested Days Off")

    requested_indexes = reserve_request_calendar_grid(
        dates,
        requirements
    )

    ranking_preference = st.selectbox(
        "Sorting preference",
        [
            "Best chance / seniority strategy",
            "Most weekends off",
            "Most weekdays off",
            "Longest off blocks",
            "Shortest off blocks",
        ]
    )

    if st.button("Generate Legal Bids", type="primary"):

        with st.spinner("Generating bids..."):

            exact_patterns = generate_all_patterns(
                num_days,
                previous_type=previous_type,
                previous_block_length=previous_block_length
            )

            patterns = generate_unique_off_day_patterns(
                num_days,
                previous_type=previous_type,
                previous_block_length=previous_block_length
            )

            patterns = filter_patterns_by_requested_off_dates(
                patterns,
                requested_indexes
            )

            patterns = sort_patterns_by_preference(
                patterns,
                requirements,
                seniority_rank,
                total_reserves,
                dates,
                ranking_preference
            )

            st.session_state["last_generated_patterns"] = patterns
            st.session_state["last_requirements"] = requirements
            st.session_state["last_requested_indexes"] = requested_indexes

        st.success(
            f"Found {len(patterns)} unique legal off-day bids "
            f"from {len(exact_patterns)} exact legal patterns."
        )

    patterns = st.session_state.get(
        "last_generated_patterns",
        []
    )

    requirements = st.session_state.get(
        "last_requirements",
        requirements
    )

    requested_indexes = st.session_state.get(
        "last_requested_indexes",
        requested_indexes
    )

    if patterns:

        displayed_total = min(
            int(max_results),
            len(patterns)
        )

        for bid_number, pattern in enumerate(
            patterns[:displayed_total],
            start=1
        ):

            chance_label, chance_description = (
                chance_label_for_displayed_order(
                    bid_number,
                    displayed_total
                )
            )

            with st.expander(
                f"Bid #{bid_number} — {chance_label}",
                expanded=(bid_number == 1)
            ):

                st.write(chance_description)

                render_bid_calendar(
                    dates,
                    pattern,
                    requirements
                )

                if st.button(
                    f"Use Bid #{bid_number} in 7-Layer Builder",
                    key=f"use_bid_{bid_number}"
                ):

                    send_bid_to_layer_builder(
                        pattern,
                        requested_indexes,
                        requirements
                    )

                    st.success(
                        f"Bid #{bid_number} sent to 7-Layer Builder."
                    )


# =========================================================
# MANUAL CHECKER TAB
# =========================================================

with tab_checker:

    manual_off_calendar_checker(
        dates,
        previous_type,
        previous_block_length,
        requirements
    )


# =========================================================
# 7 LAYER TAB
# =========================================================

with tab_layers:

    if "layer_bid_pattern" not in st.session_state:

        st.info(
            "Choose a generated or manual bid first."
        )

    else:

        build_suggested_layers(
            dates,
            st.session_state["layer_bid_pattern"],
            st.session_state.get(
                "layer_requirements",
                requirements
            ),
            st.session_state.get(
                "layer_preferred_indexes",
                []
            )
        )