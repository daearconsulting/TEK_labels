# CARE Principles Alignment
This document describes how the `localcontexts-geo` toolkit implements
each of the four CARE Principles for Indigenous Data Governance.

**CARE Principles reference:** https://www.gida-global.org/care

## What Are the CARE Principles?

The CARE Principles were developed by the Global Indigenous Data Alliance
to complement FAIR data principles with the ethical obligations that
FAIR alone does not address. FAIR governs technical data management
(findability, accessibility, interoperability, reusability). CARE governs
the rights and responsibilities that apply to Indigenous Peoples' data.

A dataset can be fully FAIR and still violate Indigenous data sovereignty.
CARE establishes what FAIR cannot:

| Principle | Core idea |
|---|---|
| **C** : Collective Benefit | Data ecosystems must enable Indigenous Peoples to benefit from the data |
| **A** : Authority to Control | Indigenous Peoples' rights and interests in data must be recognized |
| **R** : Responsibility | Those working with Indigenous data have a responsibility to the community |
| **E** : Ethics | Indigenous Peoples' rights and wellbeing should be at the center |

## C: Collective Benefit
**The principle:** Data ecosystems shall be designed and function in ways
that enable Indigenous Peoples to derive benefit from the data.

### What this requires in practice
Data collected about or from Indigenous communities should produce
outcomes that serve those communities, not just the researcher's
institution, funder, or publication record.

### How this toolkit implements CARE-C
**`check_collective_benefit()`** records how an analysis benefits the
originating community before output is written:

```python
from localcontexts.validation import check_collective_benefit

check_collective_benefit(
    meta,
    benefit_description=(
        "Drought trend analysis will be shared with the Oglala Lakota Nation "
        "Natural Resources Department in plain-language format to support "
        "land management planning."
    )
)
# Writes care:collective_benefit to meta and creates a documented record
```

**What "benefit" means:**
- Analysis results shared with the community in accessible format
- Research outputs that directly support Tribal programs
- Capacity building: Tribal staff learn from the methodology
- Publications where the community is credited as knowledge holder

**What "benefit" does NOT mean:**
- The researcher publishes a paper that mentions the community
- A dataset is made public that the community cannot access
- Results are shared with funders without sharing with the community

## A: Authority to Control
**The principle:** Indigenous Peoples' rights and interests in Indigenous
data must be recognized and their authority to control such data be
empowered.

### What this requires in practice
Tribal Nations have the right to determine how data about their lands,
people, and knowledge is collected, used, and shared. Researchers and
institutions do not have authority to override this, even for data that
is publicly accessible.

### How this toolkit implements CARE-A
**`TKMetadata` and `BCMetadata`** are the mechanism for expressing
a community's authority over their data:

```python
tk = TKMetadata(
    label     = TKLabel.NON_COMMERCIAL,
    community = "Oglala Lakota Nation",
    # Who holds the authority?
    authority = "Tribal Data Governance Office",  
    usage     = "Non-commercial research only",
    # How to reach the data authority
    contact   = "data@oglalalakota.org",          
)
```

**`validate_usage()`** enforces the community's authority at runtime:

```python
from localcontexts.validation import validate_usage, TKViolationError

try:
    validate_usage(meta, intended_use="commercial")
except TKViolationError:
    # The community's authority is enforced: this use is blocked
    pass
```

**`check_authority_to_control()`** documents the consent process:

```python
from localcontexts.validation import check_authority_to_control

check_authority_to_control(
    meta,
    consent_obtained    = True,
    consent_description = "MOU signed with OST NRD, 2024-03-15",
)
```

**Distinctions:** The toolkit enforces the label that a community
has assigned. It does not self-assign labels on communities' behalf.
Only the community or their authorized governance body assigns the label.

## R: Responsibility

**The principle:** Those working with Indigenous data have a responsibility
to share how those data are used and to support the capacity of Indigenous
Peoples to govern their own data.

### What this requires in practice
Researchers working with Indigenous data are accountable to the community,
not just to their institution or journal. This means:
- Sharing how data was used (transparency)
- Reporting results back to the community
- Supporting the community's own data governance capacity
- Not treating data access as a right without corresponding obligation

### How this toolkit implements CARE-R
**`ProvenanceRecord`** creates a machine-readable accountability trail:

