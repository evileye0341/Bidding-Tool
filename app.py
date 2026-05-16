import streamlit as st
from datetime import date, timedelta

from generator import generate_all_patterns, filter_patterns_by_requested_off_dates
from scorer import (
    sort_strategy_patterns,
    sort_award_patterns,
    chance_label_for_displayed_order
)
from rules import RA
from utils import date_range


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
st.write("Generate legal reserve bids based on GD, FD, RA rules.")


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


def toggle_requested_day(idx):
    key = f"requested_{idx}"
    st.session_state[key] = not st.session_state.get(key, False)


def reserve_request_calendar_grid(dates, requirements):
    selected_indexes = []

    weekday_headers = st.columns(7)
    for col, label in zip(weekday_headers, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
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


def render_bid_calendar(dates, pattern, requirements=None):
    weekday_headers = st.columns(7)
    for col, label in zip(weekday_headers, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
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


def manual_off_calendar_checker(
    dates,
    previous_type,
    previous_block_length,
    requirements,
    seniority_rank,
    total_reserves
):
    st.header("Manual Legality Checker")

    st.write(
        "Click dates to mark them as off. "
        "Once exactly 12 off days are selected, the app checks legality "
        "and ranks the bid mathematically among all legal bids."
    )

    selected_indexes = []

    weekday_headers = st.columns(7)
    for col, label in zip(weekday_headers, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
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
        st.info(f"Select {12 - selected_count} more off day(s).")
        return

    if selected_count > 12:
        st.error(
            f"You selected {selected_count} off days. "
            f"A legal bid must have exactly 12 off days."
        )
        return

    with st.spinner("Checking legality and ranking bid..."):
        all_legal_patterns = generate_all_patterns(
            len(dates),
            previous_type=previous_type,
            previous_block_length=previous_block_length
        )

        selected_set = set(selected_indexes)
        matching_patterns = []

        for pattern in all_legal_patterns:
            off_set = {i for i, day in enumerate(pattern) if day != RA}
            if off_set == selected_set:
                matching_patterns.append(pattern)

        sorted_all_patterns = sort_award_patterns(
            all_legal_patterns,
            requirements,
            seniority_rank,
            total_reserves
        )

    if not matching_patterns:
        st.error(
            "This manual bid is illegal. "
            "No legal FD/GD assignment exists for these exact off days."
        )
        return

    legal_pattern = matching_patterns[0]

    manual_rank = None
    for index, pattern in enumerate(sorted_all_patterns, start=1):
        if pattern == legal_pattern:
            manual_rank = index
            break

    if manual_rank is None:
        manual_rank = len(sorted_all_patterns)

    total_possible_bids = len(sorted_all_patterns)

    st.success("This manual bid is legal.")

    st.write("Here is the legal FD/GD assignment:")

    render_bid_calendar(
        dates,
        legal_pattern,
        requirements
    )


with st.sidebar:
    st.header("Bid Period")

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

    st.header("Carryover From Previous Bid Period")

    previous_type = st.radio(
        "Previous bid period ended with:",
        ["ON days", "OFF days"]
    )

    if previous_type == "ON days":
        previous_block_length = st.number_input(
            "How many consecutive ON days ended the previous period?",
            min_value=3,
            max_value=6,
            value=3,
            step=1
        )
    else:
        previous_block_length = st.number_input(
            "How many consecutive OFF days ended the previous period?",
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
        st.error("Your reserve rank cannot be greater than total reserves.")
        st.stop()

    max_results = st.number_input(
        "Maximum bids to display",
        min_value=1,
        max_value=500,
        value=25,
        step=1
    )


if start_date > end_date:
    st.error("Start date must be before end date.")
    st.stop()

dates = date_range(start_date, end_date)
num_days = len(dates)

st.subheader(f"{bid_label}: {start_date} to {end_date}")
st.write(f"Bid period length: **{num_days} days**")

st.info(
    f"Carryover applied: Previous bid period ended with "
    f"{previous_block_length} consecutive {previous_type.lower()}."
)

if num_days < 12:
    st.error(
        "Bid period must be at least 12 days because every month requires 8 GD and 4 FD."
    )
    st.stop()


tab_generate, tab_checker = st.tabs(
    ["Generate Bids", "Manual Legality Checker"]
)


with tab_generate:
    st.header("Paste Reserve Requirements")

    bulk_text = st.text_area(
        "Paste reserve requirements",
        placeholder="Example:\n2\n353\n3\n342\n4\n322",
        height=160
    )

    requirements = [100 for _ in dates]

    if bulk_text.strip():
        import re

        numbers = [int(x) for x in re.findall(r"\d+", bulk_text)]
        parsed = {}

        if len(numbers) < 2:
            st.error("Could not find enough numbers in the pasted data.")

        elif len(numbers) % 2 != 0:
            st.error("The pasted data has an odd number of numbers.")

        else:
            for i in range(0, len(numbers), 2):
                day_number = numbers[i]
                required = numbers[i + 1]
                parsed[day_number] = required

            for i, current_date in enumerate(dates):
                if current_date.day in parsed:
                    requirements[i] = parsed[current_date.day]

            st.success(f"Loaded reserve requirements for {len(parsed)} days.")

    st.header("Reserve Requirements & Requested Days Off")
    st.write("Click a date box to request that day off. Selected dates turn blue.")

    requested_indexes = reserve_request_calendar_grid(
        dates,
        requirements
    )

    if st.button("Generate Legal Bids", type="primary"):
        with st.spinner("Generating legal bids..."):
            patterns = generate_all_patterns(
                num_days,
                previous_type=previous_type,
                previous_block_length=previous_block_length
            )

            patterns = filter_patterns_by_requested_off_dates(
                patterns,
                requested_indexes
            )

            patterns = sort_strategy_patterns(
                patterns,
                requirements,
                seniority_rank,
                total_reserves
            )

        st.success(f"Found {len(patterns)} legal bids.")

        if not patterns:
            st.warning(
                "No legal bids found with the current requested days off and carryover rules."
            )
            st.stop()

        displayed_total = min(int(max_results), len(patterns))

        st.header(f"Best {displayed_total} Legal Bids")

        for bid_number, pattern in enumerate(
            patterns[:displayed_total],
            start=1
        ):
            chance_label, chance_description = chance_label_for_displayed_order(
                bid_number,
                displayed_total
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


with tab_checker:
    manual_off_calendar_checker(
        dates,
        previous_type,
        previous_block_length,
        requirements,
        seniority_rank,
        total_reserves
    )