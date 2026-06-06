# Final Merge Notes

This final codebase merges two directions:

## Friend/GitHub contributions preserved

- Clean modular Python Shiny architecture.
- Thin `app.py`.
- Service-layer data loading and output contract.
- Reactive state with Apply/Reset filters.
- Chart-ready EDA handoff.
- Test suite and Windows run instructions.

## Final dashboard improvements added

- Reduced story from repeated host maps/rankings to eight focused sections.
- Restored Graph 4 Sankey because it adds a distinct chart type and explains corridor structure.
- Added host treemap after Graph 6 to answer concentration instead of repeating another host bar.
- Added distance-band analytics to answer whether crisis displacement is near/regional/far.
- Added lightweight moving dots on route maps and cover motion, while avoiding Plotly frames.

## What is intentionally excluded from final demo

- Network graph.
- Role matrix.
- Monthly/demographic/resettlement appendix charts unless needed in report/Q&A.
- Animated choropleth with Plotly frames.
- Heavy WebGL/PyDeck iframe experiments.

## Final narrative

Scale -> Geography -> Corridors -> Rankings -> Concentration -> Distance analytics -> Crisis case -> Method.
