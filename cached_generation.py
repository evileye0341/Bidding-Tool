import streamlit as st

from generator import generate_all_patterns, unique_off_day_patterns


@st.cache_data(show_spinner=False)
def cached_generate_patterns(num_days, previous_type, previous_block_length):
    exact_patterns = generate_all_patterns(
        num_days,
        previous_type=previous_type,
        previous_block_length=previous_block_length
    )
    unique_patterns = unique_off_day_patterns(exact_patterns)

    return exact_patterns, unique_patterns
