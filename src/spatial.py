"""
spatial.py Geometry-scoped TK/BC label assignment.

This module requires geopandas and shapely (optional dependencies).
Import guard at the top surfaces a helpful error if not installed.

Labels are attached not just to whole datasets but to
specific geographic extents. A dataset intersecting a labeled territory
inherits that label. Mixed datasets (where only some areas carry
restrictions) are handled by the spatial assignment functions here.
"""

from __future__ import annotations

import warnings
from typing import Optional

try:
    import geopandas as gpd
    from shapely.geometry import box
    from shapely.geometry.base import BaseGeometry
    _SPATIAL_AVAILABLE = True
except ImportError:
    _SPATIAL_AVAILABLE = False

from .labels import TKLabel, BCLabel, TKMetadata, BCMetadata
from .propagation import propagate_labels


def _require_spatial():
    if not _SPATIAL_AVAILABLE:
        raise ImportError(
            "localcontexts.spatial requires geopandas and shapely. "
            "Install with: pip install localcontexts-geo[spatial] "
            "or: conda install geopandas"
        )


# Spatial label assignment

def assign_label_by_geometry(
    dataset_geometry: "BaseGeometry",
    label_zones: "gpd.GeoDataFrame",
    label_col: str = "tk_label",
    community_col: str = "community",
    authority_col: Optional[str] = None,
    usage_col: Optional[str] = None,
) -> Optional[dict]:
    """
    Assign a TK label to a dataset based on spatial overlap with labeled zones.
    Returns the label metadata dict for the first overlapping zone, or None
    if no overlap exists.

    Parameters
    dataset_geometry : Shapely geometry of the dataset extent or footprint
    label_zones      : GeoDataFrame with label zone polygons
    label_col        : Column in label_zones containing TK label values
    community_col    : Column in label_zones containing community names
    authority_col    : Column containing authority info (optional)
    usage_col        : Column containing usage description (optional)

    Returns
    dict with tk: prefixed fields if overlap found, None otherwise

    Examples
    >>> # label_zones is a GeoDataFrame with tribal boundary polygons
    >>> meta = assign_label_by_geometry(
    ...     dataset_geometry=ndvi_bounds,
    ...     label_zones=tribal_boundaries,
    ...     label_col="tk_label",
    ...     community_col="tribe_name",
    ... )
    >>> if meta:
    ...     dataset_meta = propagate_labels(meta, dataset_meta)
    """
    _require_spatial()

    label_zones_proj = label_zones.copy()
    if label_zones_proj.crs is None:
        warnings.warn(
            "label_zones has no CRS set. Assuming EPSG:4326.",
            UserWarning,
            stacklevel=2,
        )

    for _, zone in label_zones_proj.iterrows():
        if zone.geometry is None:
            continue
        if dataset_geometry.intersects(zone.geometry):
            meta = {
                "tk:label":     zone.get(label_col),
                "tk:community": zone.get(community_col),
            }
            if authority_col and authority_col in zone.index:
                meta["tk:authority"] = zone.get(authority_col)
            if usage_col and usage_col in zone.index:
                meta["tk:usage"] = zone.get(usage_col)
            return meta

    return None


