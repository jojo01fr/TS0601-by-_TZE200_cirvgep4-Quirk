# TS0601-by-_TZE200_cirvgep4-Quirk
Working quirk for the eMylo Temperature and Humidity sensor with clock


To install it you need to edit Home Assistant configuration.yaml and add the following (adapt folder path on your custom install, mine is on a Synology SynoCommunity package 2023.1.7-20):

# ZHA integration has been previously installed
zha:
  database_path: /volume1/@appdata/homeassistant/config/zigbee.db
  enable_quirks: true
  custom_quirks_path: /volume1/@appdata/homeassistant/config/custom_zha_quirks/

Then put this file ts0601_sensor.py on that folder /config/custom_zha_quirks/ 
If the device was already integrated on HA, you need to 
  1. Remove it from ZHA integration, 
  2. Delete the folder /config/custom_zha_quirks/__pycache__, 
  3. Restart Home Assistant (HA)
  4. Add device again on ZHA Integration
  5. Check on device info if it loaded Quirk: ts0601_sensor.eMyloYSAF033TempHumiditySensor_by_jojo01
  6. Wait a few minutes, device will take actual time and give temp and humidity. Battery sensor still not working yet.

Enjoy ! :)
