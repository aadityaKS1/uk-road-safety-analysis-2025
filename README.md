# UK Road Safety Analysis, 2025

An analysis of UK road traffic collisions in 2025 (STATS19 data), examining
how collision severity relates to time of day, speed limit, lighting
conditions, and road type. Includes a Jupyter notebook with the full
analysis and an interactive Streamlit dashboard.

**Live dashboard:** https://roadsafetyprojectuk.streamlit.app/
**One-page summaryi is in :** [SUMMARY.md](SUMMARY.md)

---

## Project structure

```
.
├── App.py              # Streamlit dashboard
├── main.ipynb           # Full analysis notebook (cleaning, EDA, stats tests)
├── dataset.csv           # STATS19 2025 collision data
├── Requirements.txt      # Python dependencies
├── SUMMARY.md            # One-page non-technical summary
└── README.md
```

## Research questions

1. How does collision severity vary by time of day?
2. How are speed limit and lighting conditions associated with severity?
3. How does severity vary by road type, and does that pattern change with speed limit?

## Key findings

- Severe-collision rates were highest in the late-night / early-morning
  window, peaking around 04:00 (33.1%) vs. 21.4% at 08:00
  (χ² = 318.78, df = 23, p < 0.001).
- Both speed limit and lighting conditions were significantly associated
  with severity (p < 0.001 for both); the 60 mph category had the highest
  severe-collision rate (36.4%), worsened further by darkness with no lighting.
- Single carriageways had the highest severe-collision rate among known
  road types (27.9% vs. 19.5% for roundabouts), rising to 37.7% at 60 mph
  — though the overall association with road type was small
  (Cramér's V ≈ 0.077).

All findings describe **associations, not causation** — traffic exposure,
weather, and driver behavior were not controlled for. See the notebook's
Limitations section for details.

## Data source

STATS19 UK road collision data, Department for Transport, released under
the [Open Government Licence](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

## Running locally

```cmd
git clone https://github.com/your-username/uk-road-safety-analysis-2025.git
cd uk-road-safety-analysis-2025
pip install -r Requirements.txt
streamlit run App.py
```

The notebook (`main.ipynb`) can be opened in Jupyter or VS Code to see the
full cleaning, EDA, and statistical testing process step by step.

## Methodology notes

- Severity is reported as a **rate** (% severe within each group) rather
  than raw counts, since group sizes vary widely across hours, speed
  limits, and road types.
- Categories with fewer than 30 collisions are excluded from heatmap cells
  to avoid drawing conclusions from unstable percentages.
- Chi-square tests of independence were used to test each association;
  Cramér's V was used to gauge effect size for road type.

---

*Built as part of the CodingAtom Data Science & Analytics internship assessment.*
