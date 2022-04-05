from ngts.cli_wrappers.interfaces.interface_interface_clis import InterfaceCliInterface


class InterfaceCliCommon(InterfaceCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """

    def __init__(self):
        pass

    @staticmethod
    def config_advertised_speeds(interface, speed_list):
        pass

    @staticmethod
    def config_interface_type(interface, interface_type):
        pass

    @staticmethod
    def config_advertised_interface_types(interface, interface_type_list):
        pass
