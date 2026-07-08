# LVT in Sweden

This repository starts with a reproducible, no-key baseline for a Swedish land-value-tax model using SCB open data.

## Baseline scope

The first model is intentionally aggregate and transparent:

- **Targets:** SCB aggregate property price / purchase-price coefficient tables by municipality or county.
- **Market activity:** SCB title registration (`lagfart`) counts or values at the same geography/year grain.
- **Controls:** demographic and income tables, initially population and municipal/county income statistics.
- **Join key:** `region_code` + `year`, yielding `data/processed/scb_baseline_model.csv`.

The pipeline avoids provider credentials. Future parcel, tax-assessment, or listings integrations should be added as separate opt-in sources.

## Configure SCB tables

`config/scb_baseline_tables.json` lists the required source roles and search terms. Add the current SCB table path for each dataset as `path` once selected from the SCB PxWeb tree, for example:

```json
{
  "name": "population",
  "path": "BE/BE0101/BE0101A/BefolkningNy"
}
```

## Run

```bash
python -m scb_lvt.cli fetch --manifest config/scb_baseline_tables.json
python -m scb_lvt.cli build --target property_prices
```

`fetch` stores raw SCB JSON under `data/raw/scb/` and flattened CSVs under `data/processed/`. `build` normalizes each measure, joins the modelling panel, and writes a simple univariate baseline summary to `models/scb_baseline.txt`.
