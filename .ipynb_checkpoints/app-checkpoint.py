import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


@st.cache_data
def load_data():
    matches = pd.read_csv("matches_cleaned.csv")  
    deliveries = pd.read_csv("deliveries_cleaned.csv")  
    
        
    # Convert season column
    matches["season"] = matches["season"].astype(str).str.extract(r'(\d{2,4})$')[0]
    
    # Convert to integer
    matches["season"] = matches["season"].astype(int)
    
    # Convert 2-digit years to 4-digit
    matches["season"] = matches["season"].apply(lambda x: x + 2000 if x < 100 else x)

    deliveries = deliveries.merge(matches[["id", "season"]], left_on="match_id", right_on="id", how="left")

    return matches, deliveries

matches, deliveries = load_data()

# 🏏 Streamlit Dashboard UI
st.title("🏏 IPL Data Analysis Dashboard")
# 🎛️ Interactive Player Search (Case-Insensitive + Runs + Wickets)
st.subheader("🔎 Search Player Stats")
player_name = st.text_input("Enter player name:").strip().lower()

if player_name:
    # Case-Insensitive Search
    player_stats = deliveries[deliveries["batter"].str.lower() == player_name]
    bowler_stats = deliveries[deliveries["bowler"].str.lower() == player_name]

    if not player_stats.empty:
        batting_summary = player_stats.groupby("batter").agg(
            total_runs=pd.NamedAgg(column="batsman_runs", aggfunc="sum"),
            total_balls=pd.NamedAgg(column="ball", aggfunc="count"),
            matches=pd.NamedAgg(column="match_id", aggfunc="nunique")
        ).reset_index()
        batting_summary["strike_rate"] = (batting_summary["total_runs"] / batting_summary["total_balls"] * 100).round(2)

        st.write(f"### 🏏 {player_name.title()}'s Batting Stats")
        st.write(batting_summary)

    if not bowler_stats.empty:
        wicket_deliveries = bowler_stats[
            bowler_stats["dismissal_kind"].isin(["bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"])
        ]
        bowling_summary = wicket_deliveries.groupby("bowler")["player_dismissed"].count().reset_index()
        bowling_summary.rename(columns={"player_dismissed": "wickets"}, inplace=True)

        st.write(f"### 🎯 {player_name.title()}'s Bowling Stats")
        st.write(bowling_summary)

    if player_stats.empty and bowler_stats.empty:
        st.write("⚠️ Player not found in dataset!")




st.subheader("🏏 Search Team Squad by Year")

min_year = 2008
max_year = matches["season"].max()

year = st.number_input("Enter Year:", min_value=min_year, max_value=max_year, step=1)

team_name_mapping = {
    "Delhi Daredevils": "Delhi Daredevils (2008-2018)",
    "Delhi Capitals": "Delhi Capitals (2019-Present)",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Deccan Chargers": "Deccan Chargers (2008-2012)",
    "Kings XI Punjab": "Kings XI Punjab (2008-2020)",
    "Punjab Kings": "Punjab Kings (2021-Present)",
    "Kochi Tuskers Kerala": "Kochi Tuskers Kerala (2011)",
    "Pune Warriors India": "Pune Warriors India (2011-2013)",
    "Gujarat Lions": "Gujarat Lions (2016-2017)",
    "Rising Pune Supergiant": "Rising Pune Supergiant (2016)",
    "Rising Pune Supergiants": "Rising Pune Supergiants (2017)",
    "Chennai Super Kings": "Chennai Super Kings",
    "Rajasthan Royals": "Rajasthan Royals"
}

matches["team1"] = matches["team1"].replace(team_name_mapping)
matches["team2"] = matches["team2"].replace(team_name_mapping)
deliveries["batting_team"] = deliveries["batting_team"].replace(team_name_mapping)
deliveries["bowling_team"] = deliveries["bowling_team"].replace(team_name_mapping)

teams = sorted(set(matches["team1"]).union(set(matches["team2"])))
team = st.selectbox("Select Team:", teams)

