"""
fal-dach-product-visuals
------------------------
Generate localized product visuals for a DACH e-commerce catalog with fal.

Reads a product CSV (German product names + short descriptions), builds a
prompt per product and market style, calls a fal image model, and writes a
report with image URLs, latency and an estimated cost per image.

Usage:
    export FAL_KEY="your-fal-api-key"
    python generate.py --input products_de.csv --out report.csv
    python generate.py --input products_de.csv --dry-run   # no API calls
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from dataclasses import dataclass, asdict

DEFAULT_MODEL = "fal-ai/flux/schnell"

# Style presets per market. A real customer would tune these with their
# brand team; they are here to show how one catalog can serve several markets.
MARKET_STYLES = {
    "DE": "clean, minimal studio look, neutral light background, high detail",
    "AT": "warm alpine living-room setting, natural wood, soft daylight",
    "CH": "premium, understated Swiss design, bright and precise lighting",
}


@dataclass
class Product:
    sku: str
    name_de: str
    description_de: str
    category: str


@dataclass
class Result:
    sku: str
    market: str
    model: str
    prompt: str
    image_url: str
    seconds: float
    est_cost_usd: float
    status: str


def load_products(path: str) -> list[Product]:
    with open(path, newline="", encoding="utf-8") as f:
        return [Product(**row) for row in csv.DictReader(f)]


def build_prompt(p: Product, market: str) -> str:
    style = MARKET_STYLES[market]
    return (
        f"Professional e-commerce product photo of {p.name_de} "
        f"({p.description_de}), category: {p.category}. {style}. "
        "No text, no watermark, product centered."
    )


def generate(p: Product, market: str, model: str, cost_per_image: float,
             dry_run: bool) -> Result:
    prompt = build_prompt(p, market)
    if dry_run:
        return Result(p.sku, market, model, prompt, "", 0.0, 0.0, "dry-run")

    import fal_client  # imported here so --dry-run works without the package

    start = time.perf_counter()
    try:
        out = fal_client.subscribe(
            model,
            arguments={"prompt": prompt, "image_size": "square_hd",
                       "num_images": 1},
            client_timeout=120,  # don't let one stuck request block the batch
        )
        url = out["images"][0]["url"]
        status = "ok"
    except Exception as exc:  # keep the batch running, log the failure
        url, status = "", f"error: {exc}"
    seconds = round(time.perf_counter() - start, 2)
    cost = cost_per_image if status == "ok" else 0.0
    return Result(p.sku, market, model, prompt, url, seconds, cost, status)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default="products_de.csv")
    ap.add_argument("--out", default="report.csv")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--markets", default="DE,AT,CH",
                    help="comma-separated subset of DE,AT,CH")
    ap.add_argument("--cost-per-image", type=float, default=0.003,
                    help="USD per image for the chosen model; check fal pricing")
    ap.add_argument("--dry-run", action="store_true",
                    help="build prompts and the report without calling fal")
    args = ap.parse_args()

    if not args.dry_run and not os.getenv("FAL_KEY"):
        print("FAL_KEY is not set. Use --dry-run or export your fal API key.",
              file=sys.stderr)
        return 1

    markets = [m.strip().upper() for m in args.markets.split(",") if m.strip()]
    unknown = [m for m in markets if m not in MARKET_STYLES]
    if unknown:
        print(f"Unknown market(s): {', '.join(unknown)}", file=sys.stderr)
        return 1

    products = load_products(args.input)
    results = [generate(p, m, args.model, args.cost_per_image, args.dry_run)
               for p in products for m in markets]

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(asdict(results[0]).keys()))
        w.writeheader()
        w.writerows(asdict(r) for r in results)

    ok = [r for r in results if r.status == "ok"]
    print(f"{len(results)} requests, {len(ok)} succeeded -> {args.out}")
    if ok:
        avg = sum(r.seconds for r in ok) / len(ok)
        total = sum(r.est_cost_usd for r in ok)
        print(f"avg latency {avg:.2f}s, est. cost ${total:.3f} "
              f"(${total / len(ok):.4f} per image)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
