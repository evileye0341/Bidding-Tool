from datetime import timedelta
from textwrap import dedent

import streamlit as st

from layer_logic import build_layer_layout, off_indexes_for_pattern
from rules import TOTAL_OFF_DAYS


WEEKDAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def render_html(html):
    st.markdown(
        dedent(html).strip(),
        unsafe_allow_html=True
    )


def layer_calendar_cells(dates):
    first_date = dates[0]
    last_date = dates[-1]
    start = first_date - timedelta(days=(first_date.weekday() + 1) % 7)
    end = last_date + timedelta(days=(5 - last_date.weekday()) % 7)

    cells = []
    current = start

    while current <= end:
        cells.append(current)
        current += timedelta(days=1)

    return cells


def render_layer_styles():
    render_html(
        """
        <style>
        .layer-note {
            color: rgba(250,250,250,0.68);
            margin: -6px 0 14px;
        }
        .layer-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 0 0 16px;
        }
        .layer-badge {
            border: 1px solid rgba(49,173,173,0.38);
            background: rgba(49,173,173,0.12);
            color: #dffafa;
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 0.84rem;
            font-weight: 850;
        }
        .layer-size-card {
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 8px;
            background: #171a21;
            padding: 10px 12px;
            margin-bottom: 8px;
        }
        .layer-size-name {
            color: rgba(250,250,250,0.68);
            font-size: 0.82rem;
            font-weight: 800;
            margin-bottom: 5px;
        }
        .layer-size-value {
            color: #fafafa;
            font-size: 1.18rem;
            font-weight: 900;
            text-align: center;
            padding-top: 0.34rem;
        }
        .layer-overview {
            border: 1px solid #c9cbc7;
            border-radius: 8px;
            background: #f1f2f3;
            padding: 12px 14px 14px;
            margin: 12px 0 18px;
            max-width: 980px;
        }
        .overview-month {
            color: #8e9092;
            font-size: 1.5rem;
            font-weight: 800;
            margin-bottom: 6px;
        }
        .overview-axis {
            display: flex;
            justify-content: space-around;
            color: #6f7377;
            font-size: 1rem;
            font-weight: 700;
            margin-left: 64px;
            margin-bottom: 4px;
        }
        .overview-row {
            display: grid;
            grid-template-columns: 58px 1fr;
            align-items: center;
            gap: 4px;
            margin: -2px 0 5px;
        }
        .overview-row.active {
            outline: 3px solid #5fc6ee;
            border-radius: 6px;
            background: #f7fbfd;
        }
        .overview-label {
            background: #c4c7c9;
            border-radius: 5px;
            color: #000;
            font-weight: 800;
            text-align: center;
            line-height: 24px;
            height: 24px;
        }
        .overview-row.active .overview-label {
            background: #65c7ee;
            color: white;
        }
        .overview-cells {
            display: grid;
            gap: 3px;
        }
        .overview-dot {
            display: block;
            aspect-ratio: 1 / 1;
            min-height: 12px;
            background: #ffffff;
            border: 1px solid #eceff1;
        }
        .overview-dot.weekend {
            background: #e8e5d8;
        }
        .overview-dot.selected {
            background: #31adad;
            border-color: #31adad;
        }
        .overview-dot.outside {
            background: #b8b8b1;
            border-color: #b8b8b1;
        }
        .bid-layer-panel {
            background: #55564f;
            border-radius: 8px;
            overflow: hidden;
            padding-bottom: 14px;
            margin: 18px 0;
            max-width: 980px;
        }
        .bid-layer-title {
            background: #4d4e47;
            color: #65c7ee;
            font-size: 1.45rem;
            font-weight: 900;
            padding: 18px 26px;
            letter-spacing: 0;
        }
        .layer-weekdays {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            color: #b8b9b3;
            font-weight: 800;
            font-size: 1.05rem;
            padding: 12px 40px 8px;
            gap: 3px;
            text-align: center;
        }
        .layer-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 3px;
            padding: 0 40px 28px;
        }
        .layer-day {
            min-height: 112px;
            border-radius: 8px;
            background: #f1f0eb;
            border: 1px solid #777870;
            position: relative;
            overflow: hidden;
        }
        .layer-day.selected {
            background: #31adad;
            color: white;
        }
        .layer-day.final-off {
            box-shadow: inset 0 0 0 3px rgba(49, 173, 173, 0.32);
        }
        .layer-day.outside {
            background: #b8b8b1;
            color: #8b8d8b;
        }
        .day-number {
            position: absolute;
            top: 6px;
            left: 8px;
            color: #92969a;
            font-size: 1.15rem;
            font-weight: 800;
        }
        .layer-day.selected .day-number,
        .layer-day.selected .requirement {
            color: white;
        }
        .day-content {
            display: flex;
            min-height: 112px;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            padding-top: 10px;
        }
        .off-text {
            font-size: 1.35rem;
            font-weight: 900;
            line-height: 1;
        }
        .prefer-text {
            font-size: 1.02rem;
            font-weight: 800;
            line-height: 1.1;
        }
        .ghost-off {
            color: #31adad;
            font-size: 1rem;
            font-weight: 900;
            opacity: 0.82;
        }
        .requirement {
            position: absolute;
            right: 8px;
            bottom: 6px;
            color: #000;
            font-weight: 900;
            font-size: 1rem;
        }
        @media (max-width: 900px) {
            .layer-weekdays,
            .layer-grid {
                padding-left: 14px;
                padding-right: 14px;
            }
            .layer-day {
                min-height: 88px;
            }
        }
        </style>
        """
    )


