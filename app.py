import streamlit as st

from bid_state import send_bid_to_layer_builder
from cached_generation import cached_generate_patterns
from calendar_ui import render_bid_calendar, reserve_request_calendar_grid
from generator import (
    filter_patterns_by_requested_off_dates,
)
from layer_builder import build_suggested_layers
from manual_checker import manual_off_calendar_checker
from requirements_parser import (
    parse_reserve_requirements_detailed,
)
from rules import (
    MAX_OFF_BLOCK,
    MAX_RA_BLOCK,
    MIN_OFF_BLOCK,
    MIN_RA_BLOCK,
    REQUIRED_FD_DAYS,
    REQUIRED_GD_DAYS,
    TOTAL_OFF_DAYS,
)
from scorer import (
    chance_label_for_displayed_order,
    sort_patterns_by_preference,
)
from utils import date_range, first_day_next_month, last_day_same_month


st.set_page_config(
    page_title="Reserve Bid Finder",
    page_icon="calendar",
    layout="wide"
)

st.markdown(
    """
    <style>
    div.stButton > button[kind="primary"] {
        background-color: #31adad !important;
        border-color: #31adad !important;
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


def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()


default_start = first_day_next_month()
default_end = last_day_same_month(default_start)

st.session_state.setdefault("bid_label_input", default_start.strftime("%B %Y"))
st.session_state.setdefault("start_date_input", default_start)
st.session_state.setdefault("end_date_input", default_end)
st.session_state.setdefault("previous_type_input", "ON days")
st.session_state.setdefault("previous_block_length_input", MIN_RA_BLOCK)
st.session_state.setdefault("total_reserves_input", 498)
st.session_state.setdefault("seniority_rank_input", 346)
st.session_state.setdefault("max_results_input", 25)
st.session_state.setdefault("reserve_requirements_text", "")
st.session_state.setdefault("active_page", "Generate Bids")


with st.sidebar:
    st.header("Bid Period")

    if st.button("Reset App / Start Over"):
        reset_app()

    bid_label = st.text_input(
        "Bid period label",
        key="bid_label_input"
    )

    start_date = st.date_input(
        "Start date",
        key="start_date_input"
    )

    end_date = st.date_input(
        "End date",
        key="end_date_input"
    )

    st.header("Carryover")

    previous_type = st.radio(
        "Previous bid period ended with:",
        ["ON days", "OFF days"],
        key="previous_type_input"
    )

    if previous_type == "ON days":
        if not (MIN_RA_BLOCK <= st.session_state["previous_block_length_input"] <= MAX_RA_BLOCK):
            st.session_state["previous_block_length_input"] = MIN_RA_BLOCK

        previous_block_length = st.number_input(
            "Previous ON block length",
            min_value=MIN_RA_BLOCK,
            max_value=MAX_RA_BLOCK,
            step=1,
            key="previous_block_length_input"
        )
    else:
        if not (MIN_OFF_BLOCK <= st.session_state["previous_block_length_input"] <= MAX_OFF_BLOCK):
            st.session_state["previous_block_length_input"] = MIN_OFF_BLOCK

        previous_block_length = st.number_input(
            "Previous OFF block length",
            min_value=MIN_OFF_BLOCK,
            max_value=MAX_OFF_BLOCK,
            step=1,
            key="previous_block_length_input"
        )

    st.header("Seniority")

    total_reserves = st.number_input(
        "Total reserves",
        min_value=1,
        step=1,
        key="total_reserves_input"
    )

    seniority_rank = st.number_input(
        "Your reserve rank",
        min_value=1,
        step=1,
        key="seniority_rank_input"
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
        step=1,
        key="max_results_input"
    )


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

if num_days < TOTAL_OFF_DAYS:
    st.error(
        f"Bid period must be at least {TOTAL_OFF_DAYS} days "
        f"because every month requires {REQUIRED_GD_DAYS} GD and {REQUIRED_FD_DAYS} FD."
    )
    st.stop()

requirements, parse_warnings, parsed_days = parse_reserve_requirements_detailed(
    st.session_state["reserve_requirements_text"],
    dates
)

page_options = [
    "Generate Bids",
    "Manual Legality Checker",
    "7-Layer Bid Builder",
]

active_page = st.radio(
    "View",
    page_options,
    index=page_options.index(st.session_state["active_page"]),
    horizontal=True,
    label_visibility="collapsed"
)

st.session_state["active_page"] = active_page

notice = st.session_state.pop("layer_builder_notice", None)

if notice:
    st.success(notice)

if active_page == "Generate Bids":
    st.header("Reserve Requirements")

    st.text_area(
        "Paste reserve requirements",
        height=160,
        key="reserve_requirements_text"
    )

    requirements, parse_warnings, parsed_days = parse_reserve_requirements_detailed(
        st.session_state["reserve_requirements_text"],
        dates
    )

    for warning in parse_warnings:
        st.warning(warning)

    if parsed_days:
        st.caption(f"Parsed {len(parsed_days)} pasted requirement value(s).")

    st.header("Requested Days Off")

    requested_indexes = reserve_request_calendar_grid(
        dates,
        requirements,
        previous_type=previous_type,
        previous_block_length=previous_block_length
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
            exact_patterns, patterns = cached_generate_patterns(
                num_days,
                previous_type,
                previous_block_length
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
                f"Bid #{bid_number} - {chance_label}",
                expanded=(bid_number == 1)
            ):
                st.write(chance_description)

                render_bid_calendar(
                    dates,
                    pattern,
                    requirements
                )

                if st.button(
                    "Bid Now",
                    key=f"use_bid_{bid_number}",
                    type="primary"
                ):
                    send_bid_to_layer_builder(
                        pattern,
                        requested_indexes,
                        requirements,
                        message=f"Bid #{bid_number} sent to 7-Layer Bid Builder."
                    )

elif active_page == "Manual Legality Checker":
    manual_off_calendar_checker(
        dates,
        previous_type,
        previous_block_length,
        requirements
    )

elif active_page == "7-Layer Bid Builder":
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
