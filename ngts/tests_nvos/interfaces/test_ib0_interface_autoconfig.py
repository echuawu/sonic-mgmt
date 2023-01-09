import pytest
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import *

logger = logging.getLogger()


@pytest.mark.ib
@pytest.mark.simx
def test_interface_ib0_autoconfig(engines, topology_obj):
    """
    Verify default autoconf  (disable), check that we can configure possible value (enable).
    and we can unset the configuration

    flow:
    1. Check default values disable - nv show interface <param1> ip
    2. Configure autoconf (enable)
    3. Unset autoconf, check default value
    """

    ipoib_port = MgmtPort('ib0')
    with allure.step('verify the default ib0 autoconf value is {value}'.format(value=IbInterfaceConsts.IB0_IP_AUTOCONF_DEFAULT_VALUE)):
        ip_dict = OutputParsingTool.parse_json_str_to_dictionary(ipoib_port.interface.ip.show()).verify_result()
        Tools.ValidationTool.verify_field_value_in_output(ip_dict, IbInterfaceConsts.AUTOCONFIG, IbInterfaceConsts.IB0_IP_AUTOCONF_DEFAULT_VALUE).verify_result()

    new_value = 'enable'
    with allure.step('Set autoconf = {value} for ib0'.format(value=new_value)):
        ipoib_port.interface.ip.autoconf.set(value=new_value, apply=True, ask_for_confirmation=True)
        ip_dict = OutputParsingTool.parse_json_str_to_dictionary(ipoib_port.interface.ip.show()).verify_result()
        Tools.ValidationTool.verify_field_value_in_output(ip_dict, IbInterfaceConsts.AUTOCONFIG, new_value).verify_result()

    with allure.step('Unset autoconf for ib0'):
        ipoib_port.interface.ip.autoconf.unset(apply=True, ask_for_confirmation=True)
        ip_dict = OutputParsingTool.parse_json_str_to_dictionary(ipoib_port.interface.ip.show()).verify_result()
        Tools.ValidationTool.verify_field_value_in_output(ip_dict, IbInterfaceConsts.AUTOCONFIG, IbInterfaceConsts.IB0_IP_AUTOCONF_DEFAULT_VALUE).verify_result()
