import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import chi2_contingency

sns.set_theme(style="whitegrid")

st.set_page_config(
    page_title="UK Road Safety Analysis 2025",
    layout="wide"
)

# ---------------------------------------------------------------
# Load and clean data (mirrors the notebook's cleaning steps)
# ---------------------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv("dataset.csv")

    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
    df = df.drop_duplicates()
    df = df[df["date"].notna()]

    severity_map = {1: "Fatal", 2: "Serious", 3: "Slight"}
    df["severity_label"] = df["collision_severity"].map(severity_map)

    road_type_map = {
        1: "Roundabout", 2: "One way street", 3: "Dual carriageway",
        6: "Single carriageway", 7: "Slip road", 9: "Unknown"
    }
    df["road_type_label"] = df["road_type"].map(road_type_map)

    light_map = {
        1: "Daylight", 4: "Darkness - lights lit", 5: "Darkness - lights unlit",
        6: "Darkness - no lighting", 7: "Darkness - lighting unknown", -1: "No data"
    }
    df["light_conditions_label"] = df["light_conditions"].map(light_map)

    df["hour"] = pd.to_datetime(df["time"], format="%H:%M", errors="coerce").dt.hour
    df["is_severe"] = df["severity_label"].isin(["Fatal", "Serious"])

    return df

df = load_data()

# ---------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------

st.sidebar.header("Filters")

road_types = sorted(df["road_type_label"].dropna().unique())
selected_roads = st.sidebar.multiselect("Road type", road_types, default=road_types)

speed_limits = sorted(df["speed_limit"].dropna().unique())
selected_speeds = st.sidebar.multiselect(
    "Speed limit (mph)", speed_limits, default=speed_limits
)

light_conditions = sorted(df["light_conditions_label"].dropna().unique())
selected_light = st.sidebar.multiselect(
    "Lighting conditions", light_conditions, default=light_conditions
)

filtered = df[
    df["road_type_label"].isin(selected_roads)
    & df["speed_limit"].isin(selected_speeds)
    & df["light_conditions_label"].isin(selected_light)
]

st.sidebar.markdown(f"**{len(filtered):,} collisions** match your filters")

# ---------------------------------------------------------------
# Header + summary
# ---------------------------------------------------------------

st.title("UK Road Safety Analysis, 2025")
st.markdown(
    "Analysis of STATS19 collision data covering the full 2025 calendar year. "
    "Charts below use the **severe collision rate** (Fatal or Serious, as a "
    "percentage of total collisions in each group) rather than raw counts, "
    "since group sizes vary widely."
)

col1, col2, col3 = st.columns(3)
col1.metric("Total collisions (filtered)", f"{len(filtered):,}")
col2.metric(
    "Severe collision rate",
    f"{filtered['is_severe'].mean()*100:.1f}%" if len(filtered) else "N/A"
)
col3.metric(
    "Fatal collisions",
    f"{(filtered['severity_label']=='Fatal').sum():,}"
)

st.divider()

# ---------------------------------------------------------------
# Q1: Severity by hour of day
# ---------------------------------------------------------------

st.header("1. How does collision severity vary by time of day?")

hourly = (
    filtered.groupby("hour")["is_severe"]
    .agg(total_collisions="count", severe_collisions="sum", severe_rate="mean")
    .reset_index()
)
hourly["severe_percentage"] = (hourly["severe_rate"] * 100).round(2)
hourly["severe_se"] = np.sqrt(
    (hourly["severe_rate"] * (1 - hourly["severe_rate"])) / hourly["total_collisions"]
)
hourly["ci_lower"] = (hourly["severe_rate"] - 1.96 * hourly["severe_se"]) * 100
hourly["ci_upper"] = (hourly["severe_rate"] + 1.96 * hourly["severe_se"]) * 100

