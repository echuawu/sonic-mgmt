from ngts.constants.constants import PlatformTypesConstants


class SupportedRebootReloadTypes:
    def __init__(self, platform=None):
        self.reboot = 'reboot'
        self.fast_reboot = 'fast-reboot'
        self.warm_reboot = 'warm-reboot'
        self.config_reload = 'config reload -y'

        if platform == PlatformTypesConstants.PLATFORM_BOXER:
            del self.fast_reboot


def get_supported_reboot_reload_types_list(platform=None):
    """
    Get list of supported reboot/reload types
    :param platform: platform, example: x86_64-mlnx_msn2010-r0
    :return: list with supported reboot types, example: ['reboot', 'warm-reboot', 'config reload -y']
    """
    supported_reboot_reload_types_list = list(SupportedRebootReloadTypes(platform).__dict__.values())
    return supported_reboot_reload_types_list
