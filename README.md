# wiz-control
Control WiZ smart bulbs from Windows locally along with f.lux unofficial support

# Features

## Color Control
- HSV color picker with live preview
- 5 preset slots
<img width="374" height="301" alt="image" src="https://github.com/user-attachments/assets/94d17557-99bc-4b36-8d82-411b3d2b71b5" />


## CCT Temperature
- 2200K to 6500K range
- 5 preset slots
<img width="374" height="278" alt="image" src="https://github.com/user-attachments/assets/99800a7e-64f2-4b9d-8d45-82643153ab25" />


   
## f.lux Integration
- Auto-sync bulbs to f.lux color temperature
- HTTP bridge listens on localhost
<img width="374" height="214" alt="image" src="https://github.com/user-attachments/assets/ea58e556-c2eb-41af-8cfa-d86c36ae3938" />


### Multi-Bulb Connections 
- Control up to 5 bulbs simultaneously
- Per-feature targeting (choose which bulbs respond)
- Individual power controls
- Batch operations (All ON/OFF)


### Run in Background 
- Minimizes to tray instead of closing
- Quick access from notification area
<img width="100" height="49" alt="image" src="https://github.com/user-attachments/assets/dbf31681-0824-4823-92d7-0eda547313c8" />


# Installation

**Download the installer:**
1. Go to [Releases](../../releases)
2. Download `WizControl_Setup.exe`
3. Run installer
4. Launch from desktop shortcut or Start Menu

**Requirements:**
- Windows 10/11
- Bulbs connected to same network as PC

**Note:** This app controls bulbs over your local network, not through WiZ cloud servers. Your bulbs stay on your network.


# Setup Guide

## Getting Bulb IP Addresses

You need to enable local communication and get the IP address for each bulb:

1. Open the WiZ V2 app → Home tab
2. Tap "..." (three dots) in top right → Settings
3. Go to Security in "My room (or whatebvery your room is called)"
4. Enable "Allow local communication"
5. Go back → Clock on Lights → select a bulb
6. Tap the dropdown icon on the right
7. Tap "Device info" → copy the IP address
8. Repeat steps 5-7 for all your bulbs (up to 5)
9. Make sure "Allow local communication" is enabled for all Rooms you want to control

## Configuring WizControl

1. Click `+` to add bulb slots
   <img width="486" height="143" alt="image" src="https://github.com/user-attachments/assets/0aeaaad6-3a6f-406d-b438-49b36d03a8b5" />

2. Enter the IP addresses you copied from the WiZ app
3. Use "Status" button to verify connection
4. Select target bulbs using "Send to" dropdown


## f.lux Bridge Setup

1. Open f.lux → Options and Smart Lighting → Connected Lighting 
    <img width="554" height="362" alt="image" src="https://github.com/user-attachments/assets/a50a3760-d67a-4743-95db-fd9a0f07e7ec" />
2. Set URL: `http://localhost:8888` or other ports
     <img width="494" height="129" alt="image" src="https://github.com/user-attachments/assets/17f41e77-ae93-43fe-abdc-ceef6b183020" />


3. Press Start in WiZ Control
   <img width="374" height="214" alt="image" src="https://github.com/user-attachments/assets/86234c94-0c17-4f0f-8a52-1a01cc1c85a0" />

4. Bulbs now follow f.lux temperature

## Building from Source

See [BUILD_GUIDE.md](BUILD_GUIDE.md)
