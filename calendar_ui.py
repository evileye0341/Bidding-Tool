import streamlit as st

from rules import RA


WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def calendar_cells(dates):
    start_weekday = dates[0].weekday()
    cells = [None] * start_weekday + list(range(len(dates)))

    while len(cells) % len(WEEKDAY_LABELS) != 0:
        cells.append(None)

    return cells


def render_weekday_headers():
    weekday_headers = st.columns(len(WEEKDAY_LABELS))

    for col, label in zip(weekday_headers, WEEKDAY_LABELS):
        col.markdown(f"**{label}**")


def toggle_requested_day(idx):
    key = f"requested_{idx}"
    st.session_state[key] = not st.session_state.get(key, False)


def render_carryover_reminder(previous_type, previous_block_length):
    if previous_type == "ON days":
        label = "RA"
        chip_class = "carryover-ra"
    else:
        label = "OFF"
        chip_class = "carryover-off"

    chips = "".join(
        f'<span class="carryover-chip {chip_class}">{label}</span>'
        for _ in range(int(previous_block_length))
    )

    st.markdown(
        f"""
        <style>
        .carryover-reminder {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 4px 0 14px;
            padding: 11px 13px;
            border: 1px solid #74756f;
            border-radius: 8px;
            background: #55564f;
            color: #f1f0eb;
        }}
        .carryover-title {{
            font-weight: 700;
            white-space: nowrap;
        }}
        .carryover-chips {{
            display: flex;
            gap: 4px;
            flex-wrap: wrap;
        }}
        .carryover-chip {{
            min-width: 38px;
            padding: 5px 9px;
            border-radius: 999px;
            text-align: center;
            font-weight: 800;
            font-size: 0.85rem;
        }}
        .carryover-ra {{
            background: #f1f0eb;
            border: 1px solid #deddd6;
            color: #111111;
        }}
        .carryover-off {{
            background: #31adad;
            border: 1px solid #31adad;
            color: #ffffff;
        }}
        </style>
        <div class="carryover-reminder">
            <div class="carryover-title">Previous month ended:</div>
            <div class="carryover-chips">{chips}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def reserve_request_calendar_grid(
    dates,
    requirements,
    previous_type=None,
    previous_block_length=None
):
    selected_indexes = []

    if previous_type is not None and previous_block_length is not None:
        render_carryover_reminder(previous_type, previous_block_length)

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
                    width="stretch"
                ):
                    toggle_requested_day(idx)
                    st.rerun()

                if st.session_state[selected_key]:
                    selected_indexes.append(idx)

    return selected_indexes


def render_bid_calendar(dates, pattern, requirements=None):
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
                day = pattern[idx]

                if day == RA:
                    bg = "#f1f0eb"
                    border = "#777870"
                    weight = "normal"
                    color = "#111111"
                else:
                    bg = "#31adad"
                    border = "#31adad"
                    weight = "bold"
                    color = "#ffffff"

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
                        color: {color};
                    ">
                        <strong>{current_date.strftime('%b %d')}</strong><br>
                        {current_date.strftime('%a')}<br>
                        <span style="font-weight:{weight};">{day}</span>
                        {req_line}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
