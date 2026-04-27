# Local Contexts Label Reference
This document describes the TK (Traditional Knowledge) and BC (Biocultural)
labels provided by Local Contexts, their intended use cases, and guidance
for selecting the appropriate label for a dataset.

For official label descriptions, images, and the process for obtaining labels
for your project, visit: https://localcontexts.org/labels/

## Traditional Knowledge (TK) Labels
TK labels address cultural heritage materials such as recordings, images, documents,
and data about or derived from Indigenous knowledge and practices. They are
designed to signal cultural authority and appropriate use conditions.

### When to Use TK Labels
Use TK labels when data involves:
- Traditional land use and management knowledge
- Cultural sites and landscapes
- Environmental observations that carry cultural significance
- Data collected by or in partnership with a Tribal Nation
- Satellite or remotely sensed data covering Indigenous territories where
  Traditional Knowledge informed site selection or interpretation
- Any dataset where Indigenous governance applies

### TK Non-Commercial
**Label value:** `TK Non-Commercial`  
**`TKLabel` enum:** `TKLabel.NON_COMMERCIAL`

**What it means:**  
This label indicates that commercial use is not appropriate without explicit
consent from the relevant Indigenous community. The data may be used for
non-commercial research, education, and environmental monitoring.

**Typical use cases:**
- NDVI and vegetation condition datasets covering reservation lands
- Groundwater monitoring data on Tribal lands
- Pasture condition scores collected by Tribal range riders
- Environmental baseline datasets supporting land management planning

**What researchers must do:**
- Confirm intended use is non-commercial before analysis
- Contact the authority listed in the label before publication
- Share results with the originating community
- Ensure derived datasets carry the same label

**Implementation:**
```python
tk = TKMetadata(
    label     = TKLabel.NON_COMMERCIAL,
    community = "Oglala Lakota Nation",
    authority = "Tribal Data Governance Office",
    usage     = "Non-commercial environmental research only",
)
```

### TK Community Use Only
**Label value:** `TK Community Use Only`  
**`TKLabel` enum:** `TKLabel.COMMUNITY_USE_ONLY`

**What it means:**  
This label restricts use to members and staff of the originating community.
It is not for public or external use without explicit permission.

**Typical use cases:**
- Detailed pasture condition monitoring data
- Community-internal land health assessments
- Culturally sensitive environmental observation records
- Data collected under a Tribal research agreement

**What researchers must do:**
- Do not use this data for external research without explicit written consent
- Do not share, publish, or transmit this data outside the community
- Contact the authority listed before any use

### TK Culturally Sensitive
**Label value:** `TK Culturally Sensitive`  
**`TKLabel` enum:** `TKLabel.CULTURALLY_SENSITIVE`

**What it means:**  
This label indicates that data has specific cultural protocols associated with
it. Access is restricted and the data should not be publicly shared or
published without community review.

**Typical use cases:**
- Locations of culturally significant sites
- Species observation data tied to ceremonial practices
- Oral history recordings with ecological content
- Geospatial data that could reveal sensitive cultural information

**What researchers must do:**
- Do not publish locations or describe contents without community consent
- Treat all access as provisional until explicit consent is obtained
- Remove from any public-facing datasets or publications

### TK Notice
**Label value:** `TK Notice`  
**`TKLabel` enum:** `TKLabel.NOTICE`

**What it means:**  
This label signals that Indigenous interests exist in this material and that
there may be cultural protocols associated with it, even if a specific
label has not yet been assigned by the community.

**Typical use cases:**
- Datasets covering Tribal lands where community consultation is pending
- Public federal data (MODIS, gridMET, Census) used in analysis of Tribal lands
- Interim labeling while waiting for a community to assign a specific label
- Mixed datasets where some portions are clearly labeled and others are not

**What researchers must do:**
- Acknowledge that Indigenous interests exist
- Seek community guidance before publication
- Treat as TK Non-Commercial until a more specific label is assigned

### TK Attribution Incomplete
**Label value:** `TK Attribution Incomplete`  
**`TKLabel` enum:** `TKLabel.ATTRIBUTION_INCOMPLETE`

