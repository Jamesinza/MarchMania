import streamlit as st
import pandas as pd

# =========================
# CONFIG
# =========================
PRED_FILE = "final_blend_submission.csv"

DATA_CONFIG = {
    "Men": {
        "teams": "MTeams.csv",
        "id_range": (1000, 2999)
    },
    "Women": {
        "teams": "WTeams.csv",
        "id_range": (3000, 3999)
    }
}

SEASON = "2026"

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_all():
    preds = pd.read_csv(PRED_FILE)
    pred_map = dict(zip(preds["ID"], preds["Pred"]))

    team_maps = {}

    for league, cfg in DATA_CONFIG.items():
        teams = pd.read_csv(cfg["teams"])
        name_to_id = dict(zip(teams["TeamName"], teams["TeamID"]))
        team_maps[league] = (name_to_id, teams)

    return pred_map, team_maps


pred_map, team_maps = load_all()

# =========================
# PREDICT
# =========================
def predict(league, teamA, teamB):
    name_to_id, _ = team_maps[league]

    idA = name_to_id[teamA]
    idB = name_to_id[teamB]

    key = f"{SEASON}_{idA}_{idB}"
    reverse_key = f"{SEASON}_{idB}_{idA}"

    if key in pred_map:
        return pred_map[key]
    elif reverse_key in pred_map:
        return 1 - pred_map[reverse_key]
    return None


# =========================
# UI
# =========================
st.set_page_config(page_title="March Madness Predictor", layout="centered")

st.title("🏀 March Madness Predictor")

# Tabs (better UX than radio)
tab_men, tab_women = st.tabs(["Men", "Women"])

def render_league(league):
    name_to_id, teams_df = team_maps[league]
    teams_list = sorted(teams_df["TeamName"].unique())

    st.subheader(f"{league} Matchup")

    teamA = st.selectbox("Team A", teams_list, key=f"{league}_A")
    teamB = st.selectbox("Team B", teams_list, key=f"{league}_B")

    if teamA == teamB:
        st.warning("Select two different teams")

    if st.button(f"Predict ({league})", key=f"{league}_btn") and teamA != teamB:
        p = predict(league, teamA, teamB)

        if p is None:
            st.error("Matchup not found")
        else:
            winner = teamA if p > 0.5 else teamB
            confidence = abs(p - 0.5)

            st.markdown(f"""
            ### 🔮 Prediction

            **{teamA} vs {teamB}**

            - {teamA}: **{p:.2%}**
            - {teamB}: **{1-p:.2%}**

            ### 🏆 Winner: **{winner}**
            """)

            st.progress(min(confidence * 2, 1.0))


with tab_men:
    render_league("Men")

with tab_women:
    render_league("Women")