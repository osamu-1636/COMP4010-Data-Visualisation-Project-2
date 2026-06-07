# EDA methodology and dashboard alignment

## Default analytical scope

- Dashboard year: **2016**
- Graph 5/6 population scope: **Refugees+Asylum-seekers+Others of concern**
- Metric type: **observed population stock** from cleaned `time_series.csv`

## Why Graph 5 and Graph 6 use `time_series_clean.csv.gz`

Graph 5 and Graph 6 are designed to answer the wireframe questions: which countries produce the largest cross-border displaced populations, and which countries host the largest populations. The cleaned `time_series.csv` is the canonical long-format stock table, so it is better suited than `asylum_seekers.csv`, which is an application-flow dataset.

## Stock vs flow separation

- Stock metrics: `time_series.csv` and `persons_of_concern.csv`.
- Flow metrics: `asylum_seekers.csv`, `asylum_seekers_monthly.csv`, `resettlement.csv`.
- IDPs are excluded from the default host-country ranking because IDPs are internally displaced and do not represent cross-border hosting.

## Dashboard tables generated

- KPI cards
- Global time series by population type
- Graph 5 top origin countries
- Graph 6 top host countries
- Combined Graph 5 + 6 comparison
- Origin-host corridors and Sankey links
- Choropleth and animated map data
- Monthly asylum seasonality
- Demographic age/sex profile
- Resettlement trend
- Network metrics
- Exploratory forecast table
- Filter options for Shiny controls
- Dashboard component-to-dataset matrix
- Input validation checklist
- Host-pressure table with WDI denominator status
- Crisis-storytelling template for manually cited crisis events
- Rubric-alignment checklist for final report/presentation

## Important caveat for professor-facing presentation

The EDA is now dashboard-ready. The only planned feature that remains partial is **hosting pressure per 100k population**, because it requires a WDI population denominator. The script therefore writes `host_pressure_per_100k.csv` and explicitly marks rows as `missing_wdi_denominator` unless a WDI file is added.

## Top findings, latest year

### Graph 5 — origins
|   rank | origin_country_std               |   value_observed |   share_of_selected_total |
|-------:|:---------------------------------|-----------------:|--------------------------:|
|      1 | Syrian Arab Republic             |      5.71702e+06 |                 0.282711  |
|      2 | Afghanistan                      |      2.98457e+06 |                 0.147589  |
|      3 | South Sudan                      |      1.44233e+06 |                 0.0713242 |
|      4 | Somalia                          |      1.07297e+06 |                 0.0530594 |
|      5 | Sudan                            | 697552           |                 0.0344945 |
|      6 | Democratic Republic of the Congo | 629419           |                 0.0311252 |
|      7 | Iraq                             | 610063           |                 0.0301681 |
|      8 | Burundi                          | 596466           |                 0.0294957 |
|      9 | Myanmar                          | 546466           |                 0.0270232 |
|     10 | Eritrea                          | 523670           |                 0.0258959 |

### Graph 6 — hosts
|   rank | host_country_std   |   value_observed |   share_of_selected_total |
|-------:|:-------------------|-----------------:|--------------------------:|
|      1 | Turkey             |      3.11528e+06 |                 0.150474  |
|      2 | Pakistan           |      1.3574e+06  |                 0.065565  |
|      3 | Germany            |      1.25669e+06 |                 0.0607006 |
|      4 | Uganda             |      1.16267e+06 |                 0.0561593 |
|      5 | Lebanon            |      1.03122e+06 |                 0.0498098 |
|      6 | Iran               | 979526           |                 0.047313  |
|      7 | Ethiopia           | 794094           |                 0.0383563 |
|      8 | Jordan             | 720748           |                 0.0348135 |
|      9 | United States      | 712731           |                 0.0344263 |
|     10 | Kenya              | 494822           |                 0.0239009 |