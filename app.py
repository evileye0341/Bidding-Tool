import streamlit as st

from app_styles import render_app_styles
from bid_state import send_bid_to_layer_builder
from cached_generation import cached_generate_patterns
from calendar_ui import render_bid_calendar, reserve_request_calendar_grid
from dev_defaults import (
    DEV_DEFAULT_BID_LABEL,
    DEV_DEFAULT_END_DATE,
    DEV_DEFAULT_START_DATE,
    load_dev_requirements_text,
)
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
    RA,
    REQUIRED_FD_DAYS,
    REQUIRED_GD_DAYS,
    TOTAL_OFF_DAYS,
)
from scorer import (
    chance_label_for_displayed_order,
    sort_patterns_by_preference,
)
from utils import date_range


APP_NAME = "AA PBS Reserve Bidding Tool"
RESULT_CALENDAR_RENDER_LIMIT = 5
GENERATED_STATE_KEYS = [
    "last_generated_patterns",
    "last_requirements",
    "last_requested_indexes",
    "last_generation_signature",
]
LAYER_STATE_KEYS = [
    "layer_bid_pattern",
    "layer_preferred_indexes",
    "layer_requirements",
    "displayed_layer",
]
NAV_ITEMS = [
    ("Generate Bids", "Generate"),
    ("Manual Legality Checker", "Manual"),
    ("7-Layer Bid Builder", "7-Layer"),
]


st.set_page_config(
    page_title=APP_NAME,
    page_icon="calendar",
    layout="wide"
)

render_app_styles()

