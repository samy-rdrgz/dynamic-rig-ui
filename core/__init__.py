"""Core de l'addon : cache et structures de données."""

from .cache import (
    CollectionData,
    PropertyData,
    RigCache,
    _cache,
    _compute_collections_hash,
    _compute_hierarchy,
    _compute_properties_hierarchy,
    _compute_props_hash,
    _parse_collection,
    _parse_property,
    get_all_collections,
    get_all_properties,
    get_collection,
    get_collections_by_part,
    get_parts,
    get_rig_cache,
)

classes = ()

__all__ = [
    "classes",
    "_cache",
    "_compute_collections_hash",
    "_compute_hierarchy",
    "_parse_collection",
    "get_collection",
    "get_collections_by_part",
    "get_parts",
    "get_rig_cache",
    "get_all_collections",
    "get_all_properties",
    "CollectionData",
    "PropertyData",
    "RigCache",
    "_parse_property",
    "_compute_properties_hierarchy",
    "_compute_props_hash",
]
