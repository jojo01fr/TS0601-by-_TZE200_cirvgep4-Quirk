""" Tuya eMylo YSAF033 temp and humidity sensor with screen. """
# https://www.amazon.fr/dp/B0C243M3PQ
# Based on the .../zhaquirks/tuya/ts0601_sensor.py

from typing import Dict

################## clean this up
import zigpy.types as t
from zigpy.zcl import foundation
from zhaquirks.tuya import TuyaTimePayload, TuyaCommand
import datetime
from typing import Tuple, Optional, Union
##################

from zigpy.profiles import zha
from zigpy.quirks import CustomDevice
from zigpy.zcl.clusters.general import Basic, Groups, Ota, Scenes, Time, AnalogOutput
from zigpy.zcl.clusters.measurement import RelativeHumidity, TemperatureMeasurement

from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
    SKIP_CONFIGURATION,
)
from zhaquirks.tuya import TuyaLocalCluster, TuyaPowerConfigurationCluster2AAA
from zhaquirks.tuya.mcu import DPToAttributeMapping, TuyaDPType, TuyaMCUCluster
#from zhaquirks.tuya.mcu import DPToAttributeMapping, TuyaMCUCluster

TUYA_SET_TIME = 0x24

class TemperatureUnitConvert(t.enum8):
    """Tuya Temp unit convert enum."""

    Celsius = 0x00
    Fahrenheit = 0x01


class TuyaTemperatureMeasurement(TemperatureMeasurement, TuyaLocalCluster):
    """Tuya local TemperatureMeasurement cluster."""

    attributes = TemperatureMeasurement.attributes.copy()
    attributes.update(
        {
            0x8001: ("temp_unit_convert", t.enum8),
            0x8002: ("alarm_max_temperature", t.Single),
            0x8003: ("alarm_min_temperature", t.Single),
            0x8004: ("temperature_sensitivity", t.Single),
        }
    )


class TuyaRelativeHumidity(RelativeHumidity, TuyaLocalCluster):
    """Tuya local RelativeHumidity cluster."""


class TemperatureHumidityManufCluster(TuyaMCUCluster):
    """Tuya Manufacturer Cluster with Temperature and Humidity data points."""
    
    dp_to_attribute: Dict[int, DPToAttributeMapping] = {
        1: DPToAttributeMapping(
            TuyaTemperatureMeasurement.ep_attribute,
            "measured_value",
            dp_type=TuyaDPType.VALUE,
            converter=lambda x: x * 10,  # decidegree to centidegree
        ),
        2: DPToAttributeMapping(
            TuyaRelativeHumidity.ep_attribute,
            "measured_value",
            dp_type=TuyaDPType.VALUE,
            converter=lambda x: x * 100,  # 0.01 to 1.0
        ),
        4: DPToAttributeMapping(
            TuyaPowerConfigurationCluster2AAA.ep_attribute,
            "battery_percentage_remaining",
            dp_type=TuyaDPType.VALUE,
            converter=lambda x: x * 2,  # reported percentage is doubled
        ),
        9: DPToAttributeMapping(
            TuyaTemperatureMeasurement.ep_attribute,
            "temp_unit_convert",
            dp_type=TuyaDPType.ENUM,
            converter=lambda x: TemperatureUnitConvert(x)
        ),
        10: DPToAttributeMapping(
            TuyaTemperatureMeasurement.ep_attribute,
            "alarm_max_temperature",
            dp_type=TuyaDPType.VALUE,
            converter=lambda x: x / 10
        ),
        11: DPToAttributeMapping(
            TuyaTemperatureMeasurement.ep_attribute,
            "alarm_min_temperature",
            dp_type=TuyaDPType.VALUE,
            converter=lambda x: x / 10
        ),
        19: DPToAttributeMapping(
            TuyaTemperatureMeasurement.ep_attribute,
            "temperature_sensitivity",
            dp_type=TuyaDPType.VALUE,
            converter=lambda x: x / 10
        )
    }
    
    set_time_offset = 1970
    set_time_local_offset = 1970

    data_point_handlers = {
        1: "_dp_2_attr_update",
        2: "_dp_2_attr_update",
        4: "_dp_2_attr_update",
        9: "_dp_2_attr_update",
        10: "_dp_2_attr_update",
        11: "_dp_2_attr_update",
        19: "_dp_2_attr_update",
    }

    def handle_set_time_request(self, sequence_number: t.uint16_t) -> foundation.Status:
        payload = TuyaTimePayload()

        utc_now = datetime.datetime.utcnow()
        now = datetime.datetime.now()

        offset_time = datetime.datetime(self.set_time_offset, 1, 1)
        offset_time_local = datetime.datetime(self.set_time_local_offset, 1, 1)
        
        utc_timestamp = int((utc_now - offset_time).total_seconds())
        local_timestamp = int((now - offset_time).total_seconds())
        
        payload.extend(utc_timestamp.to_bytes(4, "big", signed=False))
        payload.extend(local_timestamp.to_bytes(4, "big", signed=False))

        self.create_catching_task(
            self.command(TUYA_SET_TIME, payload, manufacturer=foundation.ZCLHeader.NO_MANUFACTURER_ID, expect_reply=False)
        )

        return foundation.Status.SUCCESS

class eMyloYSAF033TempHumiditySensor_by_jojo01(CustomDevice):
    """Custom device representing tuya temp and humidity sensor with a screen (eMylo YSAF033)."""

    signature = {
        # <SimpleDescriptor endpoint=1, profile=260, device_type=81
        # device_version=1
        # input_clusters=[4, 5, 61184, 0]
        # output_clusters=[25, 10]>
        MODELS_INFO: [
            ("_TZE200_cirvgep4", "TS0601"),
        ],
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.SMART_PLUG, # this is how the device reports itself
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    TemperatureHumidityManufCluster.cluster_id,
                ],
                OUTPUT_CLUSTERS: [Ota.cluster_id, Time.cluster_id],
            }
        },
    }

    replacement = {
        SKIP_CONFIGURATION: True,
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.TEMPERATURE_SENSOR,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    TemperatureHumidityManufCluster,  # Single bus for temp, humidity, and battery
                    TuyaTemperatureMeasurement,
                    TuyaRelativeHumidity,
                    TuyaPowerConfigurationCluster2AAA,
                ],
                OUTPUT_CLUSTERS: [Ota.cluster_id, Time.cluster_id],
            }
        },
    }
