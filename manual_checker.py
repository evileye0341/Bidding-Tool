import streamlit as st

from bid_state import send_bid_to_layer_builder
from cached_generation import cached_generate_patterns
from calendar_ui import WEEKDAY_LABELS, calendar_cells, render_weekday_headers
from rules import RA, TOTAL_OFF_DAYS


def render_manual_status(selected_count):
    remaining = TOTAL_OFF_DAYS - selected_count

    if remaining > 0:
        status = f"{remaining} more needed"
        state_class = "manual-pending"
    elif remaining == 0:
        status = "Ready to check"
        state_class = "manual-ready"
    else:
        status = f"{abs(remaining)} too many"
        state_class = "manual-error"

    st.markdown(
        f"""
        <style>
        .manual-status {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 12px 0 14px;
        }}
        .manual-chip {{
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 0.84rem;
            font-weight: 850;
        }}
        .manual-ready {{
            border: 1px solid rgba(49,173,173,0.38);
            background: rgba(49,173,173,0.12);
            color: #dffafa;
        }}
        .manual-pending {{
            border: 1px solid rgba(255,255,255,0.12);
            background: rgba(255,255,255,0.06);
            color: rgba(250,250,250,0.78);
        }}
        .manual-error {{
            border: 1px solid rgba(255,95,95,0.40);
            background: rgba(255,95,95,0.14);
            color: #ffdada;
        }}
        </style>
        <div class="manual-status">
            <span class="manual-chip {state_class}">{selected_count} / {TOTAL_OFF_DAYS} off days</span>
            <span class="manual-chip {state_class}">{status}</span>
            <span class="manual-chip manual-ready">Carryover checked</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def manual_off_calendar_checker(
    dates,
    previous_type,
    previous_block_length,
    requirements
):
    st.header("Manual Legality Checker")

    st.markdown(
        '<div class="section-note">Select exactly 12 off days, then send a legal bid to the 7-layer builder.</div>',
        unsafe_allow_html=True
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

    render_manual_status(selected_count)

    if selected_count < TOTAL_OFF_DAYS:
        st.markdown(
            f"""
            <div class="empty-state">
                <strong>Keep selecting dates</strong>
                Select {TOTAL_OFF_DAYS - selected_count} more off day(s).
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    if selected_count > TOTAL_OFF_DAYS:
        st.error(
            f"A legal bid must have exactly {TOTAL_OFF_DAYS} off days."
        )
        return

    with st.spinner("Checking legality..."):
        _, all_legal_patterns = cached_generate_patterns(
            len(dates),
            previous_type,
            previous_block_length
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
