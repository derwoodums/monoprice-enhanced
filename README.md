# Monoprice 6-Zone Amplifier Enhanced

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for Monoprice 6-Zone Amplifiers with enhanced controls including treble, bass, and balance adjustments.

## Features

This integration extends the core Monoprice integration with additional controls:

- **Standard Controls** (via media_player entities)
  - Power on/off
  - Volume control (0-38)
  - Mute/unmute
  - Source selection (1-6)

- **Enhanced Controls** (via number entities)
  - Treble adjustment (0-14, where 7 is flat)
  - Bass adjustment (0-14, where 7 is flat)
  - Balance adjustment (0-20, where 10 is center)

## Supported Hardware

- Monoprice 6-Zone Home Audio Multizone Controller (Model 10761)
- Supports 1-2 daisy-chained amplifiers (up to 12 zones total)
  - Single amp: Zones 11-16
  - Daisy-chained: Zones 11-16 (amp 1) and 21-26 (amp 2)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add this repository URL with category "Integration"
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Download the `monoprice_enhanced` folder from this repository
2. Copy it to your `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Monoprice 6-Zone Amplifier Enhanced"
4. Enter your serial port (e.g., `/dev/ttyUSB0` or socket://192.168.1.100:4999 for IP-to-serial)

## Entities Created

For each detected zone, the integration creates:

| Entity Type | Entity ID Example | Description |
|-------------|-------------------|-------------|
| Media Player | `media_player.monoprice_zone_1` | Main zone control |
| Number | `number.monoprice_zone_1_treble` | Treble control (0-14) |
| Number | `number.monoprice_zone_1_bass` | Bass control (0-14) |
| Number | `number.monoprice_zone_1_balance` | Balance control (0-20) |

## Zone Detection

The integration automatically detects available zones at startup by probing all possible zone addresses (11-16 for amp 1, 21-26 for amp 2). Only zones that respond are created as entities.

**Note:** If you add a second amplifier after initial setup, restart Home Assistant to detect the new zones.

## Services

### `monoprice_enhanced.snapshot`
Save the current state of all zones.

### `monoprice_enhanced.restore`
Restore zones to their previously saved state.

## Example Lovelace Card

For a compact zone control card, check out the companion [Monoprice Zone Card](https://github.com/derwoodums/monoprice-zone-card).

```yaml
type: custom:monoprice-zone-card
name: Living Room
media_player: media_player.monoprice_zone_1
treble: number.monoprice_zone_1_treble
bass: number.monoprice_zone_1_bass
balance: number.monoprice_zone_1_balance
```

## Troubleshooting

### Integration not finding zones
- Verify the serial port is correct
- Check that no other application is using the serial port
- For IP-to-serial adapters, ensure the connection string format is `socket://IP:PORT`

### Zones not responding
- Ensure the amplifier is powered on
- Check serial cable connections
- Try restarting Home Assistant

### Second amplifier not detected
- Restart Home Assistant after connecting a second amplifier
- Verify daisy-chain cable is properly connected

## Credits

This integration uses the [pymonoprice](https://github.com/etsinko/pymonoprice) library.

## License

MIT License - see [LICENSE](LICENSE) file for details.
