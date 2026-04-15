"""
propagation.py Label propagation utilities.

Core rule: a dataset derived from a labeled dataset inherits that label.
Labels can be refined (made more restrictive) but never silently dropped.

No geospatial dependencies, works with any metadata dict.
"""

from __future__ import annotations

import functools
import warnings
from typing import Any, Callable

from ..labels import extract_tk_fields, extract_bc_fields, has_any_label


# Propagation functions

def propagate_labels(parent_meta: dict, child_meta: dict) -> dict:
    """
    Propagate all TK and BC label fields from parent to child metadata.

    Labels are inherited, not overwritten. If the child already has a
    label, it is preserved (assumed to be a refinement of the parent label).
    Returns a new dict; does not modify either input.

    Parameters
    parent_meta : Metadata dict of the source dataset (may carry TK/BC labels)
    child_meta  : Metadata dict of the derived dataset

    Returns
    New metadata dict with TK/BC fields propagated from parent

    Examples
    >>> parent = {"tk:label": "TK Non-Commercial", "tk:community": "Oglala Lakota Nation"}
    >>> child  = {"process": "NDVI inversion"}
    >>> result = propagate_labels(parent, child)
    >>> "tk:label" in result
    True
    """
    tk_fields = extract_tk_fields(parent_meta)
    bc_fields = extract_bc_fields(parent_meta)

    result = dict(child_meta)

    # Propagate TK fields: do not overwrite existing child labels
    for k, v in tk_fields.items():
        if k not in result:
            result[k] = v

    # Propagate BC fields:  do not overwrite existing child labels
    for k, v in bc_fields.items():
        if k not in result:
            result[k] = v

    return result


def propagate_labels_strict(parent_meta: dict, child_meta: dict) -> dict:
    """
    Strict propagation: parent label always wins, child label is overwritten.

    Use this when you need to guarantee that a derived dataset cannot
    have a less restrictive label than its parent.

    Parameters
    parent_meta : Metadata dict of the source dataset
    child_meta  : Metadata dict of the derived dataset

    Returns
    New metadata dict with TK/BC fields from parent overwriting child
    """
    tk_fields = extract_tk_fields(parent_meta)
    bc_fields = extract_bc_fields(parent_meta)
    result    = dict(child_meta)
    result.update(tk_fields)
    result.update(bc_fields)
    return result


def merge_labels(meta_a: dict, meta_b: dict) -> dict:
    """
    Merge labels from two source datasets into a combined metadata dict.

    When combining datasets with different labels, the result carries both.
    Multiple-community provenance is noted in the merged output.

    Parameters
    meta_a, meta_b : Metadata dicts from two source datasets

    Returns
    New metadata dict carrying labels from both sources

    Notes
    If both sources have the same label type (tk:label), the values are
    combined as a list. Downstream validation should check both values.
    """
    result = {}

    for prefix in ("tk:", "bc:"):
        fields_a = {k: v for k, v in meta_a.items() if k.startswith(prefix)}
        fields_b = {k: v for k, v in meta_b.items() if k.startswith(prefix)}
        all_keys = set(fields_a) | set(fields_b)

        for k in all_keys:
            val_a = fields_a.get(k)
            val_b = fields_b.get(k)

            if val_a is None:
                result[k] = val_b
            elif val_b is None:
                result[k] = val_a
            elif val_a == val_b:
                result[k] = val_a
            else:
                # Different values: combine as list to preserve both
                result[k] = [val_a, val_b]

    return result


def strip_labels(meta: dict) -> dict:
    """
    Return a copy of meta with all TK and BC label fields removed.

    This function exists only for transparency. Stripping labels from
    data derived from labeled sources is a governance violation unless
    explicitly authorized by the originating community. Document any
    use of this function carefully.

    Parameters
    meta : Metadata dict potentially containing TK/BC fields

    Returns
    New metadata dict with all tk: and bc: fields removed

    Warnings
    Always emits a warning when called, to make label removal visible.
    """
    warnings.warn(
        "strip_labels() called: removing TK/BC label fields from metadata. "
        "This is a governance-significant action. Labels should only be "
        "removed with explicit authorization from the originating community. "
        "Document this decision in your workflow.",
        UserWarning,
        stacklevel=2,
    )
    return {
        k: v for k, v in meta.items()
        if not k.startswith("tk:") and not k.startswith("bc:")
    }


# Decorator

def enforce_label_propagation(meta_arg: str = "meta"):
    """
    Decorator that enforces TK/BC label propagation on functions that
    transform datasets.

    The decorated function must accept and return a metadata dict.
    If the input metadata carries TK/BC labels, they are automatically
    propagated to the output metadata.

    Parameters
    meta_arg : Name of the metadata argument in the decorated function
               (default: 'meta')

    Usage
    @enforce_label_propagation(meta_arg="input_meta")
    def transform_dataset(data, input_meta):
        output_meta = {"process": "some transformation"}
        return transformed_data, output_meta

    If input_meta carries TK labels, output_meta will too.

    Examples
    >>> @enforce_label_propagation()
    ... def clip_to_boundary(data, meta):
    ...     clipped_meta = {"process": "clipped to boundary"}
    ...     return data, clipped_meta
    ...
    >>> source_meta = {"tk:label": "TK Non-Commercial", "source": "NDVI"}
    >>> _, result_meta = clip_to_boundary(my_data, source_meta)
    >>> "tk:label" in result_meta
    True
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract input metadata
            input_meta = kwargs.get(meta_arg)
            if input_meta is None:
                # Try positional args
                import inspect
                sig    = inspect.signature(func)
                params = list(sig.parameters.keys())
                if meta_arg in params:
                    idx        = params.index(meta_arg)
                    input_meta = args[idx] if idx < len(args) else None

            result = func(*args, **kwargs)

            # If function returns a tuple (data, meta), propagate labels
            if isinstance(result, tuple) and len(result) == 2:
                data, output_meta = result
                if isinstance(output_meta, dict) and input_meta is not None:
                    output_meta = propagate_labels(input_meta, output_meta)
                return data, output_meta

            return result

        return wrapper
    return decorator


# Provenance tagging

def add_provenance_step(
    meta: dict,
    process: str,
    source: str | None = None,
    workflow: str | None = None,
) -> dict:
    """
    Add a provenance step to metadata, aligned with IEEE 2890-2025.

    Builds a provenance chain where each transformation is recorded.
    Labels from the source are propagated automatically.

    Parameters
    meta     : Existing metadata dict
    process  : Description of the transformation applied
    source   : Source dataset description (optional)
    workflow : Notebook or script name (optional)

    Returns
    New metadata dict with prov: fields added and TK/BC labels preserved
    """
    import json as _json

    result = dict(meta)

    # Build or extend provenance chain
    existing_chain = result.get("prov:chain", [])
    if isinstance(existing_chain, str):
        try:
            existing_chain = _json.loads(existing_chain)
        except Exception:
            existing_chain = [existing_chain]

    step = {"process": process}
    if source:
        step["source"] = source
    if workflow:
        step["workflow"] = workflow

    existing_chain.append(step)
    result["prov:chain"] = existing_chain

    # Convenience fields for the most recent step
    result["prov:process"] = process
    if source:
        result["prov:source"] = source
    if workflow:
        result["prov:workflow"] = workflow

    return result
