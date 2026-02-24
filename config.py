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
PROPERTY_PATTERN = re.compile(
    r"^(?P<part>[A-Z]+)"
    r"(?:_(?P<sub_part>[A-Z0-9_]+))?"
    r"(?:(?P<side>\.[LMRXYZ])|(?P<custom_side>\.\d+))?$"
)
MASK_PATTERN = re.compile(r"^(MASK_)([A-Z0-9_]+)(.([LMR]|(\d)))?$", re.MULTILINE)


# =============================================================================
# IK/FK CHAIN DEFINITIONS
# =============================================================================
# Les chaînes IK/FK ne sont plus hardcodées ici.
# Elles sont définies par rig via une custom prop JSON sur l'armature.
# Pas besoin de faire un dict par side (.L/.M/.R) ou par variante (.1/.2/.../.9),
# supprimer le suffix dans le nom des bones.
# Clé de la custom prop à créer sur armature.data :
IK_CHAINS = "drigui_ik_chains"

# Exemple de valeur JSON à coller dans la custom prop :
# {
#    "LEG": {
#        "switch_prop": "LEG_FK_IK",
#        "fk": {
#            "copy_end": "MCH_FK_IK_FOOT_IK",
#            "copy_pole": "MCH_FK_IK_LEG_IK_POLE",
#            "past_upper": "LEG_FK",
#            "past_middle": "SHIN_FK",
#            "past_end": "FOOT_FK"
#        },
#        "ik": {
#            "copy_upper": "MCH_LEG_IK",
#            "copy_middle": "MCH_SHIN_IK",
#            "copy_end": "MCH_FOOT_IK",
#            "past_end": "FOOT_IK",
#            "past_pole": "LEG_IK_POLE"
#        }
#    },
#    "ARM": {
#        "switch_prop": "ARM_FK_IK",
#        "fk": {
#            "copy_end": "MCH_FK_IK_HAND_IK",
#            "copy_pole": "MCH_FK_IK_ARM_IK_POLE",
#            "past_upper": "ARM_FK",
#            "past_middle": "FOREARM_FK",
#            "past_end": "HAND_FK"
#        },
#        "ik": {
#            "copy_upper": "MCH_ARM_IK",
#            "copy_middle": "MCH_FOREARM_IK",
#            "copy_end": "MCH_HAND_IK",
#            "past_end": "HAND_IK",
#            "past_pole": "ARM_IK_POLE"
#        }
#    },
#    "PONYTAIL": {
#        ...
#    }
# }


# =============================================================================
# UI SETTINGS
# =============================================================================
UI_RATIO = 0.6
UI_RATIO_PROPS = 0.45
