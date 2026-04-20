# wiz-control
Control WiZ smart bulbs from Windows along with f.lux unofficial support

## Features

**f.lux Integration**
- Auto-sync bulbs to f.lux color temperature
- HTTP bridge listens on localhost

**Color Control**
- HSV color picker with live preview
- 5 preset slots for quick recall

**White Temperature**
- 2200K to 6500K range
- 5 preset slots

**Multi-Bulb**
- Control up to 5 bulbs simultaneously
- Per-feature targeting (choose which bulbs respond)
- Individual power controls
- Batch operations (All ON/OFF)

**System Tray**
- Minimizes to tray instead of closing
- Quick access from notification area


# Installation

**Download the installer:**
1. Go to [Releases](../../releases)
2. Download `WizControl_Setup.exe`
3. Run installer
4. Launch from desktop shortcut or Start Menu

**Requirements:**
- Windows 10/11
- Bulbs on same network as PC


# Setup

1. Click `+` to add bulb slots
2. Enter bulb IP addresses (find in WiZ app or router)
3. Use "Status" button to verify connection
4. Select target bulbs using "Send to" dropdown

## f.lux Bridge Setup

1. Open f.lux → Options → Extras
2. Enable "Post to URL when lighting changes"
3. Set URL: `http://localhost:8888` or other ports
4. Press Start in WiZ Control
5. Bulbs now follow f.lux temperature

## Building from Source

See [BUILD_GUIDE.md](BUILD_GUIDE.md)
