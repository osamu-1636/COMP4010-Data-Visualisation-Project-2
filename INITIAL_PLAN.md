# Initial Project Plan

**Project:** Global Refugee Movement Dashboard  
**Course:** Data Stories: Building Interactive Dashboards with Python Shiny  
**Planning period:** 18 May 2026 – 07 June 2026  
**Final deadline:** 07 June 2026

---

## 1. Project Goal

The goal of this project is to build an interactive Python Shiny dashboard that explains global refugee and forced displacement patterns over time. The dashboard will combine geospatial, temporal, and comparative visualisations to answer the question:

> **How have global refugee movements evolved over time, and which countries or regions face the greatest displacement and hosting pressure?**

The project will move from a global overview to country-level and regional insights. Users will be able to filter by year, region, origin country, host country, and displacement category.

---

## 2. Main Deliverables

### Proposal deadline — 18 May 2026

Required outputs:

- Proposal write-up under 500 words
- Wireframe sketch
- Short presentation slides
- Initial project plan
- Dataset description
- Planned visualisation and analytical methods
- GitHub repository link

### Final deadline — 07 June 2026

Required outputs:

- Source code in the main branch of the GitHub repository
- Final Python Shiny dashboard
- Final report, up to 6 pages, written in LaTeX
- Final presentation slides
- Live demo of the deployed dashboard

---

## 3. Three-Week Timeline

## Week 1 — Proposal, data collection, and design foundation

**Dates:** 18 May – 24 May 2026  
**Main objective:** Confirm the topic, collect the dataset, design the dashboard story, and complete the proposal materials.

### 18 May — Proposal submission day

Tasks:

- Finalise project topic and research question.
- Create GitHub repository.
- Add initial `README.md`.
- Write proposal draft under 500 words.
- Prepare initial wireframe sketch.
- Prepare short proposal slides.
- Submit proposal materials.

Expected output:

- Proposal write-up completed.
- Wireframe completed.
- Initial slides completed.
- GitHub repository created.

### 19–20 May — Dataset collection and understanding

Tasks:

- Download or collect UNHCR refugee/displacement data.
- Download supporting country indicators from the World Bank if needed.
- Inspect dataset structure, columns, missing values, and country names.
- Identify available years, population categories, origin countries, and host countries.
- Save raw files under `data/raw/`.

Expected output:

- Raw datasets stored in the repository or linked through download scripts.
- Data dictionary draft created.
- Initial notes on limitations and missing values.

### 21–22 May — Data cleaning and preprocessing

Tasks:

- Standardise country names and ISO codes.
- Filter relevant displacement categories.
- Aggregate data by year, origin, host country, and region.
- Create processed datasets for charts.
- Calculate derived metrics, such as hosted refugees per 1,000 population.
- Save cleaned data under `data/processed/`.

Expected output:

- Cleaned dataset ready for dashboard development.
- Reusable preprocessing notebook or Python script.
- Initial summary statistics.

### 23–24 May — Exploratory visualisation and dashboard layout

Tasks:

- Build exploratory charts in notebooks.
- Test chart types: map, line chart, bar chart, scatter plot, Sankey/flow chart, stacked area chart.
- Refine dashboard wireframe based on actual data.
- Decide final layout and user journey.
- Create reusable chart functions in `src/charts.py`.

Expected output:

- At least 3 working exploratory charts.
- Final dashboard structure decided.
- Chart function prototypes prepared.

---

## Week 2 — Dashboard implementation and analytical components

**Dates:** 25 May – 31 May 2026  
**Main objective:** Build the main Python Shiny app with interactive filters and core charts.

### 25–26 May — Shiny app skeleton

Tasks:

- Create `app.py`.
- Build the main dashboard layout.
- Add navigation pages or tabs.
- Add year slider, region filter, country selectors, and metric selector.
- Connect cleaned data to the Shiny server logic.

Expected output:

- App runs locally.
- Basic layout and filters are functional.

### 27–28 May — Core visualisations

Tasks:

- Implement global choropleth map.
- Implement displacement trend line chart.
- Implement ranked bar charts for origin and host countries.
- Implement scatter/bubble chart for hosting pressure.
- Add tooltips and dynamic titles.

Expected output:

- At least 5 charts implemented.
- At least 3 chart types included.
- Charts update based on filters.

