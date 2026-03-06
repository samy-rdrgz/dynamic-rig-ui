# Dynamic Rig UI

Dynamic user interface generation for Blender rigs. Driven by bone collections, it displays their visibility toggles, custom properties, mask modifiers of child objects, and IK/FK smart switch buttons.

## Demo
[![Dynamic Rig UI - Demo](https://vumbnail.com/1171151228.jpg)](https://vimeo.com/1171151228)

## Installation

1. Download ZIP
2. Blender > Edit > Preferences > Add-ons > Install
3. Activate the addon

## Compatibility

- Blender 5.0+

---

## Nomenclature

This addon uses Blender's native structures (bone collections and custom properties).  
Panels are generated automatically based on naming conventions.

---

### Collections — Main Panel

Collections are only displayed if their name matches this structure:

```
BASEPART(_SUB_PART)(.SUFFIX)
```

| Segment | Format | Description |
|---|---|---|
| `BASEPART` | uppercase only | Overall category — `BODY`, `ARM`, `CLOTHES`, `SWORD` |
| `_SUB_PART` | uppercase, digits, `_` — optional | Specific sub-part — `FINGER`, `FK`, `IK`, `TWEAK`, `BELT` |
| `SUFFIX` | optional | Side, custom side, or type (see below) |

**Suffix types:**

- `.SIDE` → `.L`, `.M` or `.R` — model sides. Collections sharing the same `BASEPART` + `SUB_PART` but with different sides are aligned on the same row.
- `.CUSTOM_SIDE` → `.` + digit — model variants (`SPINE.1`, `SPINE.2`) or used to align multiple collections on the same row (`SPINE_FK.1`, `SPINE_TWEAK.2`).
- `:TYPE` → `:ORDER`, `:PROP` or `:MASK`
  - `:ORDER` — creates a placeholder entry to control ordering in the Props and Masks panels.
  - `:PROP` — displays one or several custom properties inline in the Main panel.
  - `:MASK` — displays one or several mask toggles inline in the Main panel.

> **Tips:**  
> Bone collections are reordered in the panel by `BASEPART` and by side — they don't need to be perfectly sorted in Blender.  
> Only first-level (non-nested) collections are parsed.  
> Only **UPPERCASE** collections are used — technical/backend collections can share the same structure but in lowercase to stay hidden.

```python
COLLECTION_PATTERN = re.compile(
    r"^(?P<part>[A-Z]+)"
    r"(?:_(?P<sub_part>[A-Z0-9_]+))?"
    r"(?:(?P<side>\.[LMRXYZ])|(?P<custom_side>\.\d+)|(?P<col_type>:[A-Z]+))?$"
)
```

---

### Custom Properties — Props Panel

Properties are grouped by `BASEPART` and ordered according to bone collections. Only properties stored on the `drigui_properties` pose bone are displayed, if their name matches:

```
BASEPART(_SUB_PART)(.SUFFIX)
```

Same `BASEPART`, `SUB_PART`, and `SUFFIX` rules as collections apply.

**Enum menu:** A custom property can be rendered as a dropdown menu instead of a slider. To enable this, set the property's **description** field to a JSON mapping of integer values to labels:

```json
{"0": "FK", "1": "IK"}
{"0": "ROOT", "1": "TORSO", "2": "HEAD"}
```

```python
PROPERTY_PATTERN = re.compile(
    r"^(?P<part>[A-Z]+)"
    r"(?:_(?P<sub_part>[A-Z0-9_]+))?"
    r"(?:(?P<side>\.[LMRXYZ])|(?P<custom_side>\.\d+))?$"
)
```

---

### Mask Modifiers — Masks Panel

Displays toggle buttons for mask modifiers on armature child objects.  
Only modifiers whose vertex group name matches this structure are captured:

```
MASK_NAME(.SIDE)
```

| Segment | Format | Description |
|---|---|---|
| `NAME` | uppercase, digits, `_` | Part or sub-part of the mask. If it starts with an existing `BASEPART`, it is ordered and grouped accordingly. |
| `.SIDE` | `.L`, `.M`, `.R` or `.digit` — optional | Side or variant number. |

> If multiple objects share the same vertex group name, a single button toggles all of them.

```python
MASK_PATTERN = re.compile(r"^(MASK_)([A-Z0-9_]+)(.([LMR]|(\d)))?$", re.MULTILINE)
```

---

## Setup

Main panels are located in the **Item** tab of the sidebar.  
The setup/config panel is in the **Dyn RigUI** tab.

### 1. Initialize

1. Select your armature.
2. In the **Dyn RigUI** panel, type a rig name (uppercase, digits or `_`, 3 characters minimum) and click **Create**.

The following custom properties are created on the armature:

| Property | Description |
|---|---|
| `drigui_rig_id` | Random unique string identifier |
| `drigui_rig_name` | Human-readable display name |
| `drigui_properties` | Name of the pose bone holding all driver custom properties |
| `drigui_has_ui` | Toggle to show/hide all panels for this rig without deleting its config |
| `drigui_ik_chains` | Stores the IK/FK chain configuration |

### 2. Configure custom properties

If your rig has driver custom properties, verify that `drigui_properties` points to the correct pose bone. Leave it empty if unused.

### 3. Configure IK/FK chains

If your rig has IK/FK chains, write the configuration in a Blender **Text Editor** block, then use the **Apply** button in the settings panel to store it on the armature. It can be updated at any time.

The JSON must follow this structure (no side suffixes — `.L`, `.R`, `.1`, etc. are added automatically at runtime):

```json
{
    "LEG": {
        "switch_prop": "LEG_FK_IK",
        "fk": {
            "copy_end":    "MCH_FK_IK_FOOT_IK",
            "copy_pole":   "MCH_FK_IK_LEG_IK_POLE",
            "past_upper":  "LEG_FK",
            "past_middle": "SHIN_FK",
            "past_end":    "FOOT_FK"
        },
        "ik": {
            "copy_upper":  "MCH_LEG_IK",
            "copy_middle": "MCH_SHIN_IK",
            "copy_end":    "MCH_FOOT_IK",
            "past_end":    "FOOT_IK",
            "past_pole":   "LEG_IK_POLE"
        }
    },
    "ARM": {
        "switch_prop": "ARM_FK_IK",
        "fk": {
            "copy_end":    "MCH_FK_IK_HAND_IK",
            "copy_pole":   "MCH_FK_IK_ARM_IK_POLE",
            "past_upper":  "ARM_FK",
            "past_middle": "FOREARM_FK",
            "past_end":    "HAND_FK"
        },
        "ik": {
            "copy_upper":  "MCH_ARM_IK",
            "copy_middle": "MCH_FOREARM_IK",
            "copy_end":    "MCH_HAND_IK",
            "past_end":    "HAND_IK",
            "past_pole":   "ARM_IK_POLE"
        }
    },
    "PONYTAIL": {
        "switch_prop": "PONYTAIL_FK_IK",
        "fk": { ... },
        "ik": { ... }
    }
}
```

**Convention:**
- `copy_*` — **source** bone (read) — typically an MCH bone tracking the opposite chain.
- `past_*` — **destination** bone (written) — the visible controller.

Chains without a side (e.g. a ponytail) work exactly the same — simply omit the suffix from bone names in the JSON.

---

## Usage

### Main Panel

**Panel header:**
- `>` — collapse/expand the panel
- `>` — collapse/expand all boxes
- `👁 CONTROLLERS` — toggle visibility of all collections  
  *(+ Ctrl → solo visibility / + Shift → collapse all boxes)*

**Box header:**
- `👁 BASEPART` — toggle visibility of all collections in this box  
  *(+ Ctrl → solo visibility / + Shift → collapse this box)*
- `>` — collapse/expand this box

**Box content:**
- Visibility toggle buttons for each collection. If any collection is in solo mode, solo visibility is shown instead.
- `:PROP` entry → displays matching custom properties inline (slider or enum menu).
- `:MASK` entry → displays matching mask toggles inline.

---

### Properties Panel

**Panel header:**
- `>` — collapse/expand the panel
- `> PROPERTIES` — collapse/expand all boxes

**Box header:**
- `> BASEPART` — collapse/expand this box

**Box content:**
- Custom property inputs (slider or enum menu based on the property description).
- Enum menu: click to choose from the configured options. Ctrl+Click to input any raw value directly (e.g. `0.5` for a half FK/IK blend).

---

### Masks Panel

**Panel header:**
- `👁 MASKS` — toggle visibility of all masks

**Content:**
- Toggle buttons for each mask modifier group.
- If multiple objects share the same vertex group name, one button controls all of them.

---

### Tools Panel

**Snap IK/FK:**  
Automatically detects which chain and which direction to snap based on the selected bone. Copies transforms from the opposite kinematic chain and switches the driver property. If auto-key is enabled, a keyframe is inserted automatically. Configured chains are listed below the button.

---

### Settings Panel

**Rig UI setup** (Dyn RigUI tab):
- Input field and **Create** button to initialize Dynamic Rig UI on the selected armature.
- Once initialized: displays rig name, ID, property bone field, IK chains text block picker, and a **Remove** button.

**Setup tools:**
- **Create Mask Modifiers** — scans all child objects, extracts vertex groups following the mask nomenclature, and creates the corresponding mask modifiers.
- **Symmetrize Collections** — creates the missing mirror collection for any collection found with a `.L` or `.R` suffix.
- **Create Custom Shape** — creates a new mesh object aligned to the active pose bone's transforms and assigns it as its custom shape. Select two bones to use the second as override transform.

---

### Armature Custom Properties

`drigui_has_ui` — set to `False` to hide all Dynamic Rig UI panels for this armature without losing its configuration.

---

## Credits

**Author:** Samy RODRIGUEZ  
**Version:** 1.0.0  
**License:** [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.html)

---

## Contact & Support

- 📧 Email : samy.rodriguez@proton.me
- 🐛 Bug reports : GitHub @samy-rdrgz or by mail

## Changelog

### 1.0.0
- Initial release
