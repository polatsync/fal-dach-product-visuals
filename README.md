# fal-dach-product-visuals

A small demo of how a **DACH e-commerce merchant** could use [fal](https://fal.ai) to create market-specific product visuals from an existing German product catalog — written from an account manager's point of view: what the customer gets, what it costs, and what their legal and security teams will ask.

## The customer scenario

A mid-size online shop sells in Germany, Austria and Switzerland. Product photos are expensive to shoot and look the same in every market. The shop wants:

- localized visuals per market (DE / AT / CH style presets) from one catalog,
- predictable cost per image, so finance can approve a budget,
- a pipeline its engineers can run in batch without managing GPUs.

## What the script does

1. Reads `products_de.csv` (SKU, German name, short description, category).
2. Builds one prompt per product **and** market style.
3. Calls a fal image model (default `fal-ai/flux/schnell`) through the official `fal-client` library.
4. Writes `report.csv` with the image URL, latency and estimated cost per image, and prints totals.

```bash
pip install -r requirements.txt
export FAL_KEY="your-fal-api-key"
python generate.py --input products_de.csv --out report.csv

# Try it without an API key (builds prompts and the report only):
python generate.py --dry-run
```

Options: `--model` (any fal image endpoint), `--markets DE,AT` (subset), `--cost-per-image` (set it from current fal pricing for the chosen model — the default is only a placeholder).

## Why this matters commercially

| Customer question | How the demo answers it |
|---|---|
| "What will it cost per SKU?" | `report.csv` has cost per image; multiply by catalog size × markets. |
| "Is it fast enough for batch runs?" | Latency is measured per request; failures are logged, the batch continues. |
| "Can we start small?" | `--markets DE` and a 5-SKU sample file = a pilot in minutes. |
| "Where does it grow?" | More markets, more SKUs, seasonal campaigns, video models — usage expands with the catalog. |

## What EU legal & security will ask (renewal and procurement checklist)

From my work as an ISO 27001 Lead Auditor and CISA, these are the questions a DACH enterprise customer typically raises before signing or renewing:

- **Data processing:** Is a DPA (Art. 28 GDPR) in place? Which sub-processors and regions are involved?
- **Input data:** Do prompts or uploaded images contain personal data? (This demo sends product data only.)
- **Retention:** How long are generated assets and request logs stored? Who can access the URLs?
- **Security evidence:** Which certifications or reports can be shared (e.g. SOC 2, ISO 27001), and how are API keys managed and rotated?
- **IP & content:** Usage rights for generated assets and model licences for commercial use.

Having these answers ready shortens procurement and renewal cycles — that is where an account manager adds value beyond the technical pilot.

## Files

- `generate.py` — the pipeline (Python 3.9+)
- `products_de.csv` — 5 sample products in German
- `.env.example` — where the API key goes (never commit real keys)

---
Built by Abdullah Polat — Manager, IT & Business Process Assurance at PwC (TR/DACH) · ISO 27001 Lead Auditor · CISA · German C2
