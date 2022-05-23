import logging
from ngts.nvos_tools.Devices.BaseDevice import JaguarSwitch, GorillaSwitch

logger = logging.getLogger()


class DeviceFactory:
    device_type_dict = \
        {
            'MQM8700 - Jaguar': JaguarSwitch,
            'MQM8700': JaguarSwitch,
            'MQM9700 - Gorilla Blackbird': GorillaSwitch,
            'MQM9700': GorillaSwitch,
        }

    @staticmethod
    def create_device(device_name):
        try:
            instance_type = DeviceFactory.device_type_dict[device_name]
            instance = instance_type()
            logger.info('Received switch type {device_name}, created Device instance {instance_type}'.format(device_name=device_name, instance_type=str(instance_type)))
            return instance
        except Exception:
            logger.error("please configure device_name = %s", device_name)
            raise