### 29 May — Movement/flow visualisation

Tasks:

- Implement Sankey diagram or flow map.
- Filter major origin-to-host routes to avoid visual clutter.
- Add explanation text for how to interpret the flow chart.

Expected output:

- Movement relationship chart implemented.
- Dashboard story becomes more complete.

### 30–31 May — Analytical or ML component

Tasks:

- Create simple trend projection for selected countries or regions.
- Test baseline forecasting using Linear Regression or another simple method.
- Add interpretation of model limitations.
- Optional: cluster countries by displacement/hosting profile.

Expected output:

- Analytical component added to the dashboard.
- Model output is connected to the visual story.

---

## Week 3 — Refinement, report, deployment, and final presentation

**Dates:** 01 June – 07 June 2026  
**Main objective:** Polish the dashboard, write the report, deploy the app, and prepare the final demo.

### 01–02 June — Dashboard refinement

Tasks:

- Improve layout, spacing, labels, and colour consistency.
- Add explanatory text boxes and chart captions.
- Make sure every chart supports the research question.
- Fix performance issues with large data.
- Test app on different screen sizes.

Expected output:

- Dashboard is visually polished.
- User flow is clear and logical.

### 03 June — Reproducibility and documentation

Tasks:

- Finalise `requirements.txt`.
- Check that the app runs from a fresh environment.
- Clean repository structure.
- Update `README.md` with running instructions and project explanation.
- Add comments to important scripts.

Expected output:

- Reproducible GitHub repository.
- Clear setup instructions.

### 04 June — Final report draft

Tasks:

- Write LaTeX report sections:
  - Motivation
  - Dataset and preprocessing
  - Visualisation design decisions
  - Interaction design
  - Analytical/ML methods
  - Key findings
  - Challenges and limitations
  - Future improvements
- Export key figures or screenshots.

Expected output:

- First full draft of final report completed.

### 05 June — Deployment and testing

Tasks:

- Deploy the Shiny app to shinyapps.io.
- Test deployed app link.
- Fix package or file-path issues.
- Add deployment link to README and final slides.

Expected output:

- Public dashboard link working.
- Deployment instructions documented.

### 06 June — Final presentation preparation

Tasks:

- Prepare final 8-minute presentation slides.
- Create live demo script.
- Select 3–5 key insights to present.
- Practice transition between slides and dashboard.
- Prepare backup screenshots in case the live demo fails.

Expected output:

- Final slides completed.
- Demo script completed.

### 07 June — Final submission and presentation

Tasks:

- Submit source code in main branch.
- Submit final report.
- Submit final presentation slides.
- Present dashboard and live demo.

Expected output:

- Final project submitted.
- Live demo presented.

---

## 4. Planned Dashboard Components

| Component | Chart type | Purpose | Interaction |
|---|---|---|---|
| Global overview map | Choropleth map | Show displacement/hosting by country | Year slider, metric selector |
| Global trend | Line chart | Show change over time | Country/region selector |
| Top origin countries | Bar chart | Identify major source countries | Year and region filters |
| Top host countries | Bar chart | Identify major host countries | Year and metric filters |
| Hosting pressure | Scatter/bubble chart | Compare displacement with population or GDP | Hover, region filter |
| Movement routes | Sankey diagram or flow map | Show origin-to-host relationships | Origin/host selectors |
| Regional composition | Stacked area chart | Compare regional changes over time | Region/category selector |

---

## 5. Risk Management

| Risk | Impact | Mitigation |
|---|---|---|
| Dataset is too large | App may run slowly | Pre-aggregate data before loading into Shiny |
| Country names do not match map data | Map may show missing countries | Use ISO3 country codes and manual correction table |
| Flow map becomes too cluttered | Hard to interpret | Show only top routes or add filters |
| Forecasting component is weak | May distract from visual story | Keep it simple and explain limitations clearly |
| Deployment fails | Cannot present online app | Prepare local demo and backup screenshots |

---

## 6. Success Criteria

The project will be successful if:

- The dashboard has at least 5 charts and 3 chart types.
- The app is interactive and lets users filter the data.
- The story is easy to follow from global overview to detailed insights.
- The code is reproducible and documented.
- The dashboard is deployed online.
- The final report clearly explains design decisions, data challenges, insights, limitations, and future improvements.
