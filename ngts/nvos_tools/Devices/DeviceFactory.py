import logging
from ngts.nvos_tools.Devices.BaseDevice import JaguarSwitch, GorillaSwitch, MarlinSwitch, AnacondaSwitch

logger = logging.getLogger()


class DeviceFactory:
    device_type_dict = \
        {
            'MQM8700 - Jaguar': JaguarSwitch,
            'MQM8700': JaguarSwitch,
            'MQM9700 - Gorilla Blackbird': GorillaSwitch,
            'MQM9700': GorillaSwitch,
            'MQM9520 - marlin': MarlinSwitch,
            'MQM9520': MarlinSwitch,
            'MSN3700': AnacondaSwitch,
            'MSN3700 - Anaconda': AnacondaSwitch
        }

    @staticmethod
    def create_device(device_name):
        try:
            if device_name not in DeviceFactory.device_type_dict.keys():
                device_name = device_name[0:7]
            instance_type = DeviceFactory.device_type_dict[device_name]
            instance = instance_type()
            logger.info('Received switch type {device_name}, created Device instance {instance_type}'.format(device_name=device_name, instance_type=str(instance_type)))
            return instance
        except Exception:
            logger.error("please configure device_name = %s", device_name)
            raise
