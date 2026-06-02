# Preprocessing methodology

## Scope

This preprocessing layer uses six UNHCR-style datasets: `resettlement.csv`,
`asylum_seekers_monthly.csv`, `demographics.csv`, `asylum_seekers.csv`,
`persons_of_concern.csv`, and `time_series.csv`. Combined raw rows: **905,102**.

## Core data decisions

1. Reported zero values are preserved as valid observations.
2. Redacted values (`*`), blanks, parse failures and impossible negative counts are converted to missing values and tracked through explicit flags.
3. Country names are standardised and enriched with ISO3 codes where possible.
4. Historical/composite entities are retained for ranked analysis but marked as `map_eligible_flag = False`.
5. Population-stock datasets (`time_series.csv`, `persons_of_concern.csv`) are kept separate from flow datasets (`asylum_seekers.csv`, `asylum_seekers_monthly.csv`, `resettlement.csv`).

## Numeric quality summary

- Zero cells preserved: **900,941**
- Blank cells flagged: **706,435**
- Redacted star cells flagged: **49,805**
- Negative raw cells set to missing: **4**

## Why this matters for the dashboard

The dashboard combines time, geography, origin-destination relationships and multiple population categories. Clean ISO3 fields support maps; missingness flags support transparent reporting; and the separation between stock and flow metrics prevents misleading comparisons.

## Hard checks

| check                                                | status     | detail                                                                                 |
|:-----------------------------------------------------|:-----------|:---------------------------------------------------------------------------------------|
| no_row_loss__resettlement                            | PASS       | raw=9075, clean=9075                                                                   |
| no_row_loss__asylum_seekers_monthly                  | PASS       | raw=332189, clean=332189                                                               |
| no_row_loss__demographics                            | PASS       | raw=18356, clean=18356                                                                 |
| no_row_loss__asylum_seekers                          | PASS       | raw=129720, clean=129720                                                               |
| no_row_loss__persons_of_concern_wide                 | PASS       | raw=117321, clean=117321                                                               |
| no_row_loss__time_series                             | PASS       | raw=298441, clean=298441                                                               |
| no_negative_observed_values__resettlement            | PASS       | negative_cells=0                                                                       |
| no_negative_observed_values__asylum_seekers_monthly  | PASS       | negative_cells=0                                                                       |
| no_negative_observed_values__demographics            | PASS       | negative_cells=0                                                                       |
| no_negative_observed_values__asylum_seekers          | PASS       | negative_cells=0                                                                       |
| no_negative_observed_values__persons_of_concern_wide | PASS       | negative_cells=0                                                                       |
| no_negative_observed_values__persons_of_concern_long | PASS       | negative_cells=0                                                                       |
| no_negative_observed_values__time_series             | PASS       | negative_cells=0                                                                       |
| country_mapping_unmapped_rows                        | PASS       | unique_unmapped_values=0; see 00_audit/unmapped_country_values.csv                     |
| asylum_decision_total_mismatch_documented            | DOCUMENTED | rows=1782; reported totals are retained, missing totals are recomputed from components |
| literal_NA_rsd_stage_protected                       | PASS       | raw '/ NA' rows=2234, parsed NEW rows=2234                                             |