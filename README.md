# Global Refugee Movement Dashboard

**Course project:** Data Stories: Building Interactive Dashboards with Python Shiny  
**Project type:** Interactive data visualization dashboard  
**Proposed topic:** Global refugee movement, hosting pressure, and displacement trends  
**Final deadline:** 07 June 2026

---

## 1. Project Overview

This project builds an interactive Python Shiny dashboard that explores how forced displacement has changed across countries and regions over time. The dashboard focuses on refugees, asylum-seekers, internally displaced people, and related forcibly displaced populations using publicly available humanitarian and development data.

The main goal is to turn a large, multidimensional dataset into a clear visual story. Instead of showing only static charts, the dashboard will allow users to filter by year, region, origin country, host country, and displacement category. The final app will help users understand where displacement originates, where displaced people are hosted, how patterns have changed over time, and how displacement pressure relates to country-level indicators such as population size and income level.

---

## 2. Research Question

**How have global refugee movements evolved over time, and which countries or regions face the greatest displacement and hosting pressure?**

Supporting questions:

1. Which countries have produced the largest refugee populations over time?
2. Which host countries receive the highest numbers of refugees and asylum-seekers?
3. How do displacement patterns differ across regions and income groups?
4. How has the global displacement trend changed over the last two decades?
5. Which regions experience the fastest growth in forcibly displaced populations?
6. Is hosting pressure related to population size, GDP per capita, income level, or geographic proximity?
7. Which countries host disproportionately large refugee populations relative to their population size?
8. How concentrated are refugee flows between specific origin-host country pairs?
9. Which countries act as both major refugee-producing and refugee-hosting nations?
10. How stable or volatile are refugee movement patterns across time?

---

## 3. Motivation

Forced displacement is one of the most important humanitarian issues in the world. However, the data is difficult to interpret because it involves time, geography, country relationships, population categories, and highly unequal distributions. A static table or one-dimensional chart cannot fully explain the story.

This project uses interactive visualisation to make the data easier to explore. Users can move from a global overview to country-level details, compare regions, and observe changes over time. The dashboard is designed to support both storytelling and exploration: viewers can follow the intended analytical flow, but they can also filter and investigate their own questions.

---

## 4. Dataset Description

### Main dataset

The primary dataset will be collected from the **UNHCR Refugee Data Finder** and Kaggle, which provides data on forcibly displaced and stateless populations, including refugees, asylum-seekers, internally displaced people, and related population categories.

Planned fields:

- Year
- Origin country
- Host/asylum country
- Region
- Population category
- Number of people
- Country ISO code

### Supporting datasets

Additional country-level indicators may be collected from the **World Bank World Development Indicators (WDI)**, such as:

- Total population
- GDP per capita
- Income group
- Region

These indicators will be used to calculate relative hosting pressure, for example refugees hosted per 1,000 inhabitants.

---

## 5. Visualization Challenge

This dataset is non-trivial to visualize because it contains:

- **Spatial structure:** displacement involves origin and destination countries.
- **Temporal structure:** trends change significantly across years.
- **High dimensionality:** year, region, origin, host country, and population category must be considered together.
- **Skewed distributions:** a small number of countries may dominate global totals.
- **Mixed data types:** numerical counts, geographical data, categorical regions, and time-series data must be combined.
- **Missing or inconsistent values:** country names, historical changes, and different reporting categories may require cleaning.

The dashboard must therefore combine maps, time-series charts, ranked comparisons, and linked filters to make the story understandable.

---

## 6. Planned Dashboard Story

The dashboard will be organised as a guided analytical story:

### 1 — Global Overview

Purpose: give users a quick understanding of the scale of displacement.

Planned components:

- KPI cards showing total displaced population, number of host countries, number of origin countries, and latest available year.
- Global choropleth map showing refugee or displaced population by host country.
- Year slider to observe changes over time.

### 2 — Where Displacement Comes From

Purpose: identify major origin countries and regions.

Planned components:

