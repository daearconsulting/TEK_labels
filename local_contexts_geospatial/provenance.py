"""
provenance.py IEEE 2890-2025 aligned provenance chain for labeled datasets.

IEEE 2890-2025 establishes common parameters for the provenance of Indigenous
Peoples' data describing and recording how data should be disclosed, connected
to people and place, and governed across its lifecycle.

This module implements a machine-readable provenance chain that:
  - Records the origin of a dataset and its TK/BC label authority
  - Tracks each transformation applied to the data
  - Preserves label lineage through derived datasets
  - Produces sidecar JSON files that travel with the data

No geospatial dependencies, works with any metadata dict.

Reference: https://standards.ieee.org/ieee/2890/10318/
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Provenance record objects

@dataclass
class ProvenanceOrigin:
    """
    Records the origin of a dataset: where it came from, who it is about,
    and what cultural authority it carries.

    Aligned with IEEE 2890-2025 core provenance parameters.
    """
    # What the data is about
    subject:           str           # ex. "NDVI satellite imagery Pine Ridge"
    # Who the data is about or from
    community:         str           # ex. "Oglala Lakota Nation"
    territory:         Optional[str] = None   # Geographic territory description
    # Where the data came from
    source_name:       str = ""      # ex. "MODIS MOD13Q1 via ORNL DAAC"
    source_url:        str = ""
    source_steward:    str = ""      # ex. "NASA LP DAAC"
    # When it was obtained
    obtained_date:     str = field(
        default_factory=lambda: datetime.now(timezone.utc).date().isoformat()
    )
    # Cultural authority
    tk_label:          Optional[str] = None
    bc_label:          Optional[str] = None
    label_authority:   Optional[str] = None   # Who assigned the label
    # License and access
    license:           str = ""
    access_conditions: str = ""

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ProvenanceStep:
    """
    Records a single transformation step in the provenance chain.
    Each step preserves the label lineage and transformation history.
    """
    process:     str                  # Description of the transformation
    timestamp:   str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    workflow:    Optional[str] = None  # Notebook or script name
    operator:    Optional[str] = None  # Person or system performing the step
    inputs:      list[str] = field(default_factory=list)   # Input dataset names
    outputs:     list[str] = field(default_factory=list)   # Output dataset names
    notes:       Optional[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ProvenanceRecord:
    """
    Complete provenance record for a dataset, including origin, chain of transformations,
    and label lineage. Designed to travel with the data as a sidecar file.

    Aligned with IEEE 2890-2025 provenance parameters:
    - Connects data to people and place
    - Facilitates governance and decision-making
    - Supports future benefit-sharing identification
    - Enables interoperability across platforms and databases
    """
    dataset_name:  str
    origin:        ProvenanceOrigin
    chain:         list[ProvenanceStep] = field(default_factory=list)
    created_at:    str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at:    str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    ieee_2890:     str = "https://standards.ieee.org/ieee/2890/10318/"
    care_aligned:  bool = True

    # Chain management

    def add_step(
        self,
        process: str,
        workflow: str | None = None,
        operator: str | None = None,
        inputs: list[str] | None = None,
        outputs: list[str] | None = None,
        notes: str | None = None,
    ) -> "ProvenanceRecord":
        """
        Add a transformation step to the provenance chain.
        Returns self to allow chaining.

        Examples
        >>> record.add_step(
        ...     process="Clipped to Tribal boundary",
        ...     workflow="notebook_02_vector_workflows.ipynb",
        ... ).add_step(
        ...     process="Computed NDVI anomaly",
        ...     workflow="notebook_03_raster_workflows.ipynb",
        ... )
        """
        step = ProvenanceStep(
            process=process,
            workflow=workflow,
            operator=operator,
            inputs=inputs or [],
            outputs=outputs or [],
            notes=notes,
        )
        self.chain.append(step)
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return self

    # Serialization

    def to_dict(self) -> dict:
        return {
            "dataset_name":  self.dataset_name,
            "ieee_2890":     self.ieee_2890,
            "care_aligned":  self.care_aligned,
            "created_at":    self.created_at,
            "updated_at":    self.updated_at,
            "origin":        self.origin.to_dict(),
            "chain":         [s.to_dict() for s in self.chain],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, d: dict) -> "ProvenanceRecord":
        origin = ProvenanceOrigin(**d["origin"])
        chain  = [ProvenanceStep(**s) for s in d.get("chain", [])]
        return cls(
            dataset_name = d["dataset_name"],
            origin       = origin,
            chain        = chain,
            created_at   = d.get("created_at", ""),
            updated_at   = d.get("updated_at", ""),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ProvenanceRecord":
        return cls.from_dict(json.loads(json_str))

    # File I/O

    def save(self, path: str | Path) -> Path:
        """
        Save provenance record as a JSON sidecar file.

        Convention: sidecar lives alongside the data file with the same
        stem and a .provenance.json extension.
        ex., water_stress.tif to water_stress.provenance.json

        Parameters
        path : Path to save the sidecar JSON

        Returns
        Path where the file was saved
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())
        return path

    @classmethod
    def load(cls, path: str | Path) -> "ProvenanceRecord":
        """Load a provenance record from a JSON sidecar file."""
        return cls.from_json(Path(path).read_text())

    # Display

    def summary(self) -> str:
        lines = [
            f"Provenance Record: {self.dataset_name}",
            f"  IEEE 2890-2025 aligned: {self.ieee_2890}",
            f"  Created : {self.created_at}",
            f"  Updated : {self.updated_at}",
            f"\nOrigin:",
            f"  Subject   : {self.origin.subject}",
            f"  Community : {self.origin.community}",
            f"  Source    : {self.origin.source_name}",
            f"  TK Label  : {self.origin.tk_label or 'None'}",
            f"  BC Label  : {self.origin.bc_label or 'None'}",
            f"\nTransformation chain ({len(self.chain)} steps):",
        ]
        for i, step in enumerate(self.chain, 1):
            lines.append(f"  {i}. {step.process}")
            if step.workflow:
                lines.append(f"       Workflow : {step.workflow}")
            if step.notes:
                lines.append(f"       Notes    : {step.notes}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return self.summary()


# Helper functions

def build_sidecar_path(data_path: str | Path) -> Path:
    """
    Return the conventional sidecar path for a data file.
    ex., water_stress.tif to water_stress.provenance.json
    """
    p = Path(data_path)
    return p.parent / f"{p.stem}.provenance.json"


def attach_provenance_to_meta(
    meta: dict,
    record: ProvenanceRecord,
) -> dict:
    """
    Attach a serialized ProvenanceRecord to a metadata dict.

    Adds prov: prefixed fields including the full chain as a JSON string.

    Parameters
    meta   : Existing metadata dict
    record : ProvenanceRecord to attach

    Returns
    New metadata dict with prov: fields added
    """
    result = dict(meta)
    result["prov:record"]    = record.to_json()
    result["prov:dataset"]   = record.dataset_name
    result["prov:community"] = record.origin.community
    result["prov:ieee_2890"] = record.ieee_2890
    if record.origin.tk_label:
        result.setdefault("tk:label", record.origin.tk_label)
    if record.origin.bc_label:
        result.setdefault("bc:label", record.origin.bc_label)
    return result


def extract_provenance_from_meta(meta: dict) -> ProvenanceRecord | None:
    """
    Reconstruct a ProvenanceRecord from a metadata dict that was
    created with attach_provenance_to_meta().

    Returns None if no provenance record is found.
    """
    prov_json = meta.get("prov:record")
    if not prov_json:
        return None
    return ProvenanceRecord.from_json(prov_json)
