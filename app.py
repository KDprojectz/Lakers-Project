import streamlit as st
from nba_api.stats.endpoints 
import leaguegamefinder, scheduleleaguev2
import pandas as pd
from nba_api.stats.static import teams  

st.set_page_config(page_title="Lakers Tracker", page_icon="🏀")

LAKERS_ID = 1610612747

@st.cache_data(ttl=1800)
def get_games():
    games = leaguegamefinder.LeagueGameFinder(
        team_id_nullable=LAKERS_ID,
        season_nullable="2025-26"
    )
    return games.get_data_frames()[0]   


@st.cache_data(ttl=1800)
def get_all_games():
    games = leaguegamefinder.LeagueGameFinder(
        league_id_nullable="00",
        season_nullable="2025-26"
    )
    return games.get_data_frames()[0]

@st.cache_data(ttl=1800)
def get_schedule():
    schedule = scheduleleaguev2.ScheduleLeagueV2(
        league_id="00",
        season="2025-26"
    )


    data = schedule.get_dict()
    games = []

    for date_group in data["leagueSchedule"]["gameDates"]:
        for game in date_group["games"]:
            home = game["homeTeam"]
            away = game["awayTeam"]

            if home["teamId"] == LAKERS_ID or away["teamId"] == LAKERS_ID:
                games.append({
                    "Date": pd.to_datetime(game["gameDateTimeUTC"], utc=True).tz_convert("America/Los_Angeles"),
                    "Matchup": f'{away["teamTricode"]} @ {home["teamTricode"]}',
                    "Arena": game.get("arenaName", "TBD")
                })

    return pd.DataFrame(games)

if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

df = get_games()

wins = (df["WL"] == "W").sum()
losses = (df["WL"] == "L").sum()

recent = df[["GAME_DATE", "MATCHUP", "WL", "PTS"]].head(5)

page = st.sidebar.selectbox(
    "  ",
    ["Home", "Schedule", "Win Predictor"]
)

if page == "Home":
    st.title("🏀 Lakers Performance Tracker 🏀")
    st.write("This website tracks Lakers games and predicts win chances.")
    st.write(f"Record: {wins}-{losses}")
    col1, col2, col3 = st.columns([1,2,1])
    with col2: 
        st.image("lakers_logo_png")
    

elif page == "Schedule":
    st.title("Lakers Schedule")

    st.subheader("Recent Games")
    st.table(recent)

    st.subheader("Upcoming Games")

    schedule_df = get_schedule()
    schedule_df["Date"] = pd.to_datetime(schedule_df["Date"])

    upcoming = schedule_df[schedule_df["Date"] >= pd.Timestamp.now(tz="UTC")]
    upcoming = upcoming.sort_values("Date").head(5)

    if upcoming.empty:
        st.write("No upcoming Lakers games found.")
    else:
        st.table(upcoming)

    st.subheader("Points Scored in Recent Games")

    chart_data = df[["GAME_DATE", "PTS"]].head(10)
    chart_data = chart_data[::-1]

    st.line_chart(chart_data.set_index("GAME_DATE"))

    avg_points = df["PTS"].head(10).mean()

    st.subheader("Math Insight")
    st.write(f"Lakers average {avg_points:.1f} points in their last 10 games.")

elif page == "Win Predictor":
    st.title("Pregame Win Predictor")

    all_games = get_all_games()

    nba_teams = teams.get_teams()
    team_names = {team["full_name"]: team["id"] for team in nba_teams}

    opponent_name = st.selectbox("Choose Opponent", sorted(team_names.keys()))
    opponent_id = team_names[opponent_name]

    location = st.selectbox("Location", ["Home", "Away"])

    lakers_games = all_games[all_games["TEAM_ID"] == LAKERS_ID]
    opponent_games = all_games[all_games["TEAM_ID"] == opponent_id]

    lakers_wins = (lakers_games["WL"] == "W").sum()
    lakers_total = len(lakers_games)
    lakers_win_pct = lakers_wins / lakers_total if lakers_total > 0 else 0.5

    opponent_wins = (opponent_games["WL"] == "W").sum()
    opponent_total = len(opponent_games)
    opponent_win_pct = opponent_wins / opponent_total if opponent_total > 0 else 0.5

    lakers_recent = lakers_games.head(5)
    lakers_recent_wins = (lakers_recent["WL"] == "W").sum()
    lakers_form = lakers_recent_wins / len(lakers_recent) if len(lakers_recent) > 0 else 0.5

    opponent_recent = opponent_games.head(5)
    opponent_recent_wins = (opponent_recent["WL"] == "W").sum()
    opponent_form = opponent_recent_wins / len(opponent_recent) if len(opponent_recent) > 0 else 0.5

    score = 50

    if location == "Home":
        score += 7
    else:
        score -= 4

    score += lakers_win_pct * 20
    score += lakers_form * 15
    score -= opponent_win_pct * 20
    score -= opponent_form * 15

    score = max(0, min(100, score))

    st.write(f"Lakers Win Rate: {lakers_win_pct:.1%} || Lakers Last 5 Win Rate: {lakers_form:.1%}")
    st.write(f"{opponent_name} Win Rate: {opponent_win_pct:.1%} || Last 5 Win Rate: {opponent_form:.1%}")

    st.subheader("Prediction")
    st.write(f"Predicted Lakers Win Chance: {score:.1f}%")
