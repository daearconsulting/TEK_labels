"""
validation.py CARE-aware validation checks for labeled datasets.

Validation checks run before data is used, shared, or exported.
No geospatial dependencies — works with any metadata dict.

CARE Principles alignment:
    C — Collective Benefit  : validate that use serves community interests
    A — Authority to Control: validate that use is authorized by the community
    R — Responsibility      : validate that provenance chain is intact
    E — Ethics              : validate that use aligns with label conditions
"""

from __future__ import annotations

import warnings
from typing import Literal

from localcontexts.labels import TKLabel, BCLabel, has_tk_label, has_bc_label, has_any_label


# Custom exceptions

class TKViolationError(ValueError):
    """Raised when a proposed use violates a TK label restriction."""
    pass


class BCViolationError(ValueError):
    """Raised when a proposed use violates a BC label restriction."""
    pass


class ProvenanceError(ValueError):
    """Raised when label propagation has broken in a workflow."""
    pass


class MissingLabelWarning(UserWarning):
    """Emitted when a dataset that should have a label does not."""
    pass


# Validation functions

def validate_usage(
    meta: dict,
    intended_use: str,
    raise_on_violation: bool = True,
) -> bool:
    """
    Validate that an intended use is compatible with TK/BC label conditions.

    Parameters
    meta               : Metadata dict carrying TK/BC label fields
    intended_use       : Proposed use ex. 'commercial', 'research',
                         'community_internal', 'publication', 'grant_reporting'
    raise_on_violation : If True, raise TKViolationError on incompatible use.
                         If False, return False and emit a warning.

    Returns
    True if use is compatible, False if not (when raise_on_violation=False)

    Raises
    TKViolationError : If use violates a TK label and raise_on_violation=True

    Examples
    >>> meta = {"tk:label": "TK Non-Commercial", "tk:community": "Oglala Lakota Nation"}
    >>> validate_usage(meta, "research")   # returns True
    >>> validate_usage(meta, "commercial") # raises TKViolationError
    """
    violations = []

    tk_label = meta.get("tk:label")
    bc_label = meta.get("bc:label")

    # TK label checks
    if tk_label:
        if tk_label == TKLabel.NON_COMMERCIAL.value:
            if intended_use.lower() in ("commercial", "commercial_research",
                                        "for_profit", "sale"):
                violations.append(
                    f"TK label '{tk_label}' prohibits commercial use. "
                    f"Intended use '{intended_use}' is not permitted. "
                    f"Contact {meta.get('tk:contact', 'the originating community')} "
                    f"for permission."
                )

        if tk_label == TKLabel.COMMUNITY_USE_ONLY.value:
            if intended_use.lower() not in ("community_internal", "internal"):
                violations.append(
                    f"TK label '{tk_label}' restricts use to the originating "
                    f"community ({meta.get('tk:community', 'unspecified')}). "
                    f"External use '{intended_use}' is not permitted without "
                    f"explicit community consent."
                )

        if tk_label == TKLabel.SECRET_SACRED.value:
            violations.append(
                f"TK label '{tk_label}' requires special handling. "
                f"This data must not be used, shared, or published without "
                f"explicit consent from {meta.get('tk:community', 'the originating community')}. "
                f"Contact {meta.get('tk:contact', 'the community')} before any use."
            )

        if tk_label == TKLabel.CULTURALLY_SENSITIVE.value:
            if intended_use.lower() in ("publication", "public", "open_access"):
                violations.append(
                    f"TK label '{tk_label}' requires restricted access. "
                    f"Public publication or open access is not appropriate "
                    f"without community review. "
                    f"Contact {meta.get('tk:contact', 'the originating community')}."
                )

    # BC label checks
    if bc_label:
        if bc_label == BCLabel.NON_COMMERCIAL.value:
            if intended_use.lower() in ("commercial", "for_profit", "sale"):
                violations.append(
                    f"BC label '{bc_label}' prohibits commercial use of this "
                    f"biological/cultural resource data."
                )

        if bc_label == BCLabel.COMMUNITY_USE_ONLY.value:
            if intended_use.lower() not in ("community_internal", "internal"):
                violations.append(
                    f"BC label '{bc_label}' restricts use to the originating community."
                )

    # Handle violations
    if violations:
        message = "\n".join(violations)
        if raise_on_violation:
            raise TKViolationError(f"Label restriction violated:\n{message}")
        else:
            warnings.warn(
                f"Label restriction violated:\n{message}",
                UserWarning,
                stacklevel=2,
            )
            return False

    return True


def validate_label_present(
    meta: dict,
    context: str = "dataset",
    warn_only: bool = True,
) -> bool:
    """
    Check that a metadata dict carries at least one TK or BC label.
    Use this as a pre-flight check for datasets that should be labeled.
    Emits a MissingLabelWarning by default (warn_only=True).

    Parameters
    meta      : Metadata dict to check
    context   : Description of the dataset for the warning message
    warn_only : If True, return a warning. If False, raise ValueError.

    Returns
    True if label is present, False if not
    """
    if has_any_label(meta):
        return True

    message = (
        f"No TK or BC label found in {context} metadata. "
        f"If this dataset involves Indigenous Peoples' data, land, or knowledge, "
        f"a Local Contexts label should be attached. "
        f"See https://localcontexts.org/ to obtain appropriate labels."
    )

    if warn_only:
        warnings.warn(message, MissingLabelWarning, stacklevel=2)
        return False
    else:
        raise ValueError(message)


