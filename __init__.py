"""
localcontexts-geo — Local Contexts TK/BC labels in geospatial workflows.

A toolkit for embedding Traditional Knowledge (TK) and Biocultural (BC)
labels in geospatial data pipelines so they persist through transformations,
survive exports, and are checked before data is shared or used downstream.

Quick start
-----------
>>> from localcontexts.labels import TKMetadata, TKLabel
>>> from localcontexts.propagation import propagate_labels
>>> from localcontexts.validation import validate_usage
>>> from localcontexts.provenance import ProvenanceRecord, ProvenanceOrigin

>>> tk = TKMetadata(
...     label=TKLabel.NON_COMMERCIAL,
...     community="Oglala Lakota Nation",
...     authority="Tribal Data Governance Office",
...     usage="Non-commercial environmental research only",
... )
>>> meta = tk.attach({"source": "NDVI satellite composite"})
>>> validate_usage(meta, intended_use="research")  # passes
True

Modules
-------
labels      — TKMetadata, BCMetadata, TKLabel, BCLabel (no geo dependencies)
propagation — propagate_labels(), enforce_label_propagation decorator
validation  — validate_usage(), validate_export_ready(), CARE checks
spatial     — geometry-scoped assignment (requires geopandas)
provenance  — IEEE 2890-2025 aligned provenance chain

Frameworks
----------
Local Contexts : https://localcontexts.org/
OCAP®          : https://fnigc.ca/ocap-training/
CARE           : https://www.gida-global.org/care
FAIR           : https://www.go-fair.org/fair-principles/
IEEE 2890-2025 : https://standards.ieee.org/ieee/2890/10318/
"""

__version__ = "0.1.0"
__author__  = "Lilly Jones, PhD — Daear Consulting, LLC"

from .labels import (
    TKLabel,
    BCLabel,
    TKMetadata,
    BCMetadata,
    extract_tk_fields,
    extract_bc_fields,
    has_tk_label,
    has_bc_label,
    has_any_label,
)

from .local_contexts_geospatial.propagation import (
    propagate_labels,
    propagate_labels_strict,
    merge_labels,
    strip_labels,
    enforce_label_propagation,
    add_provenance_step,
)

from .validation import (
    TKViolationError,
    BCViolationError,
    ProvenanceError,
    MissingLabelWarning,
    validate_usage,
    validate_label_present,
    validate_provenance_intact,
    validate_export_ready,
    check_collective_benefit,
    check_authority_to_control,
)

from .provenance import (
    ProvenanceOrigin,
    ProvenanceStep,
    ProvenanceRecord,
    build_sidecar_path,
    attach_provenance_to_meta,
    extract_provenance_from_meta,
)

__all__ = [
    # labels
    "TKLabel", "BCLabel", "TKMetadata", "BCMetadata",
    "extract_tk_fields", "extract_bc_fields",
    "has_tk_label", "has_bc_label", "has_any_label",
    # propagation
    "propagate_labels", "propagate_labels_strict", "merge_labels",
    "strip_labels", "enforce_label_propagation", "add_provenance_step",
    # validation
    "TKViolationError", "BCViolationError", "ProvenanceError",
    "MissingLabelWarning", "validate_usage", "validate_label_present",
    "validate_provenance_intact", "validate_export_ready",
    "check_collective_benefit", "check_authority_to_control",
    # provenance
    "ProvenanceOrigin", "ProvenanceStep", "ProvenanceRecord",
    "build_sidecar_path", "attach_provenance_to_meta",
    "extract_provenance_from_meta",
]