```python
from localcontexts.provenance import ProvenanceRecord, ProvenanceOrigin

record = ProvenanceRecord(
    dataset_name = "pine_ridge_ndvi_analysis",
    origin       = ProvenanceOrigin(
        subject   = "NDVI time series — Pine Ridge",
        community = "Oglala Lakota Nation",
        ...
    )
)

# Every transformation is documented
record.add_step(
    process  = "Annual growing season mean",
    inputs   = ["raw_ndvi.csv"],
    outputs  = ["annual_gs_ndvi.csv"],
)
```

**`build_sidecar_path()` and `record.save()`** ensure the provenance
travels with the output:

```python
from localcontexts.provenance import build_sidecar_path

sidecar = build_sidecar_path(output_path)
record.save(sidecar)
# Anyone receiving the output can read the full provenance chain
```

**`propagate_labels()`** ensures the community's label travels with
derived products, making label inheritance automatic rather than
dependent on individual researchers remembering:

```python
from localcontexts.propagation import propagate_labels

output_meta = propagate_labels(source_meta, {"process": "clip to boundary"})
# tk: and bc: fields automatically copied to output_meta
```

## E: Ethics

**The principle:** Indigenous Peoples' rights and wellbeing should be
the primary concern at all stages of the data life cycle and across the
data ecosystem.

### What this requires in practice
Ethics here is not just about avoiding harm, it is about actively
centering Indigenous rights and wellbeing in every decision:
- In what data is collected (and what is not)
- In how data is stored and who can access it
- In how results are interpreted and communicated
- In whose voice is centered when results are shared

### How this toolkit implements CARE-E
**`TKLabel.CULTURALLY_SENSITIVE` and `TKLabel.COMMUNITY_USE_ONLY`**
provide technical enforcement for the most sensitive governance cases:

```python
# This label blocks all external use and warns on sensitive operations
tk = TKMetadata(
    label = TKLabel.CULTURALLY_SENSITIVE,
    ...
)
validate_usage(meta, intended_use="publication")
# Raises TKViolationError: publication without review is blocked
```

**`strip_labels()`** always emits a warning, making label removal
visible and requiring justification:

```python
from localcontexts.propagation import strip_labels

# This will always warn, making label removal a documented, visible action
stripped = strip_labels(meta)
# UserWarning: strip_labels() called: removing TK/BC label fields...
```

**`validate_export_ready()`** runs all ethical checks as a gate
before any output leaves the workflow:

```python
from localcontexts.validation import validate_export_ready

report = validate_export_ready(
    meta,
    intended_use = "research",
    destination  = "GitHub public repository",
)
# All CARE checks run before export is permitted
```

## CARE vs. FAIR: What Each Framework Covers
| Concern | FAIR | CARE |
|---|---|---|
| Data is findable | X | - |
| Data is accessible | X | - |
| Data uses standard formats | X | - |
| Data has a license | X | - |
| Community benefits from data | - | X |
| Community controls use | - | X |
| Researcher is accountable | - | X |
| Indigenous rights are centered | - | X |

A dataset can be fully FAIR with persistent identifiers, open format,
machine-readable license, and documented schema and still violate
every CARE principle. This toolkit implements the CARE layer on top of
the technical practices that FAIR addresses.

## Implementing CARE in Your Workflow
Minimum CARE implementation for any workflow involving Indigenous data:

```python
# At ingest
validate_label_present(meta, context="my dataset")
validate_usage(meta, intended_use="research")

# At each transformation
output_meta = propagate_labels(source_meta, output_meta)
validate_provenance_intact(output_meta)

# Before export
check_collective_benefit(meta, benefit_description="...")
check_authority_to_control(meta, consent_obtained=True, ...)
report = validate_export_ready(meta, intended_use="research", destination="...")

# With output
record.save(build_sidecar_path(output_path))
```
## References
- CARE Principles for Indigenous Data Governance: https://www.gida-global.org/care
- Carroll et al. (2020). The CARE Principles for Indigenous Data Governance.
  *Data Science Journal*, 19(1). https://doi.org/10.5334/dsj-2020-043
- FAIR Principles: https://www.go-fair.org/fair-principles/
- OCAP®: https://fnigc.ca/ocap-training/
- Local Contexts: https://localcontexts.org/
- IEEE 2890-2025: https://standards.ieee.org/ieee/2890/10318/