st.markdown(
    f"""
    <div class="app-shell">
        <div>
            <div class="app-kicker">Reserve bidding workspace</div>
            <div class="app-title">{APP_NAME}</div>
            <div class="app-subtitle">Generate legal reserve bids, check manual patterns, and build a clean 7-layer bid.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


def compact_stepper(label, key, min_value, max_value, step=1):
    value = int(st.session_state.get(key, min_value))
    value = max(min_value, min(max_value, value))
    st.session_state[key] = value

    st.markdown(
        f"""
        <div class="stepper-row">
            <div class="stepper-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    minus_col, value_col, plus_col = st.columns([1, 2, 1])

    with minus_col:
        if st.button("-", key=f"{key}_minus", width="stretch"):
            st.session_state[key] = max(min_value, value - step)
            st.rerun()

    with value_col:
        st.markdown(
            f'<div class="stepper-value">{st.session_state[key]}</div>',
            unsafe_allow_html=True
        )

    with plus_col:
        if st.button("+", key=f"{key}_plus", width="stretch"):
            st.session_state[key] = min(max_value, value + step)
            st.rerun()

    return int(st.session_state[key])


def render_status_badges(labels):
    badges = "".join(
        f'<span class="status-badge">{label}</span>'
        for label in labels
    )
    st.markdown(
        f'<div class="status-badges">{badges}</div>',
        unsafe_allow_html=True
    )


def sync_reserve_requirements_text():
    st.session_state["reserve_requirements_text_saved"] = st.session_state.get(
        "reserve_requirements_text_input",
        ""
    )
    clear_bid_outputs()


def clear_bid_outputs():
    for key in GENERATED_STATE_KEYS + LAYER_STATE_KEYS:
        st.session_state.pop(key, None)


def setup_signature(
    start_date,
    end_date,
    previous_type,
    previous_block_length,
    requirements_text,
    total_reserves,
    seniority_rank
):
    return (
        start_date.isoformat(),
        end_date.isoformat(),
        previous_type,
        int(previous_block_length),
        requirements_text,
        int(total_reserves),
        int(seniority_rank),
    )


def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()


st.session_state.setdefault("bid_label_input", DEV_DEFAULT_BID_LABEL)
st.session_state.setdefault("start_date_input", DEV_DEFAULT_START_DATE)
st.session_state.setdefault("end_date_input", DEV_DEFAULT_END_DATE)
st.session_state.setdefault("previous_type_input", "ON days")
st.session_state.setdefault("previous_block_length_input", MIN_RA_BLOCK)
st.session_state.setdefault("total_reserves_input", 498)
st.session_state.setdefault("seniority_rank_input", 346)
st.session_state.setdefault("max_results_input", 5)
if "reserve_requirements_text_saved" not in st.session_state:
    st.session_state["reserve_requirements_text_saved"] = st.session_state.get(
        "reserve_requirements_text",
        load_dev_requirements_text()
    )
st.session_state.setdefault(
    "reserve_requirements_text_input",
    st.session_state["reserve_requirements_text_saved"]
)
st.session_state.setdefault("active_page", "Generate Bids")


with st.sidebar:
    st.markdown('<div class="sidebar-group">Bid Period</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-help">Set the month you are building.</div>', unsafe_allow_html=True)

    if st.button("Reset App", width="stretch"):
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

    st.markdown('<div class="sidebar-group">Carryover</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-help">Match how the prior bid ended.</div>', unsafe_allow_html=True)

    previous_type = st.radio(
        "Previous bid period ended with:",
        ["ON days", "OFF days"],
        key="previous_type_input"
    )

    if previous_type == "ON days":
        if not (MIN_RA_BLOCK <= st.session_state["previous_block_length_input"] <= MAX_RA_BLOCK):
            st.session_state["previous_block_length_input"] = MIN_RA_BLOCK

        previous_block_length = compact_stepper(
            "Previous ON block length",
            "previous_block_length_input",
            MIN_RA_BLOCK,
            MAX_RA_BLOCK
        )
    else:
        if not (MIN_OFF_BLOCK <= st.session_state["previous_block_length_input"] <= MAX_OFF_BLOCK):
            st.session_state["previous_block_length_input"] = MIN_OFF_BLOCK

        previous_block_length = compact_stepper(
            "Previous OFF block length",
            "previous_block_length_input",
            MIN_OFF_BLOCK,
            MAX_OFF_BLOCK
        )

    st.markdown('<div class="sidebar-group">Seniority</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-help">Used to sort likely outcomes.</div>', unsafe_allow_html=True)

    total_reserves = st.number_input(
        "Total reserves",
        min_value=1,
        max_value=2000,
        step=1,
        key="total_reserves_input"
    )

    seniority_rank = st.number_input(
        "Your reserve rank",
        min_value=1,
        max_value=2000,
        step=1,
        key="seniority_rank_input"
    )

    if seniority_rank > total_reserves:
        st.error(
            "Your reserve rank cannot be greater than total reserves."
        )
        st.stop()

    st.markdown('<div class="sidebar-group">Results</div>', unsafe_allow_html=True)

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

current_setup_signature = setup_signature(
    start_date,
    end_date,
    previous_type,
    previous_block_length,
    st.session_state["reserve_requirements_text_saved"],
    total_reserves,
    seniority_rank
)

if (
    "current_setup_signature" in st.session_state
    and st.session_state["current_setup_signature"] != current_setup_signature
):
    clear_bid_outputs()

st.session_state["current_setup_signature"] = current_setup_signature

dates = date_range(start_date, end_date)
num_days = len(dates)

st.markdown(
    f"""
    <div class="period-panel">
        <div class="period-item">
            <div class="period-label">Bid Period</div>
            <div class="period-value">{bid_label}</div>
        </div>
        <div class="period-item">
            <div class="period-label">Dates</div>
            <div class="period-value">{start_date} to {end_date}</div>
        </div>
        <div class="period-item">
            <div class="period-label">Length</div>
            <div class="period-value">{num_days} days</div>
        </div>
        <div class="period-item">
            <div class="period-label">Carryover</div>
            <div class="period-value">{previous_block_length} {previous_type.lower()}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

if num_days < TOTAL_OFF_DAYS:
    st.error(
        f"Bid period must be at least {TOTAL_OFF_DAYS} days "
        f"because every month requires {REQUIRED_GD_DAYS} GD and {REQUIRED_FD_DAYS} FD."
    )
    st.stop()

requirements, parse_warnings, parsed_days = parse_reserve_requirements_detailed(
    st.session_state["reserve_requirements_text_saved"],
    dates
)

st.markdown('<div class="nav-label">Workspace</div>', unsafe_allow_html=True)
nav_columns = st.columns(len(NAV_ITEMS))

for (page_name, short_label), column in zip(NAV_ITEMS, nav_columns):
    with column:
        if st.button(
            short_label,
            key=f"nav_{page_name}",
            type="primary" if st.session_state["active_page"] == page_name else "secondary",
            width="stretch"
        ):
            st.session_state["active_page"] = page_name
            st.rerun()

active_page = st.session_state["active_page"]

notice = st.session_state.pop("layer_builder_notice", None)

if notice:
    st.success(notice)

if active_page == "Generate Bids":
    st.header("Generate Bids")
    st.subheader("Reserve Requirements")
    st.markdown(
        '<div class="section-note">Paste the reserve requirement values for this bid period.</div>',
        unsafe_allow_html=True
    )

    st.text_area(
        "Paste reserve requirements",
        height=160,
        key="reserve_requirements_text_input",
        on_change=sync_reserve_requirements_text
    )

    requirements, parse_warnings, parsed_days = parse_reserve_requirements_detailed(
        st.session_state["reserve_requirements_text_saved"],
        dates
    )

    for warning in parse_warnings:
        st.warning(warning)

    if parsed_days:
        st.caption(f"Parsed {len(parsed_days)} pasted requirement value(s).")

    st.subheader("Requested Days Off")
    st.markdown(
        '<div class="section-note">Select the days you want protected in the generated bids.</div>',
        unsafe_allow_html=True
    )

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
            st.session_state["last_generation_signature"] = (
                current_setup_signature,
                tuple(requested_indexes),
                ranking_preference,
            )

        st.success(
            f"Found {len(patterns)} unique legal off-day bids "
            f"from {len(exact_patterns)} exact legal patterns."
        )

    expected_generation_signature = (
        current_setup_signature,
        tuple(requested_indexes),
        ranking_preference,
    )
    patterns = []

    if st.session_state.get("last_generation_signature") == expected_generation_signature:
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

        st.subheader("Generated Bid Options")
        render_status_badges([
            "Legal patterns",
            f"{TOTAL_OFF_DAYS} off days",
            f"{REQUIRED_GD_DAYS} GD / {REQUIRED_FD_DAYS} FD",
            "Carryover checked",
        ])

        if displayed_total > RESULT_CALENDAR_RENDER_LIMIT:
            st.caption(
                f"Showing full calendars for the first {RESULT_CALENDAR_RENDER_LIMIT} bids. "
                "Later bids show summary cards only to keep the app responsive."
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

            weekend_count = sum(
                1 for i, day in enumerate(pattern)
                if day != RA and dates[i].weekday() in (5, 6)
            )
            weekday_count = TOTAL_OFF_DAYS - weekend_count
            off_requirements = [
                requirements[i]
                for i, day in enumerate(pattern)
                if day != RA
            ]
            hardest_requirement = max(off_requirements) if off_requirements else 0
            average_requirement = (
                round(sum(off_requirements) / len(off_requirements))
                if off_requirements
                else 0
            )

            st.markdown(
                f"""
                <div class="bid-card">
                    <div class="bid-card-header">
                        <div class="bid-card-title">Bid #{bid_number}</div>
                        <div class="bid-card-rank">{chance_label}</div>
                    </div>
                    <div class="bid-card-meta">
                        <span class="bid-pill">{weekend_count} weekend off</span>
                        <span class="bid-pill">{weekday_count} weekday off</span>
                        <span class="bid-pill">Hardest date: {hardest_requirement}</span>
                        <span class="bid-pill">Avg req: {average_requirement}</span>
                        <span class="bid-pill">Legal</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.caption(chance_description)

            if bid_number <= RESULT_CALENDAR_RENDER_LIMIT:
                render_bid_calendar(
                    dates,
                    pattern,
                    requirements
                )
            else:
                st.caption("Calendar preview hidden for speed.")

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
    else:
        st.markdown(
            """
            <div class="empty-state">
                <strong>No bids generated yet</strong>
                Select any requested days off, choose a sorting preference, then generate legal bids.
            </div>
            """,
            unsafe_allow_html=True
        )

elif active_page == "Manual Legality Checker":
    manual_off_calendar_checker(
        dates,
        previous_type,
        previous_block_length,
        requirements
    )

elif active_page == "7-Layer Bid Builder":
    layer_pattern = st.session_state.get("layer_bid_pattern")

    if layer_pattern is not None and len(layer_pattern) != num_days:
        for key in LAYER_STATE_KEYS:
            st.session_state.pop(key, None)
        layer_pattern = None

    if layer_pattern is None:
        st.markdown(
            """
            <div class="empty-state">
                <strong>No bid selected</strong>
                Choose Bid Now from a generated or manual legal bid to build layers.
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        build_suggested_layers(
            dates,
            layer_pattern,
            st.session_state.get(
                "layer_requirements",
                requirements
            ),
            st.session_state.get(
                "layer_preferred_indexes",
                []
            )
        )
