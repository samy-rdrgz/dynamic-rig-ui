"""Configuration et constantes pour l'addon Rig UI."""

# =============================================================================
# RIG IDENTIFICATION
# =============================================================================
# Set a rig ID in your armature custom properties using a string
RIG_ID = "drigui_rig_id"
RIG_NAME = "drigui_rig_name"
PROPERTY_BONE = "drigui_properties"
ACTIVE = "drigui_has_ui"


# =============================================================================
# PARSING CONFIGURATION
# =============================================================================
import re

COLLECTION_PATTERN = re.compile(
    r"^(?P<part>[A-Z]+)"
    r"(?:_(?P<sub_part>[A-Z0-9_]+))?"
    r"(?:(?P<side>\.[LMRXYZ])|(?P<custom_side>\.\d+)|(?P<col_type>:[A-Z]+))?$"
)


# =============================================================================
# BODY PARTS CONFIGURATION
# =============================================================================
NO_BODY_PREFIX: list[str] = []  # Input_no_body_prefix

PREFIX_ORDER: list[str] = [
    "ROOT",
    "BODY",
    "CLOTHES",
    "HEAD",
    "HAIR",
    "NECK",
    "SPINE",
    "CHEST",
    "ARM",
    "HAND",
    "PELVIS",
    "LEG",
    "FOOT",
]

# =============================================================================
# IK/FK CHAIN DEFINITIONS
# =============================================================================
LEG_SWITCH_PROP = "LEG_FK_IK"

LEG_FK: dict[str, str] = {
    "target_C": "MCH_FK_IK_FOOT_IK",
    "target_pole": "MCH_FK_IK_LEG_IK_POLE",
    "A": "LEG_FK",
    "B": "SHIN_FK",
    "C": "FOOT_FK",
}

LEG_IK: dict[str, str] = {
    "C": "FOOT_IK",
    "pole": "LEG_IK_POLE",
    "target_A": "MCH_LEG_IK",
    "target_B": "MCH_SHIN_IK",
    "target_C": "MCH_FOOT_IK",
}

ARM_SWITCH_PROP = "ARM_FK_IK"

ARM_FK: dict[str, str] = {
    "target_C": "MCH_FK_IK_HAND_IK",
    "target_pole": "MCH_FK_IK_ARM_IK_POLE",
    "A": "ARM_FK",
    "B": "FOREARM_FK",
    "C": "HAND_FK",
}

ARM_IK: dict[str, str] = {
    "C": "HAND_IK",
    "pole": "ARM_IK_POLE",
    "target_A": "MCH_ARM_IK",
    "target_B": "MCH_FOREARM_IK",
    "target_C": "MCH_HAND_IK",
}

# =============================================================================
# UI SETTINGS
# =============================================================================
UI_RATIO = 0.6
UI_RATIO_PROPS = 0.45
