import logging
from ngts.nvos_tools.Devices.IbDevice import GorillaSwitch, \
    MarlinSwitch, GorillaSwitchBF3, CrocodileSwitch, BlackMambaSwitch, CrocodileSimxSwitch
from ngts.nvos_tools.Devices.EthDevice import AnacondaSwitch
from dotted_dict import DottedDict

logger = logging.getLogger()


class DeviceFactory:
    device_type_dict = \
        {
            'MQM9700 - Gorilla Blackbird': GorillaSwitch,
            'MQM9700 - Gorilla BF3': GorillaSwitchBF3,
            'MQM9700': GorillaSwitch,
            'MQM9520 - marlin': MarlinSwitch,
            'MQM9520': MarlinSwitch,
            'MSN3700': AnacondaSwitch,
            'MSN3700 - Anaconda': AnacondaSwitch,
            'QM3400': CrocodileSwitch,
            'QM3400 - Crocodile': CrocodileSwitch,
            'QM3400_simx - Crocodile': CrocodileSimxSwitch,
            'QM8790 - Black Mamba': BlackMambaSwitch
        }

    @staticmethod
    def create_device(device_name):
        try:
            if device_name not in DeviceFactory.device_type_dict.keys():
                device_name = device_name[0:7]
            instance_type = DeviceFactory.device_type_dict[device_name]
            instance = instance_type()
            logger.info('Received switch type {device_name}, created Device instance {instance_type}'.format(
                device_name=device_name, instance_type=str(instance_type)))
            return instance
        except Exception:
            logger.error("please configure device_name = %s", device_name)
            raise

    @staticmethod
    def create_devices_object(topology_obj):
        device_objects = DottedDict()
        dut_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific'][
            'switch_type']
        device_objects.dut = DeviceFactory.create_device(dut_name)
        return device_objects
