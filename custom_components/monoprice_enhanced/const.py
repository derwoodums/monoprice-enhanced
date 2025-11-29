"""Constants for the Monoprice Enhanced integration."""

DOMAIN = "monoprice_enhanced"

CONF_SOURCES = "sources"
CONF_NOT_FIRST_RUN = "not_first_run"

FIRST_RUN = "first_run"
MONOPRICE_OBJECT = "monoprice_object"
UNDO_UPDATE_LISTENER = "undo_update_listener"

SERVICE_SNAPSHOT = "snapshot"
SERVICE_RESTORE = "restore"

# Number entity types
NUMBER_TREBLE = "treble"
NUMBER_BASS = "bass"
NUMBER_BALANCE = "balance"

# Ranges for the controls (from Monoprice protocol)
# Treble/Bass: 0-14, where 7 is flat
TREBLE_MIN = 0
TREBLE_MAX = 14
BASS_MIN = 0
BASS_MAX = 14

# Balance: 0-20, where 10 is center (0=full left, 20=full right)
BALANCE_MIN = 0
BALANCE_MAX = 20

# Zone definitions - supports up to 3 amps daisy-chained
# Amp 1: zones 11-16, Amp 2: zones 21-26, Amp 3: zones 31-36
ZONES = {
    11: "Zone 1",
    12: "Zone 2",
    13: "Zone 3",
    14: "Zone 4",
    15: "Zone 5",
    16: "Zone 6",
    21: "Zone 7",
    22: "Zone 8",
    23: "Zone 9",
    24: "Zone 10",
    25: "Zone 11",
    26: "Zone 12",
}
