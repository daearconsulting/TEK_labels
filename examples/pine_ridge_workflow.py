"""
pine_ridge_workflow.py
End-to-end demonstration of the localcontexts-geo toolkit.
Shows the complete pattern for a geospatial analysis workflow on
Indigenous lands from data ingest with TK label attachment through
transformation, validation, and export with IEEE 2890-2025 aligned
provenance.

Subject: Pine Ridge Reservation, Oglala Lakota Nation
Data: Synthetic NDVI time series (no real data downloads required)
Run: python examples/pine_ridge_workflow.py

Author: Lilly Jones, PhD, Daear Consulting, LLC
"""

from __future__ import annotations

import datetime
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

# Imports
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from localcontexts.labels import TKLabel, TKMetadata
from localcontexts.propagation import (
    propagate_labels,
    add_provenance_step,
    enforce_label_propagation,
)
from localcontexts.validation import (
    validate_usage,
    validate_label_present,
    validate_provenance_intact,
    validate_export_ready,
    check_collective_benefit,
    check_authority_to_control,
    TKViolationError,
)
from localcontexts.provenance import (
    ProvenanceOrigin,
    ProvenanceRecord,
    build_sidecar_path,
    attach_provenance_to_meta,
)

warnings.filterwarnings("ignore")

OUTPUT_DIR = REPO_ROOT/"outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Separator helper
def section(title: str) -> None:
    print(f"  {title}")
    
# ORIGIN: Define where data came from and who it is about

section("ORIGIN")

origin = ProvenanceOrigin(
    subject        = "NDVI time series for Pine Ridge, Oglala Lakota Nation",
    community      = "Oglala Lakota Nation",
    territory      = "Pine Ridge Reservation, South Dakota",
    source_name    = "MODIS MOD13Q1 V061 via ORNL DAAC",
    source_url     = "https://modis.ornl.gov/rst/api/v1/",
    source_steward = "NASA ORNL DAAC",
    obtained_date  = datetime.date.today().isoformat(),
    tk_label       = TKLabel.NON_COMMERCIAL.value,
    label_authority= "Tribal Data Governance Office, Oglala Lakota Nation",
    license        = "NASA open data policy for non-commercial research",
    access_conditions = (
        "TK Non-Commercial label applies. Results must be shared with "
        "the Tribal Data Governance Office before publication."
    ),
)

print(f"Subject   : {origin.subject}")
print(f"Community : {origin.community}")
print(f"TK Label  : {origin.tk_label}")


# INGEST: Attach TK label and initialize provenance record

section("INGEST")

# Define the TK label
tk = TKMetadata(
    label     = TKLabel.NON_COMMERCIAL,
    community = origin.community,
    authority = origin.label_authority,
    usage     = origin.access_conditions,
    contact   = "data@oglalalakota.org",
    notes     = "Derived datasets must retain this label.",
)

# Initialize provenance record
record = ProvenanceRecord(dataset_name="pine_ridge_ndvi_2000_2023", origin=origin)

# Simulate data ingest (synthetic data no API call needed)
np.random.seed(42)
dates = pd.date_range("2000-02-18", "2023-12-31", freq="16D")
ndvi_values = (
    np.sin((dates.dayofyear / 365 - 0.3) * 2 * np.pi) * 0.2 + 0.38
    + np.random.normal(0, 0.03, len(dates))
).clip(0.05, 0.85)

# Add drought signal in known drought years
drought_mask = dates.year.isin([2002, 2012, 2021])
ndvi_values[drought_mask] -= 0.07

raw_df = pd.DataFrame({"date": dates, "ndvi": ndvi_values.round(4)})

# Build initial metadata by attaching TK label immediately at ingest
dataset_meta = tk.attach({
    "name":         "pine_ridge_ndvi_2000_2023",
    "source":       origin.source_name,
    "n_obs":        len(raw_df),
    "date_range":   f"{raw_df['date'].min().date()} to {raw_df['date'].max().date()}",
    "spatial_res":  "250m point centroid average",
    "temporal_res": "16-day composite",
})

record.add_step(
    process  = "Data ingested: MODIS MOD13Q1 via ORNL DAAC MODIS Web Service",
    inputs   = ["ORNL DAAC API (MOD13Q1, lat=43.35, lon=-102.09, 2000-2023)"],
    outputs  = ["pine_ridge_ndvi_2000_2023 (in memory)"],
    notes    = "Synthetic data used in this example script.",
)

