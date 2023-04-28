import allure
import pytest

from ngts.helpers.config_db_utils import save_config_db_json
from ngts.helpers.run_process_on_host import run_process_on_host
from ngts.constants.constants import BluefieldConstants


@pytest.mark.disable_loganalyzer
def test_change_hwsku(request, cli_objects, engines):
    """
    This test will change HwSKU
    Test used for DPU devices - when we run DASH ACL test case(which require specific HwSKU).
    Test doing HwSKU change before DASH ACL test and after test case(revert back original HwSKU).
    :param request: pytest build-in fixture
    :param cli_objects: cli_objects fixture
    :param engines: engines fixture
    """

    config_db = cli_objects.dut.general.get_config_db()
    current_hwsku = config_db['DEVICE_METADATA']['localhost']['hwsku']

    with allure.step('Changing HwSKU'):
        if current_hwsku.endswith('-C2'):
            config_db['DEVICE_METADATA']['localhost']['hwsku'] = current_hwsku.replace('-C2', '')
        else:
            config_db['DEVICE_METADATA']['localhost']['hwsku'] = f'{current_hwsku}-C2'

        save_config_db_json(engines.dut, config_db)
        cli_objects.dut.general.reload_flow(ports_list=BluefieldConstants.BLUEFIELD_PORTS_LIST, reload_force=True)

    with allure.step('Removing running_golden_config.json file'):
        engines.dut.run_cmd('sudo rm -f /etc/sonic/running_golden_config.json')

    with allure.step('Removing cache files'):
        sonic_mgmt_path = request.fspath.dirname.split('ngts/scripts')[0]
        run_process_on_host(cmd=f'sudo rm -rf {sonic_mgmt_path}_cache')
