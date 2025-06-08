#!/usr/bin/env python
"""
Synthetic POS CSV Generator
────────────────────────────────────────────
$ python make_dummy_csv.py --type=cafe --num-data=10  [-o output.csv]
   • --type       {cafe | cvs}
   • --num-data   # rows to generate
   • --out / -o   optional output filename (default auto-naming)
────────────────────────────────────────────
"""
import argparse
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# ╭─ util ─────────────────────────────────────────────────────────┐
def _random_dates(start: str, end: str, n: int) -> pd.Series:
    start_dt = pd.Timestamp(start)
    end_dt   = pd.Timestamp(end)
    days     = (end_dt - start_dt).days
    return pd.to_datetime(
        np.random.randint(0, days + 1, n), unit="D", origin=start_dt
    ).normalize()

def _random_times(n: int) -> pd.Series:
    secs = np.random.randint(0, 86_400, n)   # seconds in a day
    return pd.to_timedelta(secs, unit="s").astype(str)
# ╰─────────────────────────────────────────────────────────────────╯

# ╭─ Café generator ───────────────────────────────────────────────╮
CAFE_SIZES  = ["S", "M", "L"]
CAFE_TEMP   = ["Hot", "Iced"]
MILK_TYPES  = ["Regular", "Low-fat", "Soy", "Oat"]
PAY_TYPES   = ["Card", "Cash", "MobilePay"]

def make_cafe_pos(num_data: int = 100) -> pd.DataFrame:
    rng = np.random.default_rng()
    df = pd.DataFrame({
        "transaction_id": rng.integers(1_000_000, 9_999_999, num_data),
        "date"          : _random_dates("2025-01-01", "2025-12-31", num_data),
        "time"          : _random_times(num_data),
        "channel"       : rng.choice(["Store", "DeliveryApp", "Kiosk"], num_data),
        "item_name"     : rng.choice(
            ["Americano", "Latte", "Cappuccino", "Mocha", "Tea", "Smoothie"], num_data),
        "size"          : rng.choice(CAFE_SIZES, num_data),
        "temperature"   : rng.choice(CAFE_TEMP,  num_data),
        "shot_count"    : rng.integers(1, 4, num_data),
        "milk_type"     : rng.choice(MILK_TYPES, num_data),
        "syrup_pumps"   : rng.integers(0, 4, num_data),
        "topping"       : rng.choice(
            ["None", "Whipped Cream", "Bubble", "Cheese Cap"], num_data),
        "qty"           : 1,
        "unit_price"    : rng.integers(3000, 7000, num_data),
    })
    df["total_price"]  = df["qty"] * df["unit_price"]
    df["payment_type"] = rng.choice(PAY_TYPES, num_data)
    return df.reset_index(drop=True)
# ╰─────────────────────────────────────────────────────────────────╯

# ╭─ Convenience-store generator ──────────────────────────────────╮
CVS_CAT_L1 = ["Snack", "Beverage", "Daily", "Frozen", "Alcohol", "Cigarette"]
CVS_PAY    = ["Card", "Cash", "Voucher", "Prepaid"]

def make_cvs_pos(num_data: int = 100) -> pd.DataFrame:
    rng = np.random.default_rng()
    df = pd.DataFrame({
        "transaction_id": rng.integers(1_000_000, 9_999_999, num_data),
        "date"          : _random_dates("2025-01-01", "2025-12-31", num_data),
        "time"          : _random_times(num_data),
        "channel"       : rng.choice(["Counter", "Self-Checkout"], num_data),
        "barcode"       : rng.integers(8800000000000, 8800999999999, num_data),
        "item_name"     : rng.choice(
            ["Chips", "Chocolate", "Soda", "Energy Drink",
             "Sandwich", "Ice cream", "Beer", "Cigarette"], num_data),
        "category_lv1"  : rng.choice(CVS_CAT_L1, num_data),
        "brand"         : rng.choice(
            ["Lotte", "PepsiCo", "Coca-Cola", "Nestlé", "Local"], num_data),
        "pack_size"     : rng.choice(["350 mL", "500 mL", "1 L", "60 g", "120 g"], num_data),
        "qty"           : rng.integers(1, 4, num_data),
        "unit_price"    : rng.integers(1000, 5000, num_data),
        "promo_flag"    : rng.choice([0, 1], num_data, p=[0.8, 0.2]),
        "age_restricted": rng.choice([0, 1], num_data, p=[0.7, 0.3]),
    })
    df["total_price"]  = df["qty"] * df["unit_price"]
    df["payment_type"] = rng.choice(CVS_PAY, num_data)
    return df.reset_index(drop=True)
# ╰─────────────────────────────────────────────────────────────────╯

# ╭─ CLI entry ────────────────────────────────────────────────────╮
def _parse_args():
    p = argparse.ArgumentParser(description="Generate dummy POS CSV data")
    p.add_argument("--type", choices=["cafe", "cvs"], required=True,
                   help="Business type to generate (cafe or cvs)")
    p.add_argument("--num-data", type=int, default=100,
                   help="Number of rows to generate (default: 100)")
    p.add_argument("-o", "--out", metavar="FILE",
                   help="Output CSV filename (optional)")
    return p.parse_args()

def main():
    args = _parse_args()
    gen = make_cafe_pos if args.type == "cafe" else make_cvs_pos
    df  = gen(args.num_data)

    out_path = Path(args.out) if args.out else \
        Path(f"{args.type}_pos_dummy_{datetime.now():%Y%m%d_%H%M%S}.csv")
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"✔ Generated {len(df):,} rows → {out_path}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
