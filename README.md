# MitraStar_GPT-2541GNAC_HA
### MitraStar GPT-2541GNAC (Movistar Spain  Router) Component(Device Tracker) for Home Assistant

## Configuration variables:
**host (Required):** The hostname/IP address of the MitraStar Router. <br />
**username (Required):** Username for MitraStar Router. 1234 is the default username <br />
**password (Required):** Password for MitraStar Router. <br />

## Installation:

1. Download and place **mitrastar_gpt2541gnac.py** files in the home-assistant folder like this:
```
 .homeassistant/custom_components/device_tracker/mitrastar_gpt2541gnac.py
```

2. Add the new platform in the **configuration.yaml**:
```
device_tracker:
  - platform: mitrastar_gpt2541gnac
    host: 192.168.1.1
    username: 1234
    password: password
    interval_seconds: 120
    consider_home: 200
    new_device_defaults:
      track_new_devices: False
      hide_if_away: False

```

       
 3. **Restart** the home assistant service.