if len(hourly) > 0:
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.errorbar(
        hourly["hour"], hourly["severe_percentage"],
        yerr=[
            hourly["severe_percentage"] - hourly["ci_lower"],
            hourly["ci_upper"] - hourly["severe_percentage"]
        ],
        fmt="o-", capsize=4
    )
    ax.set_title("Severe Collision Rate by Hour of Day")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Severe Collisions (%)")
    ax.set_xticks(range(24))
    st.pyplot(fig)

    hour_table = pd.crosstab(filtered["hour"], filtered["is_severe"])
    if hour_table.shape[0] > 1 and hour_table.shape[1] > 1:
        chi2, p, dof, _ = chi2_contingency(hour_table)
        st.caption(
            f"Chi-square test: χ² = {chi2:.2f}, df = {dof}, p = {p:.4f}. "
            "Association, not causation — traffic volume and exposure per hour "
            "are not captured in this dataset."
        )
else:
    st.info("No collisions match the current filters.")

st.divider()

# ---------------------------------------------------------------
# Q2: Speed limit x lighting
# ---------------------------------------------------------------

st.header("2. How are speed limit and lighting associated with severity?")

speed_light = pd.pivot_table(
    filtered, values="is_severe", index="speed_limit",
    columns="light_conditions_label", aggfunc="mean"
) * 100
speed_light = speed_light.drop(columns=["No data"], errors="ignore")

if not speed_light.empty:
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(
        speed_light, annot=True, fmt=".1f", cmap="Blues",
        cbar_kws={"label": "Severe Collision Rate (%)"}, ax=ax
    )
    ax.set_title("Severe Collision Rate by Speed Limit and Lighting")
    ax.set_xlabel("Lighting Conditions")
    ax.set_ylabel("Speed Limit (mph)")
    st.pyplot(fig)
    st.caption(
        "Cells excluded where lighting was recorded as 'No data'. "
        "Association, not causation — road type, traffic volume, and location "
        "may drive both variables."
    )
else:
    st.info("Not enough data to build this chart with the current filters.")

st.divider()

# ---------------------------------------------------------------
# Q3: Road type x speed limit
# ---------------------------------------------------------------

st.header("3. How does severity vary by road type and speed limit?")

road_speed = pd.pivot_table(
    filtered, values="is_severe", index="road_type_label",
    columns="speed_limit", aggfunc="mean"
) * 100
road_speed_counts = pd.pivot_table(
    filtered, values="is_severe", index="road_type_label",
    columns="speed_limit", aggfunc="count"
)
road_speed_reliable = road_speed.where(road_speed_counts >= 30)

if not road_speed_reliable.dropna(how="all").empty:
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.heatmap(
        road_speed_reliable, annot=True, fmt=".1f", cmap="Blues",
        cbar_kws={"label": "Severe Collision Rate (%)"}, ax=ax
    )
    ax.set_title("Severe Collision Rate by Road Type and Speed Limit")
    ax.set_xlabel("Speed Limit (mph)")
    ax.set_ylabel("Road Type")
    st.pyplot(fig)
    st.caption(
        "Cells based on fewer than 30 collisions are blanked out to avoid "
        "drawing conclusions from unstable percentages."
    )
else:
    st.info("Not enough data to build a reliable heatmap with the current filters.")

st.divider()

# ---------------------------------------------------------------
# Summary
# ---------------------------------------------------------------

st.header("Key Takeaways")

st.markdown("""
1. **Severity varies by time of day.** Severe collisions made up a larger share
   of reported collisions during late-night and early-morning hours, peaking
   around 04:00 (33.1%) versus 08:00 (21.4%). Statistically significant
   (χ² = 318.78, df = 23, p < 0.001).

2. **Speed limit and lighting are both associated with severity.** The
   highest severe-collision rate by speed limit was at 60 mph (36.4%).
   Darkness with no lighting compounded this further. Both factors were
   statistically significant (p < 0.001).

3. **Single carriageways carry the highest severe-collision rate** among
   known road types (27.9%, vs. 19.5% for roundabouts), and that rate climbs
   with speed limit, reaching 37.7% at 60 mph. The overall association is
   statistically significant but practically small (Cramér's V ≈ 0.077).

**Recommended action:** Prioritise safety review of higher-speed single
carriageways, particularly locations with repeated severe collisions during
late-night and early-morning hours. Consider targeted speed management,
improved lighting, and clearer road markings at flagged locations.

*These findings describe associations in reported 2025 collision data, not
causal effects. Traffic exposure, vehicle characteristics, and location were
not controlled for.*
""")