from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass

from ..config import COLLECTION_PATTERN, PROPERTY_PATTERN, RIG_ID
from ..utils import get_property_bone


@dataclass
class CollectionData:
    """Données parsées d'une bone collection."""

    name: str
    part: str
    sub_part: str = ""
    side: str = ""
    custom_side: str = ""
    c_type: str = ""
    fake: bool = False

    # Propriétés calculées

    @property
    def is_left(self) -> bool:
        return self.side == ".L"

    @property
    def is_right(self) -> bool:
        return self.side == ".R"

    @property
    def has_custom_type(self) -> bool:
        return self.c_type != ""

    @property
    def is_prop(self) -> bool:
        return self.c_type == ":PROP"

    @property
    def is_mask(self) -> bool:
        return self.c_type == ":MASK"

    @property
    def is_order(self) -> bool:
        return self.c_type == ":ORDER"

    @property
    def is_fake(self) -> bool:
        return self.fake

    @property
    def has_side(self) -> bool:
        return bool(self.side or self.custom_side)

    @property
    def mirror_name(self) -> str | None:
        if self.side == ".L":
            return self.name[:-1] + "R"
        elif self.side == ".R":
            return self.name[:-1] + "L"
        return None

    @property
    def base_name(self) -> str:
        """Nom sans le side."""
        if self.side:
            return self.name[:-2]
        return self.name


@dataclass
class PropertyData:
    """Données parsées des custom properties."""

    name: str
    part: str
    sub_part: str = ""
    side: str = ""
    custom_side: str = ""
    fake: bool = False

    @property
    def is_left(self) -> bool:
        return self.side == ".L"

    @property
    def is_right(self) -> bool:
        return self.side == ".R"

    @property
    def is_fake(self) -> bool:
        return self.fake

    @property
    def has_side(self) -> bool:
        return bool(self.side or self.custom_side)

    @property
    def mirror_name(self) -> str | None:
        if self.side == ".L":
            return self.name[:-1] + "R"
        elif self.side == ".R":
            return self.name[:-1] + "L"
        return None

    @property
    def base_name(self) -> str:
        """Nom sans le side."""
        if self.side:
            return self.name[:-2]
        return self.name


@dataclass
class RigCache:
    """Cache pour un rig."""

    collections: dict[str, CollectionData]  # name → data
    parts: list[str]  # Ordre des parts
    hierarchy: list[list[CollectionData]]  # Groupé + fake pour layout
    c_hash: tuple  # Pour détecter les changements

    properties: dict[str, PropertyData]
    p_parts: list[str]
    p_hierarchy: list[list[CollectionData]]
    p_hash: tuple


# Cache global : rig_id → RigCache
_cache: dict[str, RigCache] = {}


def _compute_hierarchy(
    collections: dict[str, CollectionData], parts: list[str]
) -> list[list[CollectionData]]:
    """Construit la hiérarchie avec fake collections."""
    ordered = []
    ordered_names = set()

    for part in parts:
        part_collections = []
        part_cols = [c for c in collections.values() if c.part == part]

        for col in part_cols:
            if col.name in ordered_names:
                continue

            if not col.side:
                part_collections.append(col)
                ordered_names.add(col.name)
            else:
                base = col.base_name

                for s in (".L", ".M", ".R"):
                    full_name = f"{base}{s}"

                    if full_name in ordered_names:
                        continue

                    if full_name in collections:
                        part_collections.append(collections[full_name])
                        ordered_names.add(full_name)
                    elif s != ".M":
                        fake = CollectionData(
                            name="",
                            part=part,
                            sub_part=col.sub_part,
                            side=s,
                            fake=True,
                        )
                        part_collections.append(fake)

        ordered.append(part_collections)

    return ordered


def _compute_hash(armature) -> tuple:
    """Hash rapide pour détecter les changements."""
    cols = armature.data.collections
    return (len(cols), tuple(c.name for c in cols))


def _parse_collection(name: str) -> CollectionData | None:
    """Parse un nom de collection."""
    match = COLLECTION_PATTERN.match(name)
    if not match:
        return None

    return CollectionData(
        name=name,
        part=match.group("part") or "",
        sub_part=match.group("sub_part") or "",
        side=match.group("side") or "",
        custom_side=match.group("custom_side") or "",
        c_type=match.group("col_type") or "",
    )


