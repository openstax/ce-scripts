# Content Engineering Scripts

A central location to store content engineering scripts used for ad-hoc purposes and for posterity.


## Scripts contained herein

### Python

| script                       | description                                                                                                                 |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| `self_close_xpath_search.py` | Used to do xpath searches (self closing tags) on html content via archive. Exports results to a csv in `./output`           |
| `double_barrel_selenium.py`  | Uses the results from the previous script to open 1 or 2 browser windows for visual comparison. Exports results with PASS/FAIL in `./output` |
