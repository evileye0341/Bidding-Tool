import streamlit as st


APP_CSS = """
<style>
:root {
    --aa-bg: #0e1117;
    --aa-panel: #171a21;
    --aa-panel-2: #20232b;
    --aa-border: rgba(255,255,255,0.10);
    --aa-muted: rgba(250,250,250,0.68);
    --aa-teal: #31adad;
    --aa-portal-panel: #55564f;
    --aa-portal-cell: #f1f0eb;
    --aa-portal-weekend: #e8e5d8;
}
.block-container {
    max-width: 1180px;
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}
[data-testid="stSidebar"] {
    border-right: 1px solid rgba(255,255,255,0.08);
    background: #24252d;
}
[data-testid="stSidebar"] .block-container {
    padding-top: 1.1rem;
}
h1, h2, h3 {
    letter-spacing: 0;
}
h2 {
    margin-top: 0.85rem;
}
.app-kicker {
    color: #31adad;
    font-size: 0.82rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.app-title {
    font-size: 2.35rem;
    font-weight: 900;
    line-height: 1.05;
    margin-bottom: 8px;
}
.app-subtitle {
    color: rgba(250,250,250,0.72);
    margin-bottom: 18px;
}
.app-shell {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 14px;
}
.period-panel {
    display: grid;
    grid-template-columns: minmax(220px, 1fr) repeat(3, minmax(120px, 0.35fr));
    gap: 12px;
    padding: 14px;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    background: #171a21;
    margin: 8px 0 18px;
}
.nav-label {
    color: rgba(250,250,250,0.58);
    font-size: 0.78rem;
    font-weight: 800;
    margin-bottom: 6px;
    text-transform: uppercase;
}
.sidebar-group {
    margin: 16px 0 8px;
    padding-top: 13px;
    border-top: 1px solid rgba(255,255,255,0.09);
    color: #fafafa;
    font-size: 1.05rem;
    font-weight: 850;
}
.sidebar-help {
    color: rgba(250,250,250,0.62);
    font-size: 0.82rem;
    margin: -2px 0 10px;
}
.stepper-row {
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    background: #171a21;
    padding: 8px 10px;
    margin-bottom: 8px;
}
.stepper-label {
    color: rgba(250,250,250,0.64);
    font-size: 0.82rem;
    font-weight: 750;
    margin-bottom: 4px;
}
.stepper-value {
    text-align: center;
    color: #fafafa;
    font-size: 1rem;
    font-weight: 900;
    padding-top: 0.35rem;
}
.period-item {
    padding: 8px 10px;
    border-radius: 6px;
    background: rgba(255,255,255,0.035);
}
.period-label {
    color: rgba(250,250,250,0.58);
    font-size: 0.78rem;
    font-weight: 700;
    margin-bottom: 2px;
}
.period-value {
    color: #fafafa;
    font-weight: 850;
    font-size: 1rem;
}
.empty-state {
    border: 1px solid rgba(255,255,255,0.08);
    background: #171a21;
    border-radius: 8px;
    padding: 18px 20px;
    color: rgba(250,250,250,0.76);
    margin: 16px 0;
}
.empty-state strong {
    color: #fafafa;
    display: block;
    margin-bottom: 4px;
}
.status-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 0 0 16px;
}
.status-badge {
    border: 1px solid rgba(49,173,173,0.38);
    background: rgba(49,173,173,0.12);
    color: #dffafa;
    border-radius: 999px;
    padding: 6px 10px;
    font-size: 0.84rem;
    font-weight: 850;
}
.bid-card {
    border: 1px solid rgba(255,255,255,0.10);
    background: #171a21;
    border-radius: 8px;
    padding: 16px 18px 18px;
    margin: 14px 0;
}
.bid-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
}
.bid-card-title {
    color: #fafafa;
    font-size: 1.15rem;
    font-weight: 900;
}
.bid-card-rank {
    color: #31adad;
    font-size: 0.92rem;
    font-weight: 850;
    white-space: nowrap;
}
.bid-card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 4px 0 14px;
}
.bid-pill {
    border: 1px solid rgba(255,255,255,0.10);
    background: rgba(255,255,255,0.05);
    border-radius: 999px;
    padding: 5px 10px;
    color: rgba(250,250,250,0.82);
    font-size: 0.85rem;
    font-weight: 750;
}
.section-note {
    color: rgba(250,250,250,0.68);
    margin-top: -8px;
    margin-bottom: 14px;
}
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
    min-height: 42px;
    white-space: pre-line;
    border-radius: 8px;
    font-weight: 600;
}
div[data-testid="stSidebar"] div.stButton > button,
div[data-testid="stSidebar"] div.stButton > button[kind="secondary"] {
    min-height: 32px;
    padding: 0.25rem 0.5rem;
}
div[data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,0.10);
}
@media (max-width: 900px) {
    .period-panel {
        grid-template-columns: 1fr;
    }
    .app-shell {
        flex-direction: column;
    }
    .app-title {
        font-size: 1.9rem;
    }
}
</style>
"""


def render_app_styles():
    st.markdown(APP_CSS, unsafe_allow_html=True)
