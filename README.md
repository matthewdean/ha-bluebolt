# BlueBOLT Power Management for Home Assistant

Home Assistant integration for Panamax/Furman power management devices with [BlueBOLT-CV2](https://s3-us-west-1.amazonaws.com/corebrands-resources/products/BLUEBOLT-CV2/pdf_BlueBOLT-CV2_manual.pdf) network interface cards.

Uses [BlueBOLT Advanced Networking](https://classic.mybluebolt.com/support/Advanced_Networking.php) for local control via XML/UDP port 57010.

## Features

- Power monitoring every 30 seconds (voltage, current, power, temperature)
- Individual control of outlets/outlet banks
- UI-based configuration

## Installation

Copy `custom_components/bluebolt` to your Home Assistant `config/custom_components/` directory and restart.

## Configuration

### Option 1: UI Configuration

Add via **Settings → Devices & Services → Add Integration → BlueBOLT**

Required information:
- **IP Address**: e.g., 192.168.1.50
- **MAC Address**: CV2 card MAC address (12 hex characters), e.g., `1065a3XXXXXX`
- **Name**: Optional friendly name

### Option 2: YAML Configuration

Add to your `configuration.yaml`:

```yaml
bluebolt:
  - host: 192.168.1.50
    mac: "1065a3XXXXXX"
    name: "AV Power Conditioner"
    outlets:
      1: "TV"
      2: "Receiver"
      3: "Amplifier"
      4: "Subwoofer"
      5: "HDMI Matrix"

  - host: 192.168.1.51
    mac: "1065a3XXXXXX"
    name: "UPS"
    outlet_banks:
      1: "Router"
      2: "NAS"
      3: "NVR-1 & NVR-2"
```

**Notes:**
- Device type is auto-detected from CV2
- MAC address should be 12 hex characters
- Custom outlet/bank names are optional (will default to "Outlet 1", "Outlet Bank 1", etc.)
- Use `outlets` for M4315/M4320, `outlet_banks` for F1500/MB1500

## Entities

**M4315-PRO / M4320-PRO:**
- 4 sensors: voltage, current, power, temperature
- 8 switches: individual outlet controls (Outlet 1-8)

**MB1500 / F1500-UPS / F1500-UPS E:**
- 6 sensors: voltage, current, power, output voltage, battery level, load level
- 4 switches: outlet bank controls (Outlet Bank 1-4)

## Supported Devices

**Tested:**
- Panamax M4315-PRO
- Furman F1500-UPS

**Untested (should work):**
- Panamax M4320-PRO
- Panamax MB1500
- Furman F1500-UPS E

## Disclaimer

BlueBOLT and Panamax are trademarks of their respective owners. This is an unofficial integration not affiliated with or endorsed by the trademark holders.

## Repository

https://github.com/matthewdean/ha-bluebolt