def validate_provenance_intact(
    meta: dict,
    required_fields: list[str] | None = None,
) -> bool:
    """
    Check that TK/BC label fields are present and populated in a derived dataset.
    Use after propagation steps to verify labels weren't accidentally dropped.

    Parameters
    meta            : Metadata dict of derived dataset
    required_fields : Specific tk: or bc: fields that must be present.
                      Defaults to checking for tk:label or bc:label.

    Returns
    True if provenance is intact

    Raises
    ProvenanceError : If required label fields are missing
    """
    if required_fields is None:
        # Default: at least one label must be present
        if not has_any_label(meta):
            raise ProvenanceError(
                "Provenance check failed: no TK or BC label found in derived "
                "dataset metadata. Labels may have been dropped during a "
                "transformation. Check propagate_labels() calls in your workflow."
            )
        return True

    missing = [f for f in required_fields if f not in meta or meta[f] is None]
    if missing:
        raise ProvenanceError(
            f"Provenance check failed: required label fields are missing: {missing}. "
            f"Labels may have been dropped during transformation."
        )
    return True


def validate_export_ready(
    meta: dict,
    intended_use: str,
    destination: str = "unspecified",
    require_contact: bool = False,
) -> dict:
    """
    Run all pre-export validation checks in sequence.
    Call this immediately before writing any labeled dataset to disk,
    sharing with external parties, or publishing.

    Parameters
    meta           : Metadata dict of the dataset being exported
    intended_use   : Proposed use (ex. 'research', 'publication', 'commercial')
    destination    : Where the data is going (ex. 'GitHub', 'journal supplement')
    require_contact: If True, raise an error if no contact info is in the label

    Returns
    The original meta dict if all checks pass (allows chaining)

    Raises
    TKViolationError : If intended use violates label conditions
    ProvenanceError  : If label fields are missing from metadata
    ValueError       : If require_contact=True and no contact info present

    Examples
    >>> meta = tk.attach({"source": "NDVI"})
    >>> validate_export_ready(meta, intended_use="research", destination="GitHub")
    >>> # raises if any check fails; returns meta if all pass
    """
    report = {
        "meta":         meta,
        "intended_use": intended_use,
        "destination":  destination,
        "checks":       [],
    }

    # Check 1: Label present
    label_present = has_any_label(meta)
    report["checks"].append({
        "check":  "label_present",
        "passed": label_present,
        "note":   "TK or BC label found" if label_present
                  else "No label found, consider attaching one",
    })
    if not label_present:
        warnings.warn(
            f"Exporting unlabeled dataset to {destination}. "
            "If this involves Indigenous data, attach a Local Contexts label.",
            MissingLabelWarning,
            stacklevel=2,
        )

    # Check 2: Usage compatible with label
    if label_present:
        usage_ok = validate_usage(meta, intended_use, raise_on_violation=True)
        report["checks"].append({
            "check":  "usage_compatible",
            "passed": usage_ok,
            "note":   f"Use '{intended_use}' is compatible with label",
        })

    # Check 3: Contact info present (optional)
    if require_contact:
        tk_contact = meta.get("tk:contact") or meta.get("bc:contact")
        if not tk_contact:
            raise ValueError(
                "Export requires contact information in the label metadata "
                "(tk:contact or bc:contact), but none was found. "
                "Add contact info to the TKMetadata or BCMetadata object."
            )
        report["checks"].append({
            "check":  "contact_present",
            "passed": True,
            "note":   f"Contact: {tk_contact}",
        })

    report["all_passed"] = all(c["passed"] for c in report["checks"])
    return report


# CARE principle checks

def check_collective_benefit(
    meta: dict,
    benefit_description: str,
) -> None:
    """
    CARE Collective Benefit check.
    Prompts the analyst to document how the analysis benefits the originating
    community. Does not block execution. Records the benefit description in
    the metadata as a CARE compliance note.

    Parameters
    meta                : Metadata dict (modified in place)
    benefit_description : Description of how this work benefits the community
    """
    community = meta.get("tk:community") or meta.get("bc:community", "the originating community")
    meta["care:collective_benefit"] = benefit_description
    print(
        f"CARE Collective Benefit recorded for {community}:\n"
        f"  {benefit_description}"
    )


def check_authority_to_control(
    meta: dict,
    consent_obtained: bool,
    consent_description: str = "",
) -> None:
    """
    CARE Authority to Control check.
    Records whether community consent was obtained for this use.
    Raises a warning if consent_obtained=False for sensitive labels.

    Parameters
    meta                 : Metadata dict (modified in place)
    consent_obtained     : Whether explicit community consent was obtained
    consent_description  : Description of consent process or agreement
    """
    tk_label = meta.get("tk:label", "")
    sensitive = tk_label in (
        TKLabel.SECRET_SACRED.value,
        TKLabel.COMMUNITY_USE_ONLY.value,
        TKLabel.CULTURALLY_SENSITIVE.value,
    )

    meta["care:consent_obtained"]    = consent_obtained
    meta["care:consent_description"] = consent_description

    if sensitive and not consent_obtained:
        warnings.warn(
            f"CARE Authority to Control: label '{tk_label}' requires community "
            f"consent, but consent_obtained=False. Ensure explicit authorization "
            f"from {meta.get('tk:community', 'the originating community')} before "
            f"proceeding with this use.",
            UserWarning,
            stacklevel=2,
        )