- Ranked bar chart of top origin countries.
- Time-series line chart for selected origin countries.
- Region filter to compare displacement patterns.

### 3 — Where Refugees Are Hosted

Purpose: understand destination and hosting pressure.

Planned components:

- Ranked bar chart of top host countries.
- Bubble/scatter plot comparing hosted refugees with population or GDP per capita.
- Metric toggle between absolute count and per-capita hosting pressure.

### 4 — Movement and Regional Patterns

Purpose: show origin-to-host relationships.

Planned components:

- Sankey diagram or flow map showing major origin-to-host routes.
- Regional stacked area chart showing changes over time.
- Tooltips and country selection for detailed inspection.

### 5 — Insights and Forecasting

Purpose: summarise key findings and add an analytical component.

Planned components:

- Short-term trend projection using a simple baseline model.
- Model comparison or uncertainty explanation if time allows.
- Summary text boxes explaining key findings.

---

## 7. Planned Charts

The final dashboard will include at least **5 charts** and at least **3 chart types**.

Planned chart list:

1. **Choropleth map** — displaced or hosted population by country.
2. **Line chart** — displacement trend over time.
3. **Bar chart** — top origin or host countries.
4. **Scatter/bubble chart** — hosting pressure vs. country indicators.
5. **Sankey diagram or flow map** — major origin-to-host movements.
6. **Stacked area chart** — regional displacement composition over time.
7. **Animated Flow Map** — Migration flows between continents and countries. This allows users to observe not only where people are moving from and to, but also how these migration patterns change across different years.
---

## 8. Planned Interactivity

The dashboard will include:

- Year slider
- Region selector
- Origin country selector
- Host country selector
- Population category filter
- Metric toggle: absolute count vs. per-capita rate
- Hover tooltips
- Dynamic chart updates
- Linked views where one selection affects other charts
- Optional animation for time-based map or flow changes

---

## 9. Analytical and ML Methods

The project will mainly focus on visual analytics, but it may include lightweight analytical or predictive components:

- Data cleaning and aggregation with Pandas
- Country-code matching and geospatial joins
- Normalisation by population size
- Trend calculation by country and region
- Simple forecasting using Linear Regression or another baseline time-series method
- Optional clustering of countries based on displacement/hosting profiles

The ML component will be used to support interpretation rather than replace the visual story.

---

## 10. Technology Stack

Planned tools:

- **Python Shiny** — dashboard framework
- **Pandas** — data cleaning and transformation
- **Plotly** — interactive charts
- **GeoPandas** — geospatial data processing
- **PyDeck or Plotly Mapbox** — interactive maps
- **Scikit-learn** — simple forecasting or clustering
- **Matplotlib/Seaborn** — exploratory plots during development
- **LaTeX/Overleaf** — final report
- **GitHub** — version control and documentation
- **shinyapps.io** — deployment

---


## 11. Deployment Plan

The final app will be deployed to **shinyapps.io** using `rsconnect-python`.

Planned deployment command:

```bash
rsconnect deploy shiny . --name <account-name> --title global-refugee-dashboard
```

The final deployment link will be added here:

```text
Deployment link: [to be added]
```
---

## 12. Team Task Allocation

| Role | Main responsibility | Tasks |
|---|---|---|
| Member 1 | Data collection and preprocessing | Download data, clean country names, handle missing values |
| Member 2 | Visualization design | Dashboard story, chart choices, wireframe |
| Member 3 | Shiny app implementation | Layout, filters, dynamic chart updates |
| Member 4 | Report and presentation | LaTeX report, slides, final demo script |

This table can be updated depending on the final team structure.

---

## 13. Expected Output

The final output will be a reproducible Python Shiny dashboard that:

- Tells a clear data story about forced displacement.
- Includes at least 5 charts and at least 3 chart types.
- Supports interactive exploration and filtering.
- Includes meaningful analytical insights.
- Can be run locally from the GitHub repository.
- Is deployed online through shinyapps.io.