def render_layer_badges(labels):
    badges = "".join(
        f'<span class="layer-badge">{label}</span>'
        for label in labels
    )
    render_html(f'<div class="layer-badges">{badges}</div>')


def compact_layer_stepper(label, key, min_value, max_value, default_value):
    if key not in st.session_state:
        st.session_state[key] = default_value

    value = int(st.session_state[key])
    value = max(min_value, min(max_value, value))
    st.session_state[key] = value

    render_html(
        f"""
        <div class="layer-size-card">
            <div class="layer-size-name">{label}</div>
        </div>
        """
    )
    minus_col, value_col, plus_col = st.columns([1, 2, 1])

    with minus_col:
        if st.button("-", key=f"{key}_minus", width="stretch"):
            st.session_state[key] = max(min_value, value - 1)
            st.rerun()

    with value_col:
        render_html(f'<div class="layer-size-value">{st.session_state[key]}</div>')

    with plus_col:
        if st.button("+", key=f"{key}_plus", width="stretch"):
            st.session_state[key] = min(max_value, value + 1)
            st.rerun()

    return int(st.session_state[key])


def render_layer_calendar(dates, pattern, requirements, selected_indexes, layer_number):
    cells = layer_calendar_cells(dates)
    date_to_index = {
        current_date: i
        for i, current_date in enumerate(dates)
    }
    selected = set(selected_indexes)
    final_off = set(off_indexes_for_pattern(pattern))
    weekday_header = "".join(
        f"<div class='layer-weekday'>{label}</div>"
        for label in WEEKDAY_LABELS
    )
    day_tiles = []

    for current_date in cells:
        idx = date_to_index.get(current_date)

        if idx is None:
            requirement = 0
            content = ""
            classes = "layer-day outside"
        elif idx in selected:
            requirement = requirements[idx]
            content = (
                f"<div class='off-text'>{pattern[idx]}</div>"
                "<div class='prefer-text'>Prefer</div>"
            )
            classes = "layer-day selected"
        elif idx in final_off:
            requirement = requirements[idx]
            content = f"<div class='ghost-off'>{pattern[idx]}</div>"
            classes = "layer-day final-off"
        else:
            requirement = requirements[idx]
            content = ""
            classes = "layer-day"

        day_tiles.append(
            f'<div class="{classes}">'
            f'<div class="day-number">{current_date.day}</div>'
            f'<div class="day-content">{content}</div>'
            f'<div class="requirement">{requirement}</div>'
            f'</div>'
        )

    render_html(
        f"""
        <section class="bid-layer-panel">
            <div class="bid-layer-title">LAYER {layer_number}</div>
            <div class="layer-weekdays">{weekday_header}</div>
            <div class="layer-grid">{"".join(day_tiles)}</div>
        </section>
        """
    )


