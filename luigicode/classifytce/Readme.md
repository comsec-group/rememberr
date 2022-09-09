First, create an env var ERRATA_USERNAME (for example `human2`).

Classify using for example:

```bash
python3 -m classifytce.classify
```

To see statistics of how many errata must be classified manually, were filtered in or out:

```bash
python3 -m classifytce.filterpercentages
```