def assign_labels_to_geodataframe(
    gdf: "gpd.GeoDataFrame",
    label_zones: "gpd.GeoDataFrame",
    label_col: str = "tk_label",
    community_col: str = "community",
    output_label_col: str = "tk_label",
    output_community_col: str = "tk_community",
    how: str = "intersects",
) -> "gpd.GeoDataFrame":
    """
    Spatially assign TK labels to features in a GeoDataFrame based on overlap
    with labeled zone polygons.
    Features that do not overlap any labeled zone receive None for label fields.

    Parameters
    gdf                  : GeoDataFrame to label
    label_zones          : GeoDataFrame with label zone polygons
    label_col            : Column in label_zones with TK label values
    community_col        : Column in label_zones with community names
    output_label_col     : Name for the label column in the output GeoDataFrame
    output_community_col : Name for the community column in the output
    how                  : Spatial predicate such as 'intersects' or 'within'

    Returns
    GeoDataFrame with TK label columns added

    Examples
    >>> labeled_gdf = assign_labels_to_geodataframe(
    ...     gdf=vegetation_polygons,
    ...     label_zones=tribal_boundaries,
    ...     label_col="tk_label",
    ...     community_col="tribe_name",
    ... )
    """
    _require_spatial()

    # Align CRS
    if label_zones.crs != gdf.crs:
        label_zones = label_zones.to_crs(gdf.crs)

    joined = gpd.sjoin(
        gdf,
        label_zones[[community_col, label_col, "geometry"]],
        how="left",
        predicate=how,
    )

    # Handle multiple matches (takes the first most specific zone)
    joined = joined.groupby(joined.index).first()

    result = gdf.copy()
    result[output_label_col]     = joined.get(label_col)
    result[output_community_col] = joined.get(community_col)

    n_labeled   = result[output_label_col].notna().sum()
    n_unlabeled = result[output_label_col].isna().sum()

    print(
        f"Spatial label assignment complete:\n"
        f"  {n_labeled} features labeled\n"
        f"  {n_unlabeled} features have no overlapping label zone"
    )

    return result


def build_label_zone(
    geometry: "BaseGeometry",
    tk_meta: TKMetadata,
    zone_name: str = "",
    crs: str = "EPSG:4326",
) -> "gpd.GeoDataFrame":
    """
    Create a single-row GeoDataFrame representing a labeled authority zone.
    Useful for building label zone layers from scratch when working with
    Tribal boundary data.

    Parameters
    geometry  : Shapely geometry defining the authority zone
    tk_meta   : TKMetadata object to attach to the zone
    zone_name : Name for this zone (optional)
    crs       : Coordinate reference system string

    Returns
    Single-row GeoDataFrame with geometry and TK label fields

    Examples
    >>> zone = build_label_zone(
    ...     geometry=pine_ridge_polygon,
    ...     tk_meta=tk,
    ...     zone_name="Pine Ridge Reservation",
    ... )
    """
    _require_spatial()

    data = {
        "zone_name": [zone_name],
        "geometry":  [geometry],
        **{k: [v] for k, v in tk_meta.to_dict().items()},
    }
    return gpd.GeoDataFrame(data, crs=crs)


def get_label_coverage_report(
    gdf: "gpd.GeoDataFrame",
    label_col: str = "tk_label",
) -> dict:
    """
    Summarize TK label coverage across features in a GeoDataFrame.
    Returns a dict with counts of labeled vs. unlabeled features,
    label distribution, and area coverage if geometry is polygon.

    Parameters
    gdf       : GeoDataFrame with a TK label column
    label_col : Name of the column containing TK label values

    Returns
    Coverage report dict
    """
    _require_spatial()

    total     = len(gdf)
    labeled   = gdf[label_col].notna().sum()
    unlabeled = total - labeled

    report = {
        "total_features":    total,
        "labeled_features":  int(labeled),
        "unlabeled_features": int(unlabeled),
        "label_coverage_pct": round(labeled / total * 100, 1) if total > 0 else 0.0,
        "label_distribution": gdf[label_col].value_counts().to_dict(),
    }

    # Area coverage if polygon geometry
    geom_types = gdf.geometry.geom_type.unique()
    if any(t in ("Polygon", "MultiPolygon") for t in geom_types):
        try:
            proj = gdf.to_crs("EPSG:5070")  # Albers Equal Area
            labeled_area   = proj[gdf[label_col].notna()].geometry.area.sum() / 1e6
            total_area     = proj.geometry.area.sum() / 1e6
            report["labeled_area_km2"]   = round(labeled_area, 1)
            report["total_area_km2"]     = round(total_area, 1)
            report["area_coverage_pct"]  = round(labeled_area / total_area * 100, 1) \
                                           if total_area > 0 else 0.0
        except Exception:
            pass  # CRS projection may fail for some geometries

    return report
