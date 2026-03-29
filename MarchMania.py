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

st.divider()

st.markdown("""
Predict outcomes for **NCAA Division I March Madness** tournaments.

- Covers **Men’s and Women’s tournaments**
- Based on machine learning ensemble models
- Optimized for **win/loss predictions**

⚠️ This tool currently supports **2026 tournament matchups only**
""")

st.divider()

with st.expander("ℹ️ How to use this app"):
    st.markdown("""
1. Select two teams  
2. Click **Predict Winner**  
3. View win probabilities and predicted winner  

### What the prediction means
- Values above 50% → predicted winner  
- Values near 50% → close matchup  
- Values far from 50% → strong prediction  

This model focuses on **direction (who wins)** rather than perfect probability calibration.
""")
    
with st.expander("📊 Scope & Limitations"):
    st.markdown("""
- Only includes **NCAA Division I March Madness**
- Covers **Men’s and Women’s tournaments**
- Predictions are based on **precomputed matchups**
- Does NOT account for:
  - injuries
  - roster changes
  - live game conditions

Future versions will include real-time model inference.
""")
    
with st.expander("👤 About"):
    st.markdown("""
**Developer:** James Sheldon

Machine learning enthusiast focused on:
- Time-series modeling
- Ensemble systems
- Experimental architectures

This project explores combining multiple models to improve **decision accuracy** in sports prediction.

🔗 Add your links here:
- GitHub: https://github.com/Jamesinza
- LinkedIn: https://www.linkedin.com/in/jamesinza/
- WebSite: https://jamessheldon.wordpress.com/
""")
    
st.divider()

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

            # st.markdown(f"""
            # ### 🔮 Prediction

            # **{teamA} vs {teamB}**

            # - {teamA}: **{p:.2%}**
            # - {teamB}: **{1-p:.2%}**

            # ### 🏆 Winner: **{winner}**
            # """)

            st.markdown(f"## 🏆 {winner}")

            st.markdown(f"""
            ### {teamA} vs {teamB}

            - **{teamA}**: {p:.2%}  
            - **{teamB}**: {1-p:.2%}
            """)

            # Confidence label
            if confidence > 0.25:
                st.success("High confidence prediction")
            elif confidence > 0.1:
                st.info("Moderate confidence")
            else:
                st.warning("Close matchup")

            st.progress(min(confidence * 2, 1.0))


with tab_men:
    render_league("Men")

with tab_women:
    render_league("Women")
