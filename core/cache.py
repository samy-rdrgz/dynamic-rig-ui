"""Cache de données parsées pour les rigs."""

from copy import deepcopy
from dataclasses import dataclass

from ..config import COLLECTION_PATTERN, PROPERTY_BONE, PROPERTY_PATTERN, RIG_ID
from ..utils import get_property_bone


@dataclass
class CollectionData:
    """Données parsées d'une bone collection."""

    name: str
    part: str
    sub_part: str = ""
    side: str = ""
    custom_side: str = ""
    col_type: str = ""
    fake: bool = False

    @property
    def is_left(self) -> bool:
        return self.side == ".L"

    @property
    def is_right(self) -> bool:
        return self.side == ".R"

    @property
    def has_custom_type(self) -> bool:
        return self.col_type != ""

    @property
    def is_prop(self) -> bool:
        return self.col_type == ":PROP"

    @property
    def is_mask(self) -> bool:
        return self.col_type == ":MASK"

    @property
    def is_order(self) -> bool:
        return self.col_type == ":ORDER"

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
    collections_hash: tuple  # Pour détecter les changements

    properties: dict[str, PropertyData]
    props_parts: list[str]
    props_hierarchy: list[list[PropertyData]]
    props_hash: tuple


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


def _compute_collections_hash(armature) -> tuple:
    """Hash rapide pour détecter les changements de collections."""
    cols = armature.data.collections
    return (len(cols), tuple(c.name for c in cols))


def _compute_props_hash(armature) -> tuple:
    """Hash rapide pour détecter les changements de custom props."""
    props = get_all_properties(armature)
    return (len(props), tuple(props))


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
        col_type=match.group("col_type") or "",
    )


def get_rig_cache(armature) -> RigCache:
    """Récupère ou crée le cache pour un rig."""
    rig_id = armature.data.get(RIG_ID, armature.name)
    current_collections_hash = _compute_collections_hash(armature)
    current_props_hash = _compute_props_hash(armature)

    recompute_collections = (
        rig_id not in _cache or _cache[rig_id].collections_hash != current_collections_hash
    )
    recompute_props = rig_id not in _cache or _cache[rig_id].props_hash != current_props_hash

    old = _cache.get(rig_id)

    # Valeurs par défaut depuis le cache existant
    collections = deepcopy(old.collections) if old else {}
    collections_parts = deepcopy(old.parts) if old else []
    collections_hierarchy = deepcopy(old.hierarchy) if old else []

    properties = deepcopy(old.properties) if old else {}
    props_parts = deepcopy(old.props_parts) if old else []
    props_hierarchy = deepcopy(old.props_hierarchy) if old else []

    if recompute_collections:
        collections = {}
        collections_parts = []

        for col in armature.data.collections:
            data = _parse_collection(col.name)
            if data:
                collections[col.name] = data
                if data.part not in collections_parts:
                    collections_parts.append(data.part)

        collections_hierarchy = _compute_hierarchy(collections, collections_parts)

    # Lit PROPERTY_BONE directement sur l'armature, sans bpy.context
    property_bone_name = armature.data.get(PROPERTY_BONE)

    if (recompute_props or recompute_collections) and property_bone_name:
        properties = {}
        props_parts = []

        for prop in get_all_properties(armature):
            data = _parse_property(prop)
            if data:
                properties[prop] = data
                if data.part not in props_parts:
                    props_parts.append(data.part)

        # Respecte l'ordre des collections pour les parts communes
        props_parts_ordered = list(
            dict.fromkeys([p for p in collections_parts if p in props_parts] + props_parts)
        )
        props_hierarchy = _compute_properties_hierarchy(properties, props_parts_ordered)

    elif recompute_props and not property_bone_name:
        properties = {}
        props_parts = []
        props_hierarchy = []
        current_props_hash = (0, ())

    _cache[rig_id] = RigCache(
        collections=collections,
        parts=collections_parts,
        hierarchy=collections_hierarchy,
        collections_hash=current_collections_hash,
        properties=properties,
        props_parts=props_parts,
        props_hierarchy=props_hierarchy,
        props_hash=current_props_hash,
    )

    return _cache[rig_id]


# === Accesseurs ===


def get_collection(armature, name: str) -> CollectionData | None:
    """Récupère une collection par nom."""
    return get_rig_cache(armature).collections.get(name)


def get_all_collections(armature) -> list[CollectionData]:
    """Toutes les collections."""
    return list(get_rig_cache(armature).collections.values())


def get_collections_by_part(armature, part: str) -> list[CollectionData]:
    """Collections d'une part (accepte plusieurs parts séparées par virgule)."""
    cache = get_rig_cache(armature)
    return [c for c in cache.collections.values() if c.part in part.split(",")]


def get_parts(armature) -> list[str]:
    """Liste des parts dans l'ordre."""
    return get_rig_cache(armature).parts


# === Properties ===


def get_all_properties(armature) -> list[str]:
    """Toutes les custom props du property bone."""
    property_bone = get_property_bone(armature)
    if property_bone is not None:
        return list(property_bone.keys())
    return []


def _parse_property(name: str) -> PropertyData | None:
    """Parse un nom de custom property."""
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
    """Construit la hiérarchie de properties avec fakes pour le layout L/R."""
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
