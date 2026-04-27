"""
labels.py TK and BC label schema and metadata objects.

This module has zero geospatial dependencies. TKMetadata and BCMetadata
work with plain Python dicts and can be used in any data pipeline.

References
Local Contexts TK Labels : https://localcontexts.org/labels/traditional-knowledge-labels/
Local Contexts BC Labels : https://localcontexts.org/labels/biocultural-labels/
IEEE 2890-2025           : https://standards.ieee.org/ieee/2890/10318/
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


# TK Label vocabulary

class TKLabel(str, Enum):
    """
    Traditional Knowledge label types from Local Contexts.
    Values match the Local Contexts label slugs for interoperability.
    """
    # Use conditions
    ATTRIBUTION_INCOMPLETE = "TK Attribution Incomplete"
    COMMERCIAL             = "TK Commercial"
    NON_COMMERCIAL         = "TK Non-Commercial"
    COMMUNITY_USE_ONLY     = "TK Community Use Only"
    SEASONAL               = "TK Seasonal"
    WOMEN_GENERAL          = "TK Women General"
    MEN_GENERAL            = "TK Men General"
    # Access conditions
    SECRET_SACRED          = "TK Secret/Sacred"
    CULTURALLY_SENSITIVE   = "TK Culturally Sensitive"
    VERIFIED               = "TK Verified"
    NON_VERIFIED           = "TK Non-Verified"
    MULTIPLE_COMMUNITY     = "TK Multiple Community"
    OPEN_TO_COLLABORATION  = "TK Open to Collaboration"
    CREATIVE_COMMONS       = "TK Creative Commons"
    # Notice labels
    NOTICE                 = "TK Notice"
    CLAN                   = "TK Clan"
    FAMILY                 = "TK Family"


class BCLabel(str, Enum):
    """
    Biocultural label types from Local Contexts.
    BC labels address biological diversity and genetic resources.
    """
    PROVENANCE             = "BC Provenance"
    MULTIPLE_COMMUNITY     = "BC Multiple Community"
    CLAN                   = "BC Clan"
    FAMILY                 = "BC Family"
    SEASONAL               = "BC Seasonal"
    VERIFIED               = "BC Verified"
    NON_VERIFIED           = "BC Non-Verified"
    COMMUNITY_VOICE        = "BC Community Voice"
    RESEARCH_USE           = "BC Research Use"
    COMMERCIAL              = "BC Commercial"
    NON_COMMERCIAL         = "BC Non-Commercial"
    COMMUNITY_USE_ONLY     = "BC Community Use Only"
    NOTICE                 = "BC Notice"
    OPEN_TO_COLLABORATION  = "BC Open to Collaboration"
    CREATIVE_COMMONS       = "BC Creative Commons"


# Label description registry

TK_LABEL_DESCRIPTIONS: dict[TKLabel, str] = {
    TKLabel.NON_COMMERCIAL: (
        "This label is used to indicate that this material has conditions for use "
        "and that commercial use is not appropriate without explicit consent from "
        "the relevant Indigenous community."
    ),
    TKLabel.COMMERCIAL: (
        "This label is used when a community has decided that commercial use of "
        "certain materials is acceptable."
    ),
    TKLabel.COMMUNITY_USE_ONLY: (
        "This label indicates materials that should only be used within the "
        "originating community. They are not for public or outside use."
    ),
    TKLabel.SECRET_SACRED: (
        "This label is used for materials that have cultural protocols associated "
        "with them that require careful handling and should not be publicly shared."
    ),
    TKLabel.CULTURALLY_SENSITIVE: (
        "This label is used to indicate materials that have specific cultural "
        "sensitivities and that have protocols for restricted access."
    ),
    TKLabel.VERIFIED: (
        "This label is used by a community to verify the cultural authority of "
        "this material and to confirm that it has been appropriately attributed."
    ),
    TKLabel.ATTRIBUTION_INCOMPLETE: (
        "This label is used to indicate that the current attribution of this "
        "material is incomplete and that the community is in process of "
        "researching and reclaiming their heritage."
    ),
    TKLabel.NOTICE: (
        "This label is used to assert the existence of Indigenous interests in "
        "materials that may not yet have a specific TK Label assigned."
    ),
    TKLabel.OPEN_TO_COLLABORATION: (
        "This label signals that the community is interested in engaging with "
        "researchers and institutions who work with this material."
    ),
}


# Metadata objects

@dataclass
class TKMetadata:
    """
    Traditional Knowledge label metadata for a dataset or dataset component.

    This object is designed to be:
    - Attached to any data structure (dict, GeoDataFrame attribute, raster tag)
    - Propagated to derived datasets
    - Validated before use
    - Serialized to JSON for sidecar files or STAC extensions

    Parameters
    label       : TKLabel enum value
    community   : Name of the Indigenous community asserting cultural authority
    authority   : Governance body or individual with authority to assign the label
    usage       : Plain-language description of appropriate use conditions
    contact     : Contact information for data use inquiries
    notes       : Additional context or restrictions
    label_url   : URL to the Local Contexts label page (auto-populated if known)
    """
    label:      TKLabel
    community:  str
    authority:  str
    usage:      str
    contact:    Optional[str] = None
    notes:      Optional[str] = None
    label_url:  Optional[str] = field(default=None, init=False)

    def __post_init__(self):
        self.label_url = (
            "https://localcontexts.org/labels/traditional-knowledge-labels/"
        )

    # Serialization

    def to_dict(self) -> dict:
        """
        Serialize to a flat dict with tk: namespace prefix.
        Compatible with GeoJSON properties, rasterio tags, and STAC extensions.
        """
        return {
            "tk:label":      self.label.value,
            "tk:community":  self.community,
            "tk:authority":  self.authority,
            "tk:usage":      self.usage,
            "tk:contact":    self.contact,
            "tk:notes":      self.notes,
            "tk:label_url":  self.label_url,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, d: dict) -> "TKMetadata":
        """
        Reconstruct from a flat dict with tk: namespace prefix.
        Inverse of to_dict().
        """
        label_value = d.get("tk:label", "")
        try:
            label = TKLabel(label_value)
        except ValueError:
            raise ValueError(
                f"Unknown TK label value: {label_value!r}. "
                f"Valid values: {[l.value for l in TKLabel]}"
            )
        return cls(
            label=label,
            community=d.get("tk:community", ""),
            authority=d.get("tk:authority", ""),
            usage=d.get("tk:usage", ""),
            contact=d.get("tk:contact"),
            notes=d.get("tk:notes"),
        )

    # Attachment

    def attach(self, meta: dict) -> dict:
        """
        Attach TK label fields to an existing metadata dict.
        Returns a new dict, does not modify in place.

        Usage
        dataset_meta = tk.attach(dataset_meta)
        """
        return {**meta, **self.to_dict()}

    # Display

    def describe(self) -> str:
        """Return a human-readable description of this label."""
        desc = TK_LABEL_DESCRIPTIONS.get(self.label, "No description available.")
        return (
            f"TK Label: {self.label.value}\n"
            f"Community: {self.community}\n"
            f"Authority: {self.authority}\n"
            f"Usage: {self.usage}\n"
            f"\nLabel description:\n{desc}\n"
            f"\nMore information: {self.label_url}"
        )

    def __repr__(self) -> str:
        return self.to_json()


@dataclass
class BCMetadata:
    """
    Biocultural label metadata for biological diversity and genetic resource data.

    BC labels address the cultural relationships Indigenous communities have
    with biological resources such as plants, animals, and ecosystems.

    Parameters
    label       : BCLabel enum value
    community   : Name of the Indigenous community asserting authority
    authority   : Governance body or individual with authority to assign
    usage       : Plain-language description of appropriate use conditions
    species     : Species or biological resource this label applies to (optional)
    territory   : Geographic territory this label applies to (optional)
    contact     : Contact information for data use inquiries
    notes       : Additional context or restrictions
    """
    label:      BCLabel
    community:  str
    authority:  str
    usage:      str
    species:    Optional[str] = None
    territory:  Optional[str] = None
    contact:    Optional[str] = None
    notes:      Optional[str] = None
    label_url:  Optional[str] = field(default=None, init=False)

    def __post_init__(self):
        self.label_url = (
            "https://localcontexts.org/labels/biocultural-labels/"
        )

    def to_dict(self) -> dict:
        return {
            "bc:label":      self.label.value,
            "bc:community":  self.community,
            "bc:authority":  self.authority,
            "bc:usage":      self.usage,
            "bc:species":    self.species,
            "bc:territory":  self.territory,
            "bc:contact":    self.contact,
            "bc:notes":      self.notes,
            "bc:label_url":  self.label_url,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, d: dict) -> "BCMetadata":
        label_value = d.get("bc:label", "")
        try:
            label = BCLabel(label_value)
        except ValueError:
            raise ValueError(
                f"Unknown BC label value: {label_value!r}. "
                f"Valid values: {[l.value for l in BCLabel]}"
            )
        return cls(
            label=label,
            community=d.get("bc:community", ""),
            authority=d.get("bc:authority", ""),
            usage=d.get("bc:usage", ""),
            species=d.get("bc:species"),
            territory=d.get("bc:territory"),
            contact=d.get("bc:contact"),
            notes=d.get("bc:notes"),
        )

    def attach(self, meta: dict) -> dict:
        return {**meta, **self.to_dict()}

    def __repr__(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# Helper functions

def extract_tk_fields(meta: dict) -> dict:
    """Return only the tk: prefixed fields from a metadata dict."""
    return {k: v for k, v in meta.items() if k.startswith("tk:")}


def extract_bc_fields(meta: dict) -> dict:
    """Return only the bc: prefixed fields from a metadata dict."""
    return {k: v for k, v in meta.items() if k.startswith("bc:")}


def has_tk_label(meta: dict) -> bool:
    """Return True if metadata contains a TK label."""
    return "tk:label" in meta and meta["tk:label"] is not None


def has_bc_label(meta: dict) -> bool:
    """Return True if metadata contains a BC label."""
    return "bc:label" in meta and meta["bc:label"] is not None


def has_any_label(meta: dict) -> bool:
    """Return True if metadata contains any TK or BC label."""
    return has_tk_label(meta) or has_bc_label(meta)
