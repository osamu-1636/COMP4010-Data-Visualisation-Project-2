# Final Checklist

Before demo / submission:

```powershell
python tests\test_smoke.py
python tests\test_json_safety.py
python tests\test_data_contract.py
python -m py_compile app.py
python -m shiny run --launch-browser --port 8050 app.py
```

Manual checks:

- Reset works.
- Apply filters works.
- Top N = 12 for clean demo.
- Graph 1 moving dots appear.
- Graph 4 Sankey appears.
- Treemap appears after Graph 6.
- Distance analytics appears and is explained as spatial analytics / feature-engineering baseline, not causal ML.
- Crisis case route map works for Syrian Civil War and Iraq conflict.
- No Shiny Client Error popup.