def build_suggested_layers(
    dates,
    pattern,
    requirements,
    preferred_indexes
):
    st.header("7-Layer Bid Builder")
    render_layer_styles()
    render_layer_badges([
        "Legal",
        f"{TOTAL_OFF_DAYS} off days",
        "Carryover checked",
        "Layer 7 locked",
    ])

    off_indexes = off_indexes_for_pattern(pattern)

    if len(off_indexes) != TOTAL_OFF_DAYS:
        st.error(
            f"This tool expects a final bid with exactly {TOTAL_OFF_DAYS} off days."
        )
        return

    preferred_in_bid = [
        i for i in preferred_indexes
        if i in off_indexes
    ]

    ordered_priority_dates = []

    if preferred_in_bid:
        st.subheader("Preferred Date Priority")

        render_html(
            '<div class="layer-note">Protect the most important dates first.</div>'
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
        render_html(
            """
            <div class="empty-state">
                <strong>No preferred dates selected</strong>
                Layers will be balanced by date difficulty.
            </div>
            """
        )

    st.subheader("Layer Sizes")
    render_html(
        f'<div class="layer-note">Set Layers 1-5. Layer 6 fills the remaining dates. Layer 7 stays locked at {TOTAL_OFF_DAYS}.</div>'
    )

    requested_sizes = {}

    layer_size_columns = st.columns(5)

    for layer_number, column in enumerate(layer_size_columns, start=1):
        with column:
            requested_sizes[layer_number] = compact_layer_stepper(
                f"Layer {layer_number}",
                f"layer_size_{layer_number}",
                0,
                TOTAL_OFF_DAYS,
                2
            )

    layers, _ = build_layer_layout(
        pattern,
        requirements,
        ordered_priority_dates,
        requested_sizes
    )

    st.session_state.setdefault("displayed_layer", 7)

    st.subheader("Layer Overview")
    cells = layer_calendar_cells(dates)
    date_to_index = {
        current_date: i
        for i, current_date in enumerate(dates)
    }

    week_starts = [
        current_date.day
        for current_date in cells
        if current_date.weekday() == 6 and current_date in date_to_index
    ]

    if dates[0].day not in week_starts:
        week_starts.insert(0, dates[0].day)

    if dates[-1].day not in week_starts:
        week_starts.append(dates[-1].day)

    header = "".join(
        f"<span>{day}</span>"
        for day in week_starts
    )

    overview_rows = []

    for layer_number in range(1, 8):
        selected = set(layers[layer_number])
        day_cells = []

        for current_date in cells:
            idx = date_to_index.get(current_date)
            classes = ["overview-dot"]

            if idx is None:
                classes.append("outside")
            elif idx in selected:
                classes.append("selected")
            elif current_date.weekday() in (5, 6):
                classes.append("weekend")

            day_cells.append(f'<span class="{" ".join(classes)}"></span>')

        active_class = " active" if layer_number == st.session_state["displayed_layer"] else ""
        overview_rows.append(
            f'<div class="overview-row{active_class}">'
            f'<div class="overview-label">{layer_number}</div>'
            f'<div class="overview-cells" style="grid-template-columns: repeat({len(cells)}, minmax(8px, 1fr));">'
            f'{"".join(day_cells)}'
            f'</div>'
            f'</div>'
        )

    render_html(
        f"""
        <div class="layer-overview">
            <div class="overview-month">{dates[0].strftime('%B %Y')}</div>
            <div class="overview-axis">{header}</div>
            {"".join(overview_rows)}
        </div>
        """
    )

    st.write("Select layer:")
    button_columns = st.columns(7)

    for layer_number, column in enumerate(button_columns, start=1):
        with column:
            if st.button(
                str(layer_number),
                key=f"display_layer_{layer_number}",
                type="primary" if st.session_state["displayed_layer"] == layer_number else "secondary",
                width="stretch"
            ):
                st.session_state["displayed_layer"] = layer_number
                st.rerun()

    displayed_layer = st.session_state["displayed_layer"]

    st.subheader("Suggested 7-Layer Bid Layout")
    render_layer_calendar(
        dates,
        pattern,
        requirements,
        layers[displayed_layer],
        displayed_layer
    )

    st.caption(
        "Preferred dates are placed first. Remaining dates are balanced by difficulty across Layers 1-6."
    )
