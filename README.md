# Local Contexts Labels in Geospatial Workflows
**Author:** Lilly Jones, PhD, Daear Consulting, LLC  
**Status:** Active development  
**License:**  AGPL-3.0 license

[![DOI](https://zenodo.org/badge/1211814979.svg)](https://doi.org/10.5281/zenodo.19892978)

## Overview
[Local Contexts](https://localcontexts.org/) provides Traditional Knowledge (TK)
and Biocultural (BC) labels that allow Indigenous communities to express how their
cultural heritage materials and data should be accessed, used, and shared. These
labels are designed to travel with data, signaling cultural authority,
appropriate use, and community expectations across the full data lifecycle.

This repository demonstrates how to embed Local Contexts labels in geospatial
workflows so they persist through transformations, survive exports, and are
checked before data is shared or used in downstream analysis.

The primary shift this toolkit enables:
> From: metadata as description  
> To: metadata as governance logic embedded in computation

## Frameworks
This toolkit is aligned with four complementary frameworks:
| Framework | What it governs |
|---|---|
| **Local Contexts TK/BC Labels** | Cultural authority, appropriate use, community expectations |
| **OCAP®** | Tribal Nations own, control, access, and possess their data |
| **CARE Principles** | Collective Benefit, Authority to Control, Responsibility, Ethics |
| **IEEE 2890-2025** | Provenance of Indigenous Peoples' data (machine-readable ethical lineage) |

## Repository Structure
```
local_contexts_geospatial/
├── localcontexts/              # Reusable Python toolkit (pip-installable)
│   ├── labels.py               # TKMetadata, BCMetadata, label registry
│   ├── propagation.py          # Label propagation utilities and decorators
│   ├── validation.py           # CARE-aware validation checks
│   ├── spatial.py              # Geometry-scoped label assignment
│   └── provenance.py           # IEEE 2890-aligned provenance chain
├── notebooks/
│   ├── 01_labels_and_schema.ipynb        # TK/BC label concepts and TKMetadata object
│   ├── 02_vector_workflows.ipynb         # Labels in GeoJSON and GeoPackage
│   ├── 03_raster_workflows.ipynb         # Labels in GeoTIFF via rasterio tags
│   ├── 04_propagation_and_lineage.ipynb  # Labels surviving transformations
│   ├── 05_spatial_authority.ipynb        # Geometry-scoped label assignment
│   ├── 06_care_validation.ipynb          # Runtime checks before export/share
│   └── 07_ieee2890_provenance.ipynb      # Full lifecycle: ingest→process→export
├── data/
│   ├── real/                   # Public data downloaded at runtime (Census TIGER)
│   └── synthetic/              # Clearly labeled synthetic data for demonstrations
├── examples/
│   └── pine_ridge_workflow.py  # End-to-end script showing the full pattern
├── docs/
│   ├── label_reference.md      # TK and BC label descriptions and use cases
│   ├── care_alignment.md       # How the toolkit implements each CARE principle
│   └── ieee2890_alignment.md   # How provenance chain maps to IEEE 2890-2025
├── environment.yml
├── pyproject.toml
└── README.md
```

## Installation
```bash
# Clone the repository
git clone https://github.com/daearconsulting/local_contexts_geospatial
cd local_contexts_geospatial

# Create and activate the conda environment
conda env create -f environment.yml
conda activate local-contexts-geo

# The localcontexts package is installed in editable mode via environment.yml
# To install manually with optional dependencies:
pip install -e ".[all]"
```

## Quick Start
```python
from localcontexts.labels import TKMetadata, TKLabel
from localcontexts.propagation import propagate_labels
from localcontexts.validation import validate_usage

# Define a TK label for a dataset
tk = TKMetadata(
    label=TKLabel.NON_COMMERCIAL,
    community="Oglala Lakota Nation",
    authority="Tribal Data Governance Office",
    usage="Non-commercial environmental research only",
    contact="data@oglalalakota.org",
)

# Attach to a dataset's metadata dict
dataset_meta = {"source": "NDVI satellite composite"}
dataset_meta = tk.attach(dataset_meta)

# Validate before use
validate_usage(dataset_meta, intended_use="research")   # passes
validate_usage(dataset_meta, intended_use="commercial") # raises TKViolationError

# Propagate to derived datasets
derived_meta = {"process": "NDVI inversion for water stress"}
derived_meta = propagate_labels(dataset_meta, derived_meta)
# derived_meta now carries the TK label
```
## Notebooks
| Notebook | Focus | Data |
|---|---|---|
| 01 | TK/BC label concepts, `TKMetadata` object, label vocabulary | None required |
| 02 | Attaching labels to GeoJSON fields and GeoPackage attributes | Census TIGER (downloaded) |
| 03 | Embedding labels in GeoTIFF metadata via `rasterio` tags | Synthetic raster |
| 04 | Label propagation through transformations; the "drop vs. keep" contrast | Synthetic |
| 05 | Geometry-scoped authority: labels assigned by spatial overlap | Census TIGER + synthetic zones |
| 06 | CARE-aware validation checks before export and sharing | Synthetic |
| 07 | Full IEEE 2890-aligned provenance chain from ingest to export | Mixed |

## About Local Contexts Labels
Local Contexts TK and BC labels are developed by the
[Local Contexts](https://localcontexts.org/) initiative in partnership with
Indigenous communities globally.

**Traditional Knowledge (TK) Labels** address cultural heritage materials, including
recordings, images, documents, and data, and allow Indigenous communities to
express appropriate use conditions.

**Biocultural (BC) Labels** address biological diversity and genetic resources
and the cultural relationships Indigenous communities have with them.

Labels are not restrictions imposed from outside: they are expressions of
community authority over community knowledge. Embedding them in geospatial
workflows is a technical implementation of that authority.

For full label descriptions and to apply for labels for your project, visit:
https://localcontexts.org/labels/traditional-knowledge-labels/

## Data Notice
```
data/synthetic/ contains data created solely for demonstration purposes.
It does not represent any real Tribal Nation's data, conditions, or knowledge.

data/real/ contains public federal data downloaded at runtime.
It carries the governance notes described in each notebook.
```

## Acknowledgments
This toolkit is developed in the spirit of the frameworks below. Citation of
these frameworks is appropriate when using or extending this toolkit:

- Local Contexts: https://localcontexts.org/
- OCAP®: First Nations Information Governance Centre: https://fnigc.ca/ocap-training/
- CARE Principles: GIDA: https://www.gida-global.org/care
- FAIR Principles: https://www.go-fair.org/fair-principles/
- IEEE 2890-2025: https://standards.ieee.org/ieee/2890/10318/

## Citation
Jones, L. and Sanovia, J. (2026). Local Contexts Labels in Geospatial Workflows.
Daear Consulting, LLC. https://github.com/daearconsulting/local_contexts_geospatial