**What it means:**  
The current attribution of this material is incomplete. The community is in
the process of researching and reclaiming their heritage.

**Typical use cases:**
- Historical datasets where the originating community's role was not
  documented at collection time
- Archival materials being repatriated or re-attributed

### TK Verified
**Label value:** `TK Verified`  
**`TKLabel` enum:** `TKLabel.VERIFIED`

**What it means:**  
The community has verified the cultural authority of this material and
confirmed that it has been appropriately attributed.

**Typical use cases:**
- Datasets that have been reviewed and approved by the relevant community
- Environmental monitoring products developed in formal partnership

### TK Open to Collaboration
**Label value:** `TK Open to Collaboration`  
**`TKLabel` enum:** `TKLabel.OPEN_TO_COLLABORATION`

**What it means:**  
The community is interested in engaging with researchers and institutions
who work with this material.

**Typical use cases:**
- Datasets where the community actively wants research partnerships
- Monitoring programs seeking external technical support

## Biocultural (BC) Labels
BC labels address biological diversity and genetic resource data and the
cultural relationships Indigenous communities have with plants, animals,
and ecosystems in their territories.

### When to Use BC Labels
Use BC labels when data involves:
- Species occurrence records in Indigenous territories
- Plant and animal knowledge tied to specific communities
- Genetic resource data from Indigenous lands
- Biodiversity monitoring where community stewardship is central
- Ecosystem services data with cultural context

### BC Label Types
**BC Provenance** (`BCLabel.PROVENANCE`)  
Asserts community provenance over biological materials and associated
knowledge. Use when the community's relationship to the biological resource
is central to the dataset.

**BC Non-Commercial** (`BCLabel.NON_COMMERCIAL`)  
Restricts commercial use of biological/cultural resource data. Critical
for preventing commercial bioprospecting without community consent.

**BC Community Use Only** (`BCLabel.COMMUNITY_USE_ONLY`)  
Restricts use to the originating community. Use for sensitive species
location data or traditional ecological knowledge about biological resources.

**BC Research Use** (`BCLabel.RESEARCH_USE`)  
Signals that the community has approved research use of this biological
data under specified conditions.

## Combining TK and BC Labels
Some datasets warrant both a TK and a BC label. A traditional medicinal
plant dataset, for example, carries:
- **TK label** : because it encodes traditional knowledge about plant use
- **BC label** : because it records biological resource locations

```python
meta = tk.attach({"name": "traditional_plants"})
meta = bc.attach(meta)
# meta now carries both tk: and bc: prefixed fields
```

## Label Selection Decision Tree
```
Does this data involve Indigenous Peoples' knowledge, practices,
or observations?
  └─ YES Does it involve biological resources specifically
           (species, plants, animals, genetics)?
               ├─ YES Use BC label (and TK label if cultural
               │         knowledge is also involved)
               └─ NO  Use TK label
  └─ NO  Consider TK Notice if data covers Tribal lands

Is the appropriate label already determined by the community?
  ├─ YES Use the specified label
  └─ NO  Use TK Notice while consultation is pending

Is the data for community-internal use only?
  ├─ YES TK Community Use Only
  └─ NO  Consider TK Non-Commercial, TK Verified, or TK Notice
           depending on the level of community review
```

## Obtaining Labels for Your Project
Labels are assigned by Indigenous communities, not by researchers.
To obtain a label:
1. Visit https://localcontexts.org/
2. Review the label types and their meanings
3. Contact the relevant Indigenous community's data governance office
4. Work with the community to identify the appropriate label
5. Receive the label through the Local Contexts Hub

The labels in this toolkit use the label vocabulary from Local Contexts.
The `TKMetadata` and `BCMetadata` objects are containers for expressing
a label that a community has assigned, not a mechanism for self-assigning
labels to someone else's data.

## References
- Local Contexts: https://localcontexts.org/
- TK Label descriptions: https://localcontexts.org/labels/traditional-knowledge-labels/
- BC Label descriptions: https://localcontexts.org/labels/biocultural-labels/
- OCAP® Principles: https://fnigc.ca/ocap-training/
- CARE Principles: https://www.gida-global.org/care
