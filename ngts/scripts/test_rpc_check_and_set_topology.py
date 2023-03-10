# Builtin libs
import subprocess as sp
import pytest
import logging
import allure
import sys


BRANCH_PTF_MAPPING = {'master': 'latest',
                      '202012': '42007',
                      '202106': '42007'
                      }

logger = logging.getLogger("PreTestCheck")


@pytest.fixture(scope='function')
def current_topo(request):
    """
    Method for get current_topo from pytest arguments
    :param request: pytest buildin
    :return: current_topo, i.e. t1-lag
    """
    return request.config.getoption('--current_topo')


@pytest.fixture(scope='function')
def expected_topo(request):
    """
    Method for get expected_topo from pytest arguments
    :param request: pytest buildin
    :return: expected_topo, i.e. ptf32
    """
    return request.config.getoption('--expected_topo')


def get_sonic_hwsku(duthost):
    return duthost.run_cmd('redis-cli -n 4 hget "DEVICE_METADATA|localhost" hwsku').strip()


def update_device_neighbor_metadata(sonic_dut, dut_cli_object, topo):
    """
    Hack the DEVICE_NEIGHBOR_METADATA table for the ptf32 topo on "Mellanox-SN4600C-C64" to simulate the
    dual tor qos scenario
    :param sonic_dut: dut host engine
    :param dut_cli_object: dut cli object
    :param topo: topology value, expect ptf32 topo
    :param hwsku: dut hwsku
    """
    sonic_dut.disconnect()
    hwsku = get_sonic_hwsku(sonic_dut)
    if topo != "ptf32" or hwsku != "Mellanox-SN4600C-C64":
        return
    neighbors = sonic_dut.run_cmd("redis-cli -n 4 keys DEVICE_NEIGHBOR*").strip("\n").split("\n")
    vm_hwsku = "Arista-VM"
    lo_addr = None
    add_neighbor_metadata_cmd_pattern = 'redis-cli -n 4 hset "DEVICE_NEIGHBOR_METADATA|{}" hwsku {} lo_addr {} mgmt_addr {}  type {}'
    mgmt_addr_patern = "10.75.207.{}"
    for index, neighbor in enumerate(neighbors):
        neighbor_name = sonic_dut.run_cmd('redis-cli -n 4 hget \"{}\" name'.format(neighbor)).strip("\n")
        mgmt_addr = mgmt_addr_patern.format(10 + index)
        if neighbor_name.endswith("T0"):
            router_type = "ToRRouter"
        else:
            router_type = "SpineRouter"
        add_neighbor_metadata_cmd = add_neighbor_metadata_cmd_pattern.format(neighbor_name, vm_hwsku, lo_addr, mgmt_addr, router_type)
        sonic_dut.run_cmd(add_neighbor_metadata_cmd)
    enable_qos_remap_table = 'redis-cli -n 4 hset "SYSTEM_DEFAULTS|tunnel_qos_remap" status enabled'
    sonic_dut.run_cmd(enable_qos_remap_table)
    sonic_dut.run_cmd("sudo config qos reload --no-dynamic-buffer")
    dut_cli_object.general.save_configuration()
    dut_cli_object.general.reload_configuration()
    sonic_dut.run_cmd("sleep 180")


def run_testbed_cli_script(cmd, ansible_path):
    logger.info("Running CMD: {}".format(cmd))
    pipe = sp.Popen(f"cd {ansible_path} && {cmd}", shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    res = pipe.communicate()
    for line in res[0].decode(encoding='utf-8').split('\n'):
        logger.info(line)
    assert not pipe.returncode, "stderr = {0}".format(res[1])


def test_rpc_check_and_set_topology(topology_obj, engines, cli_objects, current_topo, expected_topo):
    ansible_path = "/root/mars/workspace/sonic-mgmt/ansible"
    dut_name = cli_objects.dut.chassis.get_hostname()
    if current_topo == expected_topo:
        sys.exit()

    sonic_branch = topology_obj.players['dut']['branch']
    logger.info('SONiC branch is: {}'.format(sonic_branch))
    ptf_tag = BRANCH_PTF_MAPPING.get(sonic_branch, 'latest')

    with allure.step("Remove topo {}".format(current_topo)):
        cmd = "./testbed-cli.sh -k ceos remove-topo {SWITCH}-{TOPO} vault".format(SWITCH=dut_name, TOPO=current_topo)
        run_testbed_cli_script(cmd, ansible_path)

    with allure.step("Add topology {}".format(expected_topo)):
        cmd = "./testbed-cli.sh -k ceos add-topo {SWITCH}-{TOPO} vault " \
              "-e ptf_imagetag={PTF_TAG}".format(SWITCH=dut_name, TOPO=expected_topo, PTF_TAG=ptf_tag)
        run_testbed_cli_script(cmd, ansible_path)

    with allure.step("Deploy minigraph"):
        cmd = "./testbed-cli.sh deploy-mg {SWITCH}-{TOPO} lab vault".format(SWITCH=dut_name, TOPO=expected_topo)
        run_testbed_cli_script(cmd, ansible_path)

    with allure.step("Post upgrade checks"):
        cmd = "ansible-playbook -i inventory --limit {SWITCH} post_upgrade_check.yml " \
              "-e topo={TOPO} -b -vvv ".format(SWITCH=dut_name, TOPO=expected_topo)
        run_testbed_cli_script(cmd, ansible_path)

    update_device_neighbor_metadata(engines.dut, cli_objects.dut, expected_topo)
