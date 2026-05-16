import streamlit as st

from bid_state import send_bid_to_layer_builder
from calendar_ui import WEEKDAY_LABELS, calendar_cells, render_weekday_headers
from generator import generate_unique_off_day_patterns
from rules import RA, TOTAL_OFF_DAYS


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

    render_weekday_headers()
    cells = calendar_cells(dates)

    for week_start in range(0, len(cells), len(WEEKDAY_LABELS)):
        cols = st.columns(len(WEEKDAY_LABELS))

        for i in range(len(WEEKDAY_LABELS)):
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
                    width="stretch"
                ):
                    st.session_state[key] = not st.session_state[key]
                    st.rerun()

                if st.session_state[key]:
                    selected_indexes.append(idx)

    selected_count = len(selected_indexes)

    st.write(f"Selected off days: **{selected_count} / {TOTAL_OFF_DAYS}**")

    if selected_count < TOTAL_OFF_DAYS:
        st.info(
            f"Select {TOTAL_OFF_DAYS - selected_count} more off day(s)."
        )
        return

    if selected_count > TOTAL_OFF_DAYS:
        st.error(
            f"A legal bid must have exactly {TOTAL_OFF_DAYS} off days."
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

    if st.button("Bid Now", type="primary"):
        send_bid_to_layer_builder(
            legal_pattern,
            selected_indexes,
            requirements,
            message="Manual bid sent to 7-Layer Bid Builder."
        )
