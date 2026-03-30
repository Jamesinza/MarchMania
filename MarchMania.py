import streamlit as st
import pandas as pd
import re
from difflib import get_close_matches

# =========================
# CONFIG
# =========================
PRED_FILE = "final_blend_submission.csv"

DATA_CONFIG = {
    "Men": {
        "teams": "MTeams.csv",
        "spellings": "MTeamSpellings.csv"
    },
    "Women": {
        "teams": "WTeams.csv",
        "spellings": "WTeamSpellings.csv"
    }
}

SEASON = "2026"

# =========================
# NORMALIZATION
# =========================
def normalize_name(name):
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", " ", name)
    name = re.sub(r"\s+", " ", name)
    return name


# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_all():
    preds = pd.read_csv(PRED_FILE)
    pred_map = dict(zip(preds["ID"], preds["Pred"]))

    league_data = {}

    for league, cfg in DATA_CONFIG.items():
        teams = pd.read_csv(cfg["teams"])
        spellings = pd.read_csv(cfg["spellings"])

        id_to_name = dict(zip(teams["TeamID"], teams["TeamName"]))

        name_to_id = {}

        # canonical names
        for tid, name in id_to_name.items():
            name_to_id[normalize_name(name)] = tid

        # spelling aliases
        for _, row in spellings.iterrows():
            alias = normalize_name(row["TeamNameSpelling"])
            tid = row["TeamID"]
            name_to_id[alias] = tid

        league_data[league] = {
            "name_to_id": name_to_id,
            "id_to_name": id_to_name,
            "teams": teams
        }

    return pred_map, league_data


pred_map, league_data = load_all()

# =========================
# RESOLUTION
# =========================
def resolve_team(name, league):
    data = league_data[league]
    key = normalize_name(name)

    if key in data["name_to_id"]:
        tid = data["name_to_id"][key]
        return tid, data["id_to_name"][tid]

    return None, None


# =========================
# SUGGESTION (NEW)
# =========================
def suggest_team(name, league):
    data = league_data[league]
    key = normalize_name(name)

    candidates = list(data["name_to_id"].keys())

    matches = get_close_matches(key, candidates, n=1, cutoff=0.8)

    if not matches:
        return None, None

    match_key = matches[0]
    tid = data["name_to_id"][match_key]
    return tid, data["id_to_name"][tid]


# =========================
# PARSE INPUT
# =========================
def parse_input(text):
    text = text.lower()

    if " vs " in text:
        parts = text.split(" vs ")
    elif " vs. " in text:
        parts = text.split(" vs. ")
    else:
        return None, None

    if len(parts) != 2:
        return None, None

    return parts[0].strip(), parts[1].strip()


# =========================
# PREDICTION
# =========================
def predict(idA, idB):
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

⚠️ Supports **2026 tournament matchups only**
""")

st.divider()

with st.expander("ℹ️ How to use"):
    st.markdown("""
1. Type matchups naturally:

**Examples:**
- `uconn vs ucla`
- `duke vs kentucky`
 
2. Click **Predict (Gender)**  
3. View win probabilities and predicted winner  

### What the prediction means
- Values above 50% → predicted winner  
- Values near 50% → close matchup  
- Values far from 50% → strong prediction  

This model focuses on **direction (who wins)** rather than perfect probability calibration.
"""
)

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

# =========================
# MAIN LOGIC
# =========================
tab_men, tab_women = st.tabs(["Men", "Women"])

def render_league(league):
    st.subheader(f"{league} Matchup")

    user_input = st.text_input(
        "Enter matchup (e.g. 'uconn vs ucla')",
        key=f"{league}_input"
    )

    if st.button(f"Predict ({league})", key=f"{league}_btn"):

        teamA_raw, teamB_raw = parse_input(user_input)

        if teamA_raw is None:
            st.error("Invalid format. Use: teamA vs teamB")
            return

        idA, teamA = resolve_team(teamA_raw, league)
        idB, teamB = resolve_team(teamB_raw, league)

        # =========================
        # SUGGESTION LOGIC (NEW)
        # =========================
        if idA is None:
            sug_idA, sug_teamA = suggest_team(teamA_raw, league)
        else:
            sug_idA, sug_teamA = None, None

        if idB is None:
            sug_idB, sug_teamB = suggest_team(teamB_raw, league)
        else:
            sug_idB, sug_teamB = None, None

        if idA is None or idB is None:
            if sug_teamA or sug_teamB:
                st.warning(f"Did you mean: {sug_teamA or teamA_raw} vs {sug_teamB or teamB_raw}?")
            else:
                st.error("One or both teams not recognized")
            return

        st.info(f"Interpreted as: {teamA} vs {teamB}")

        p = predict(idA, idB)

        if p is None:
            st.error("Matchup not found in predictions")
            return

        winner = teamA if p > 0.5 else teamB
        confidence = abs(p - 0.5)

        # Card UI (kept your style)
        st.markdown(f"""
        <div style='border: 2px solid #4CAF50; border-radius: 12px; padding: 16px; margin-bottom: 16px; background-color: black;'>
            <h2 style='margin: 0;'>🏆 {winner}</h2>
            <h3 style='margin: 6px 0;'>{teamA} vs {teamB}</h3>
            <ul>
                <li><strong>{teamA}</strong>: {p:.2%}</li>
                <li><strong>{teamB}</strong>: {1-p:.2%}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if confidence > 0.25:
            st.success("High confidence")
        elif confidence > 0.1:
            st.info("Moderate confidence")
        else:
            st.warning("Close matchup")

        st.progress(min(confidence * 2, 1.0))


with tab_men:
    render_league("Men")

with tab_women:
    render_league("Women")