print(f"Ingested  : {len(raw_df):,} observations")
print(f"TK label  : {dataset_meta.get('tk:label')}")
print(f"Label OK  : {validate_label_present(dataset_meta, context='raw NDVI', warn_only=False)}")


# VALIDATE USE: Confirm intended use before analysis

section("STAGE 3: VALIDATE INTENDED USE")

INTENDED_USE = "research"

try:
    validate_usage(dataset_meta, intended_use=INTENDED_USE)
    print(f"Use '{INTENDED_USE}': PERMITTED by TK label")
except TKViolationError as e:
    print(f"Use '{INTENDED_USE}': BLOCKED {e}")
    sys.exit(1)

# Demonstrate commercial use rejection
try:
    validate_usage(dataset_meta, intended_use="commercial")
    print("Commercial use: PERMITTED")
except TKViolationError:
    print("Commercial use: BLOCKED (correct TK Non-Commercial label)")


# TRANSFORM: Process with label propagation at each step

section("TRANSFORM")


@enforce_label_propagation(meta_arg="meta")
def resample_to_monthly(df: pd.DataFrame, meta: dict) -> tuple[pd.DataFrame, dict]:
    """Resample 16-day NDVI to monthly means."""
    monthly = (
        df.set_index("date")["ndvi"]
        .resample("MS")
        .mean()
        .reset_index()
        .rename(columns={"index": "date"})
    )
    output_meta = {
        "name":         meta["name"].replace("_2000_2023", "_monthly"),
        "temporal_res": "monthly mean",
        "n_obs":        len(monthly),
    }
    return monthly, output_meta


@enforce_label_propagation(meta_arg="meta")
def compute_annual_gs_mean(
    df: pd.DataFrame, meta: dict,
    growing_months: list[int] = None,
) -> tuple[pd.DataFrame, dict]:
    """Compute annual growing season mean NDVI (May–September)."""
    if growing_months is None:
        growing_months = [5, 6, 7, 8, 9]
    gs = df[df["date"].dt.month.isin(growing_months)].copy()
    annual = (
        gs.groupby(gs["date"].dt.year)["ndvi"]
        .mean()
        .reset_index()
        .rename(columns={"date": "year"})
    )
    output_meta = {
        "name":           meta["name"].replace("_monthly", "_annual_gs"),
        "growing_months": str(growing_months),
        "n_years":        len(annual),
    }
    return annual, output_meta


@enforce_label_propagation(meta_arg="meta")
def compute_anomaly(
    df: pd.DataFrame, meta: dict,
) -> tuple[pd.DataFrame, dict]:
    """Compute NDVI anomaly (departure from long-term mean)."""
    long_term_mean = df["ndvi"].mean()
    out = df.copy()
    out["ndvi_anomaly"]    = (out["ndvi"] - long_term_mean).round(4)
    out["long_term_mean"]  = round(long_term_mean, 4)
    output_meta = {
        "name":            meta["name"].replace("_annual_gs", "_anomaly"),
        "long_term_mean":  round(long_term_mean, 4),
        "process":         "anomaly = annual_gs_ndvi - long_term_mean",
    }
    return out, output_meta


# Run the transformation pipeline
monthly_df,  monthly_meta  = resample_to_monthly(raw_df, dataset_meta)
annual_df,   annual_meta   = compute_annual_gs_mean(monthly_df, monthly_meta)
anomaly_df,  anomaly_meta  = compute_anomaly(annual_df, annual_meta)

# Add provenance steps to the record
record.add_step(
    process = "Resample: 16-day to monthly mean NDVI",
    inputs  = ["pine_ridge_ndvi_2000_2023"],
    outputs = [monthly_meta["name"]],
)
record.add_step(
    process = f"Annual growing season mean (months {annual_meta.get('growing_months')})",
    inputs  = [monthly_meta["name"]],
    outputs = [annual_meta["name"]],
)
record.add_step(
    process = f"Anomaly: annual GS NDVI minus {anomaly_meta.get('long_term_mean')} (long-term mean)",
    inputs  = [annual_meta["name"]],
    outputs = [anomaly_meta["name"]],
)

