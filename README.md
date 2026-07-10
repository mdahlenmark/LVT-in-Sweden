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

`config/scb_baseline_tables.json` lists the required source roles and search terms. The `fetch` command now tries to select tables automatically from the SCB PxWeb tree when a dataset has no `path`:

1. It starts at the configured `api_base` (`https://api.scb.se/OV0104/v1/doris/en/ssd`).
2. It walks the PxWeb navigation tree. Folder nodes are opened recursively; table nodes are ranked against the dataset `search_terms`.
3. If one table is clearly the best match, `fetch` prints `auto-selected <dataset>: <path>` and downloads it immediately.
4. If several tables are tied, `fetch` prints candidate paths and skips that dataset so you can choose the intended table manually.

To manually choose a table, browse the same tree in a browser or with the API: open `api_base`, click/open folders matching the dataset subject, and copy the slash-separated table path made from the node `id` values. Add that path to the dataset entry as `path`, for example:

```json
{
  "name": "population",
  "path": "BE/BE0101/BE0101A/BefolkningNy"
}
```

Configured `path` values always win over automatic discovery, which makes future runs reproducible after you have selected the exact SCB tables.

## Run

This project uses a `src/` package layout, so install it into your active
Python environment before running the CLI from a checkout:

```bash
python -m pip install -e .
```

On Windows, from PowerShell, use the same interpreter you will use to run the
commands, for example:

```powershell
py -m pip install -e .
```

If you prefer not to install the package, set `PYTHONPATH` for the current shell before using `python -m`:

```powershell
$env:PYTHONPATH = "src"
python -m scb_lvt.cli fetch --manifest config/scb_baseline_tables.json
```

After installation, either invoke the console script:

```bash
scb-lvt fetch --manifest config/scb_baseline_tables.json
scb-lvt build --target property_prices
```

or run the module explicitly:

```bash
python -m scb_lvt.cli fetch --manifest config/scb_baseline_tables.json
python -m scb_lvt.cli build --target property_prices
```

`fetch` stores raw SCB JSON under `data/raw/scb/` and flattened CSVs under `data/processed/`. `build` normalizes each measure, joins the modelling panel, and writes a simple univariate baseline summary to `models/scb_baseline.txt`.
