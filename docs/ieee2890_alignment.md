# IEEE 2890-2025 Alignment
This document describes how the `localcontexts-geo` provenance chain
maps to the parameters established by IEEE 2890-2025.

**Standard reference:** https://standards.ieee.org/ieee/2890/10318/

## What Is IEEE 2890-2025?
IEEE 2890-2025 *Recommended Practice for Provenance of Indigenous
Peoples' Data* is the first international standard specifically
addressing the provenance of data about Indigenous Peoples.

Published November 2025 by the IEEE Standards Association, it establishes:
- **Common parameters** for describing how Indigenous Peoples' data
  should be disclosed and governed
- **Controlled vocabulary** for provenance metadata applicable across
  sectors including AI/ML and biodiversity science
- **Connection requirements**: how data should be connected to the
  people and place it describes
- **Lifecycle governance**: how responsibilities travel with data
  through transformations
- **Interoperability**: alignment with CARE, FAIR, and Local Contexts

## IEEE 2890-2025 Parameters
The standard identifies key provenance parameters that should accompany
any dataset about Indigenous Peoples. The table below shows how each
parameter maps to the `localcontexts-geo` implementation.

| IEEE 2890-2025 Parameter | Description | localcontexts-geo field |
|---|---|---|
| **Subject** | What the data is about | `ProvenanceOrigin.subject` |
| **Community** | Which Indigenous community the data concerns | `ProvenanceOrigin.community` + `tk:community` |
| **Territory** | Geographic connection to Indigenous lands | `ProvenanceOrigin.territory` |
| **Source** | Where the data came from | `ProvenanceOrigin.source_name`, `source_url` |
| **Steward** | Who manages the source data | `ProvenanceOrigin.source_steward` |
| **Obtained** | When data was accessed | `ProvenanceOrigin.obtained_date` |
| **Cultural authority** | What governance label applies | `tk:label`, `bc:label` |
| **Label authority** | Who assigned the label | `ProvenanceOrigin.label_authority` + `tk:authority` |
| **Access conditions** | How data may be used | `ProvenanceOrigin.access_conditions` and `tk:usage` |
| **Transformation history** | What happened to the data | `ProvenanceRecord.chain` |
| **Governance lineage** | How responsibilities traveled | `propagate_labels()` at each step |
| **Machine-readable** | Can a system parse this? | `ProvenanceRecord.to_json()` |

## Implementing IEEE 2890-2025 in localcontexts-geo

### Create a ProvenanceOrigin
The `ProvenanceOrigin` object captures the root provenance parameters
required by IEEE 2890-2025:

```python
from localcontexts.provenance import ProvenanceOrigin
from localcontexts.labels import TKLabel

origin = ProvenanceOrigin(
    # What the data is about (IEEE 2890: subject)
    subject        = "NDVI time series for Pine Ridge, Oglala Lakota Nation",

    # Who the data concerns (IEEE 2890: community, territory)
    community      = "Oglala Lakota Nation",
    territory      = "Pine Ridge Reservation, South Dakota",

    # Where it came from (IEEE 2890: source, steward)
    source_name    = "MODIS MOD13Q1 V061 via ORNL DAAC",
    source_url     = "https://modis.ornl.gov/rst/api/v1/",
    source_steward = "NASA ORNL DAAC",

    # When it was obtained (IEEE 2890: obtained)
    obtained_date  = "2024-06-01",

    # Cultural authority (IEEE 2890: governance label)
    tk_label       = TKLabel.NON_COMMERCIAL.value,
    label_authority= "Tribal Data Governance Office, Oglala Lakota Nation",

    # Use conditions (IEEE 2890: access conditions)
    access_conditions = "Non-commercial research only; share results with TDG Office",
)
```

### Build a ProvenanceRecord
The `ProvenanceRecord` holds the origin and an ordered chain of
transformation steps:

```python
from localcontexts.provenance import ProvenanceRecord

record = ProvenanceRecord(
    dataset_name = "pine_ridge_ndvi_2000_2023",
    origin       = origin,
    care_aligned = True,  
)
```

### Add Steps at Each Transformation
Each transformation is recorded as a `ProvenanceStep`:

```python
record.add_step(
    process  = "Resample: 16-day NDVI to monthly mean",
    workflow = "notebook_03_raster_workflows.ipynb",
    inputs   = ["pine_ridge_ndvi_raw.csv"],
    outputs  = ["pine_ridge_ndvi_monthly.csv"],
    notes    = "Growing season months only (May–Sep).",
)

record.add_step(
    process  = "Compute anomaly: annual GS NDVI minus 2000–2023 mean",
    workflow = "notebook_03_raster_workflows.ipynb",
    inputs   = ["pine_ridge_ndvi_monthly.csv"],
    outputs  = ["pine_ridge_ndvi_anomaly.csv"],
)
```

### Save as Machine-Readable Sidecar
The provenance record is saved as a JSON sidecar file alongside the output:

```python
from localcontexts.provenance import build_sidecar_path

sidecar_path = build_sidecar_path(output_path)
# ex. pine_ridge_ndvi_anomaly.provenance.json

record.save(sidecar_path)
```

### Reload and Verify
Any downstream system can load and verify the provenance chain:

```python
reloaded = ProvenanceRecord.load(sidecar_path)
print(reloaded.summary())
# Provenance Record: pine_ridge_ndvi_2000_2023
# Community: Oglala Lakota Nation
# TK Label: TK Non-Commercial
# Steps: 3
# ...
```

## Sidecar JSON Structure
The sidecar JSON produced by `record.save()` follows this structure,
aligned with IEEE 2890-2025 parameters:

```json
{
  "dataset_name": "pine_ridge_ndvi_2000_2023",
  "ieee_2890": "https://standards.ieee.org/ieee/2890/10318/",
  "care_aligned": true,
  "created_at": "2024-06-01T12:00:00+00:00",
  "updated_at": "2024-06-01T12:05:00+00:00",
  "origin": {
    "subject": "NDVI time series for Pine Ridge, Oglala Lakota Nation",
    "community": "Oglala Lakota Nation",
    "territory": "Pine Ridge Reservation, South Dakota",
    "source_name": "MODIS MOD13Q1 V061 via ORNL DAAC",
    "source_url": "https://modis.ornl.gov/rst/api/v1/",
    "source_steward": "NASA ORNL DAAC",
    "obtained_date": "2024-06-01",
    "tk_label": "TK Non-Commercial",
    "label_authority": "Tribal Data Governance Office, Oglala Lakota Nation",
    "access_conditions": "Non-commercial research only"
  },
  "chain": [
    {
      "process": "Data ingested from ORNL DAAC",
      "timestamp": "2024-06-01T12:00:00+00:00",
      "workflow": "pine_ridge_analysis.ipynb",
      "inputs": ["ORNL DAAC API"],
      "outputs": ["pine_ridge_ndvi_raw.csv"]
    },
    {
      "process": "Resample: 16-day to monthly mean",
      "timestamp": "2024-06-01T12:01:00+00:00",
      "workflow": "pine_ridge_analysis.ipynb",
      "inputs": ["pine_ridge_ndvi_raw.csv"],
      "outputs": ["pine_ridge_ndvi_monthly.csv"]
    }
  ]
}
```

## How TK Labels and IEEE 2890 Work Together
IEEE 2890-2025 establishes the provenance chain which provides documentation
of where data came from and what transformations happened to it. Local Contexts TK/BC
labels establish the governance layer and what can be done with it.

These are complementary:

```
IEEE 2890-2025:                   Local Contexts TK Labels:
"This data came from X,           "This data may only be used for Y,
 was transformed via A, B, C,      by permission of community Z,
 and describes territory T."       contact W for authorization."
```

Together they provide:
- **Origin** (IEEE 2890) and **Authority** (TK label)
- **History** (chain steps) and **Restrictions** (label type)
- **Machine-readable lineage** (JSON sidecar) and **Governance enforcement** (validate_usage())

The `prov:ieee_2890` field in every metadata dict written by this toolkit
points to the standard, affirming alignment:

```python
dataset_meta["prov:ieee_2890"]  # "https://standards.ieee.org/ieee/2890/10318/"
```

## Alignment with Other Standards
IEEE 2890-2025 is designed to align with:
| Framework | Role | Relationship to IEEE 2890 |
|---|---|---|
| **CARE Principles** | Ethical obligations | IEEE 2890 implements CARE's technical provenance requirements |
| **FAIR Principles** | Technical data management | IEEE 2890 extends FAIR to include Indigenous-specific provenance |
| **Local Contexts** | Label vocabulary | IEEE 2890 uses Local Contexts labels as the governance layer |
| **Dublin Core** | Metadata vocabulary | IEEE 2890 extends DC with Indigenous-specific fields |
| **PROV-O** | Provenance ontology | IEEE 2890's chain structure is compatible with W3C PROV |
| **STAC** | Geospatial metadata | `tk:` and `prov:` fields map to STAC item properties |

## Citation
When using this toolkit in published work, cite both the standard and
the Local Contexts initiative:

**IEEE 2890-2025:**
> IEEE. (2025). *IEEE 2890-2025: Recommended Practice for Provenance
> of Indigenous Peoples' Data.* IEEE Standards Association.
> https://standards.ieee.org/ieee/2890/10318/

**Local Contexts:**
> Anderson, J. and Christen, K. (2019). 'Decolonizing' Attribution:
> Traditions of Exclusion. *Journal of Radical Librarianship*, 5.
> https://localcontexts.org/

**CARE Principles:**
> Carroll, S.R. et al. (2020). The CARE Principles for Indigenous
> Data Governance. *Data Science Journal*, 19(1).
> https://doi.org/10.5334/dsj-2020-043
