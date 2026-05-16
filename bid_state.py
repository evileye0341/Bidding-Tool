import streamlit as st


def send_bid_to_layer_builder(
    pattern,
    preferred_indexes,
    requirements,
    message=None
):
    st.session_state["layer_bid_pattern"] = list(pattern)
    st.session_state["layer_preferred_indexes"] = list(preferred_indexes)
    st.session_state["layer_requirements"] = list(requirements)

    if message:
        st.session_state["layer_builder_notice"] = message

    st.session_state["active_page"] = "7-Layer Bid Builder"

    st.rerun()