# Allowed years for each team
special_cases = {
    "Chennai Super Kings": list(range(2008, 2016)) + list(range(2018, max_year + 1)),  
    "Rajasthan Royals": list(range(2008, 2016)) + list(range(2018, max_year + 1)),  
    "Deccan Chargers (2008-2012)": list(range(2008, 2013)),
    "Kings XI Punjab (2008-2020)": list(range(2008, 2021)),  
    "Punjab Kings (2021-Present)": list(range(2021, max_year + 1)),  
    "Delhi Daredevils (2008-2018)": list(range(2008, 2019)),  
    "Delhi Capitals (2019-Present)": list(range(2019, max_year + 1)),  
    "Rising Pune Supergiant (2016)": [2016],  
    "Rising Pune Supergiants (2017)": [2017],  
    "Pune Warriors India (2011-2013)": list(range(2011, 2014)),  
}

if team and year:
    if team in special_cases and year not in special_cases[team]:
        st.write(f"⚠️ {team} did not play in IPL {year}.")
    else:
        team_matches = matches[(matches["season"] == year) & ((matches["team1"] == team) | (matches["team2"] == team))]
        
        if not team_matches.empty:
            team_deliveries = deliveries[deliveries["match_id"].isin(team_matches["id"])]

            team_batters = team_deliveries[team_deliveries["batting_team"] == team]["batter"].dropna().unique()
            team_bowlers = team_deliveries[team_deliveries["bowling_team"] == team]["bowler"].dropna().unique()

            unique_players = sorted(set(team_batters).union(set(team_bowlers)))

            if unique_players:
                st.write(f"### 🏏 {team} Squad in {year}")
                st.write(", ".join(unique_players))
            else:
                st.write(f"⚠️ No squad data available for {team} in {year}!")
        else:
            st.write(f"⚠️ No matches found for {team} in {year}.")
# 1️⃣ Most Successful Teams (By Wins)
st.subheader("🏆 Most Successful IPL Teams")
team_wins = matches[matches["winner"] != "No Result"]["winner"].value_counts()

fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(y=team_wins.index, x=team_wins.values, palette="viridis", ax=ax)
ax.set_xlabel("Total Wins")
ax.set_ylabel("Teams")
ax.set_title("Most Successful IPL Teams")

# Add labels
for index, value in enumerate(team_wins.values):
    ax.text(value + 2, index, str(value), va='center', fontsize=12)

st.pyplot(fig)


# Create tabs
tab1, tab2 = st.tabs(["Top 10 Batsmen (By Runs)", "Highest Partnerships (By Runs)"])