def get_rig_cache(armature) -> RigCache:
    """Récupère ou crée le cache pour un rig."""
    rig_id = armature.data.get(RIG_ID, armature.name)
    current_c_hash = _compute_hash(armature)
    current_p_hash = _compute_p_hash(armature)

    recompute_c = rig_id not in _cache or _cache[rig_id].c_hash != current_c_hash
    recompute_p = rig_id not in _cache or _cache[rig_id].p_hash != current_p_hash

    old = _cache.get(rig_id)

    collections = deepcopy(old.collections) if old else {}
    c_parts = deepcopy(old.parts) if old else []
    c_hierarchy = deepcopy(old.hierarchy) if old else []

    properties = deepcopy(old.properties) if old else {}
    p_parts = deepcopy(old.p_parts) if old else []
    p_hierarchy = deepcopy(old.p_hierarchy) if old else []

    if recompute_c:
        collections = {}
        c_parts = []

        for col in armature.data.collections:
            data = _parse_collection(col.name)
            if data:
                collections[col.name] = data
                if data.part not in c_parts:
                    c_parts.append(data.part)

        c_hierarchy = _compute_hierarchy(collections, c_parts)

    if recompute_p:
        properties = {}
        p_parts = []

        for prop in get_all_properties(armature):
            data = _parse_property(prop)
            if data:
                properties[prop] = data
                if data.part not in p_parts:
                    p_parts.append(data.part)

        p_parts_ordered = list(dict.fromkeys([p for p in c_parts if p in p_parts] + p_parts))
        p_hierarchy = _compute_properties_hierarchy(properties, p_parts_ordered)

    _cache[rig_id] = RigCache(
        collections=collections,
        parts=c_parts,
        hierarchy=c_hierarchy,
        c_hash=current_c_hash,
        properties=properties,
        p_parts=p_parts,
        p_hierarchy=p_hierarchy,
        p_hash=current_p_hash,
    )

    return _cache[rig_id]


# === Accesseurs simples ===


def get_collection(armature, name: str) -> CollectionData | None:
    """Récupère une collection par nom."""
    return get_rig_cache(armature).collections.get(name)


def get_all_collections(armature) -> list[CollectionData]:
    """Toutes les collections."""
    return list(get_rig_cache(armature).collections.values())


def get_collections_by_part(armature, part: str) -> list[CollectionData]:
    """Collections d'une part."""
    cache = get_rig_cache(armature)
    return [c for c in cache.collections.values() if c.part == part]


def get_parts(armature) -> list[str]:
    """Liste des parts dans l'ordre."""
    return get_rig_cache(armature).parts


def get_collections_hierarchy(armature) -> list[list[CollectionData]]:
    cache = get_rig_cache(armature)

    by_part = defaultdict(list)
    for c in cache.collections.values():
        by_part[c.part].append(c)

    return [by_part[p] for p in cache.parts]


# === Properties ===


def get_all_properties(armature) -> list[str]:
    pb = get_property_bone(armature)
    if pb is not None:
        return list(pb.keys())
    else:
        return []


def _parse_property(name: str) -> PropertyData | None:
    """Parse un nom de collection."""
    match = PROPERTY_PATTERN.match(name)
    if not match:
        return None

    return PropertyData(
        name=name,
        part=match.group("part") or "",
        sub_part=match.group("sub_part") or "",
        side=match.group("side") or "",
        custom_side=match.group("custom_side") or "",
    )


def _compute_properties_hierarchy(
    properties: dict[str, PropertyData], parts: list[str]
) -> list[list[PropertyData]]:
    """Construit la hiérarchie avec fake collections."""
    ordered = []
    ordered_names = set()

    for part in parts:
        part_properties = []
        part_cols = [c for c in properties.values() if c.part == part]

        for col in part_cols:
            if col.name in ordered_names:
                continue

            if not col.side:
                part_properties.append(col)
                ordered_names.add(col.name)
            else:
                base = col.base_name

                for s in (".L", ".M", ".R"):
                    full_name = f"{base}{s}"

                    if full_name in ordered_names:
                        continue

                    if full_name in properties:
                        part_properties.append(properties[full_name])
                        ordered_names.add(full_name)
                    elif s != ".M":
                        fake = PropertyData(
                            name="", part=part, sub_part=col.sub_part, side=s, fake=True
                        )
                        part_properties.append(fake)

        ordered.append(part_properties)

    return ordered


def _compute_p_hash(armature) -> tuple:
    """Hash rapide pour détecter les changements."""
    props = get_all_properties(armature)
    return (len(props), tuple(p for p in props))