# Verify label survived every step
for name, meta in [
    ("monthly",  monthly_meta),
    ("annual_gs", annual_meta),
    ("anomaly",  anomaly_meta),
]:
    validate_provenance_intact(meta)
    print(f"  {name:<12}: TK label intact {meta.get('tk:label')}")


# CARE COMPLIANCE: Document community benefit and consent

section("CARE COMPLIANCE")

final_meta = dict(anomaly_meta)

check_collective_benefit(
    final_meta,
    benefit_description=(
        "Results will be shared with the Oglala Lakota Nation Natural "
        "Resources Department in plain-language format to support "
        "drought planning and land management decision-making."
    ),
)

check_authority_to_control(
    final_meta,
    consent_obtained    = True,
    consent_description = (
        "Research agreement with OST Natural Resources Department signed "
        f"{datetime.date.today()}. OST NRD has approved this analysis."
    ),
)

print(f"  care:collective_benefit: {bool(final_meta.get('care:collective_benefit'))}")
print(f"  care:consent_obtained  : {final_meta.get('care:consent_obtained')}")


# EXPORTS: Write output with embedded provenance

section("EXPORTS")

# Pre-export validation
report = validate_export_ready(
    final_meta,
    intended_use    = INTENDED_USE,
    destination     = "OST Natural Resources Department and GitHub repository",
    require_contact = True,
)

for check in report["checks"]:
    status = "Passed" if check["passed"] else "Did not pass"
    print(f"  {status} {check['check']}: {check['note']}")

if not report["all_passed"]:
    print("\nExport blocked: resolve issues above before proceeding.")
    sys.exit(1)

# Attach full provenance record to metadata
final_meta = attach_provenance_to_meta(final_meta, record)

# Write output CSV
output_csv = OUTPUT_DIR/"pine_ridge_ndvi_anomaly.csv"
anomaly_df.to_csv(output_csv, index=False)
print(f"\n  Output CSV    : {output_csv}")

# Write provenance sidecar JSON
sidecar_path = build_sidecar_path(output_csv)
record.save(sidecar_path)
print(f"  Provenance    : {sidecar_path}")

# Write human-readable metadata JSON
metadata_out = OUTPUT_DIR/"pine_ridge_ndvi_anomaly_metadata.json"
metadata_out.write_text(json.dumps(
    {k: str(v) for k, v in final_meta.items() if k != "prov:record"},
    indent=2,
))
print(f"  Metadata JSON : {metadata_out}")


# VERIFY: Reload and confirm provenance chain

section("VERIFY")

from localcontexts.provenance import ProvenanceRecord as _PR

reloaded_record = _PR.load(sidecar_path)
reloaded_df     = pd.read_csv(output_csv)

print(f"  Dataset      : {reloaded_record.dataset_name}")
print(f"  Community    : {reloaded_record.origin.community}")
print(f"  TK Label     : {reloaded_record.origin.tk_label}")
print(f"  Chain steps  : {len(reloaded_record.chain)}")
print(f"  IEEE 2890    : {reloaded_record.ieee_2890}")
print(f"  CARE aligned : {reloaded_record.care_aligned}")
print(f"  Rows in CSV  : {len(reloaded_df)}")
print()
print("  Provenance chain:")
for i, step in enumerate(reloaded_record.chain, 1):
    print(f"    {i}. {step.process}")


# SUMMARY

section("COMPLETE")

print("""
Full lifecycle demonstrated:

  ORIGIN      : documented who data is about and where it came from
  INGEST      : TK Non-Commercial label attached at load time
  VALIDATE    : intended use checked against label before analysis
  TRANSFORM   : label propagated through all transformation steps
  CARE        : Collective Benefit and Authority to Control documented
  EXPORT      : pre-export validation passed; CSV and sidecar written
  VERIFY      : provenance chain reloaded and confirmed intact

Governance facts about this output:
""")
print(f"  Community    : {reloaded_record.origin.community}")
print(f"  TK Label     : {reloaded_record.origin.tk_label}")
print(f"  Permitted use: non-commercial research only")
print(f"  Contact      : {final_meta.get('tk:contact', 'data@oglalalakota.org')}")
print(f"  IEEE 2890    : https://standards.ieee.org/ieee/2890/10318/")