# 🏏 Top 10 IPL Batsmen by Runs
with tab1:
    st.subheader("🏏 Top 10 IPL Batsmen by Runs")
    
    batsman_runs = deliveries.groupby("batter")["batsman_runs"].sum().reset_index()
    top_batsmen = batsman_runs.sort_values(by="batsman_runs", ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(y=top_batsmen["batter"], x=top_batsmen["batsman_runs"], palette="coolwarm", ax=ax)
    ax.set_xlabel("Total Runs")
    ax.set_ylabel("Batsmen")
    ax.set_title("Top 10 IPL Batsmen by Runs")

    # Add labels
    for index, value in enumerate(top_batsmen["batsman_runs"]):
        ax.text(value + 200, index, str(value), va='center', fontsize=12)

    st.pyplot(fig)

# 🤝 Highest IPL Partnerships by Runs
with tab2:
    st.subheader("🤝 Highest IPL Partnerships by Runs")

    partnerships = deliveries.groupby(["match_id", "batter", "non_striker"])["batsman_runs"].sum().reset_index()
    partnerships = partnerships.groupby(["batter", "non_striker"])["batsman_runs"].sum().reset_index()
    top_partnerships = partnerships.sort_values(by="batsman_runs", ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(y=top_partnerships["batsman_runs"], 
                x=top_partnerships["batter"] + " & " + top_partnerships["non_striker"], 
                palette="magma", ax=ax)
    ax.set_ylabel("Total Runs")
    ax.set_xlabel("Partnerships")
    ax.set_title("Top 10 Highest IPL Partnerships by Runs")
    plt.xticks(rotation=45, ha='right')

    for index, value in enumerate(top_partnerships["batsman_runs"]):
        ax.text(index, value + 5, str(value), ha='center', fontsize=12)

    st.pyplot(fig)
    
# Create tabs
tab1, tab2, tab3= st.tabs(["Top 10 Bowlers (By Wickets)", "Best Economy Bowlers (Min 50 Overs)",
    "Death Bowlers"])

# 🎯 Top 10 IPL Bowlers by Wickets
with tab1:
    st.subheader("🎯 Top 10 IPL Bowlers by Wickets")
    
    wicket_deliveries = deliveries[
        deliveries["dismissal_kind"].isin(["bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"])
    ]

    bowler_wickets = wicket_deliveries.groupby("bowler")["player_dismissed"].count().reset_index()
    bowler_wickets.rename(columns={"player_dismissed": "wickets"}, inplace=True)
    top_bowlers = bowler_wickets.sort_values(by="wickets", ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(y=top_bowlers["bowler"], x=top_bowlers["wickets"], palette="magma", ax=ax)
    ax.set_xlabel("Total Wickets")
    ax.set_ylabel("Bowlers")
    ax.set_title("Top 10 IPL Bowlers by Wickets")

    # Add labels
    for index, value in enumerate(top_bowlers["wickets"]):
        ax.text(value + 2, index, str(value), va='center', fontsize=12)

    st.pyplot(fig)

# 💰 Best Economy Rate Bowlers (Min 50 Overs)
with tab2:
    st.subheader("💰 Best Economy Rate Bowlers (Min 50 Overs)")

    bowler_stats = deliveries.groupby("bowler").agg(
        total_runs=pd.NamedAgg(column="total_runs", aggfunc="sum"),
        total_balls=pd.NamedAgg(column="ball", aggfunc="count")
    ).reset_index()

    bowler_stats["economy"] = (bowler_stats["total_runs"] / (bowler_stats["total_balls"] / 6)).round(2)
    qualified_bowlers = bowler_stats[bowler_stats["total_balls"] >= 300]  # 50 overs = 300 balls
    top_economy_bowlers = qualified_bowlers.sort_values(by="economy").head(10)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(y=top_economy_bowlers["bowler"], x=top_economy_bowlers["economy"], palette="coolwarm", ax=ax)
    ax.set_xlabel("Economy Rate")
    ax.set_ylabel("Bowlers")
    ax.set_title("Best Economy Rate Bowlers (Min 50 Overs)")

    # Add labels
    for index, value in enumerate(top_economy_bowlers["economy"]):
        ax.text(value + 0.1, index, str(value), va='center', fontsize=12)

    st.pyplot(fig)

with tab3:
    st.subheader("🎯 Most Effective Death Bowlers (Wickets in Overs 16-20)")
    death_bowlers = deliveries[(deliveries["over"] >= 16) & (deliveries["is_wicket"] == 1)]
    death_bowlers_count = death_bowlers["bowler"].value_counts().head(10)
    st.bar_chart(death_bowlers_count)

# 1️⃣ Win Percentage of Teams Over the Years
tab1, tab2 = st.tabs([
     "Most Impactful Players", "Most Sixes"
])


with tab1:
    st.subheader("🏆 Most Impactful Players (By Player of the Match Awards)")
    impactful_players = matches["player_of_match"].value_counts().head(10)
    st.bar_chart(impactful_players)

with tab2:
    st.subheader("💥 Most Six-Hitters in IPL History")
    sixes = deliveries[deliveries["batsman_runs"] == 6]
    most_sixes = sixes["batter"].value_counts().head(10)
    st.bar_chart(most_sixes)




st.write("📊 More insights coming soon!")


st.markdown("---")  # Adds a horizontal line
st.write("👨‍💻 **Developed by: PJ Hemanadhan**")