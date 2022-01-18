import logging
import random
import traceback
import time
import allure
import shlex
import subprocess
import os

from ngts.scripts.reset_fanout.fanout_reset_factory_test import test_fanout_reset_factory
from ngts.constants.constants import MarsConstants

logger = logging.getLogger()


def deploy_fanout_config(onyx_image_url, ansible_path, host_name):
    """
    Method which deploy fanout switch config
    """
    logger.info("Performing reset_factory on fanout switch")
    test_fanout_reset_factory(onyx_image_url=onyx_image_url)

    logger.info("Performing deploy fanout")
    pfcwd_dockers_url = '{}/auto/sw_system_project/sonic/docker/'.format(MarsConstants.HTTTP_SERVER_FIT69)
    with allure.step("Deploy fanout config"):
        cmd = "ansible-playbook -i lab fanout.yml -l {host_name} " \
              "-e pfcwd_dockers_url={pfcwd_dockers_url} -vvv".format(host_name=_remove_mlnx_lab_suffix(host_name),
                                                                     pfcwd_dockers_url=pfcwd_dockers_url)
        logger.info("Running CMD: {}".format(cmd))
        return execute_script(cmd, ansible_path)


def generate_minigraph(ansible_path, dut_name, sonic_topo, port_number):
    """
    Method which doing minigraph generation
    """
    logger.info("Generating minigraph")
    cmd = "./testbed-cli.sh gen-mg {SWITCH}-{TOPO} lab vault".format(SWITCH=dut_name, TOPO=sonic_topo)
    if port_number:
        cmd += " -e port_number={}".format(port_number)
    logger.info("Running CMD: {}".format(cmd))
    retries = initial_count = 3
    sleep_time = 30
    while retries:
        try:
            execute_script(cmd, ansible_path)
            break
        except Exception:
            logger.warning("Failed in Generating minigraph. Trying again. Try number {} ".
                           format(initial_count - retries + 1))
            logger.warning(traceback.print_exc())
            logger.error('Sleep {} seconds after attempt'.format(sleep_time))
            time.sleep(sleep_time)
            retries = retries - 1


def deploy_minigprah(ansible_path, dut_name, sonic_topo, recover_by_reboot):
    """
    Method which doing minigraph deploy on DUT
    """
    cmd = ansible_path + "/ansible-playbook -i inventory --limit {SWITCH}-{TOPO} deploy_minigraph.yml " \
                         "-e dut_minigraph={SWITCH}.{TOPO}.xml -b -vvv".format(SWITCH=dut_name, TOPO=sonic_topo)
    logger.info("Running CMD: {}".format(cmd))
    if recover_by_reboot:
        try:
            logger.info("Deploying minigraph")
            return execute_script(cmd, ansible_path)
        except Exception:
            logger.warning("Failed in Deploying minigraph")
            logger.warning("Performing a reboot and retrying")
            reboot_validation(ansible_path, "reboot", dut_name, sonic_topo)
    logger.info("Deploying minigraph")
    return execute_script(cmd, ansible_path)


def reboot_validation(ansible_path, reboot, dut_name, sonic_topo):
    """
    Method which doing reboot validation
    """
    if reboot == "random":
        reboot_type = random.choice(list(MarsConstants.REBOOT_TYPES.values()))
    else:
        reboot_type = MarsConstants.REBOOT_TYPES[reboot]

    with allure.step("Reboot validation (community setup)"):
        logger.info("Running reboot type: {}".format(reboot_type))
        cmd = "ansible-playbook test_sonic.yml -i inventory --limit {SWITCH}-{TOPO} \
               -e testbed_name={SWITCH}-{TOPO} -e testbed_type={TOPO} \
               -e testcase_name=reboot -e reboot_type={REBOOT_TYPE} -\
               vvv".format(SWITCH=dut_name, TOPO=sonic_topo, REBOOT_TYPE=reboot_type)
        exec_result = execute_script(cmd, ansible_path)
        logger.warning("reboot type: {} failed".format(reboot_type))
        logger.debug("reboot type {} failure results: {}".format(reboot_type, exec_result))
        logger.info("Running reboot type: {} after {} failed".format(MarsConstants.REBOOT_TYPES["reboot"], reboot_type))
        if not exec_result and reboot != MarsConstants.REBOOT_TYPES["reboot"]:
            cmd = "/ansible-playbook test_sonic.yml -i inventory --limit {SWITCH}-{TOPO} \
                  -e testbed_name={SWITCH}-{TOPO} -e testbed_type={TOPO} -e testcase_name=reboot \
                  -e reboot_type={REBOOT_TYPE} -vvv".format(SWITCH=dut_name, TOPO=sonic_topo,
                                                            REBOOT_TYPE=MarsConstants.REBOOT_TYPES["reboot"])
            reboot_res = execute_script(cmd, ansible_path)
            logger.info("reboot type: {} result is {}"
                        .format(MarsConstants.REBOOT_TYPES["reboot"], reboot_res))


def _remove_mlnx_lab_suffix(hostname_string):
    """
    Returns switch hostname without mlnx lab prefix
    :param hostname_string: 'arc-switch1030.mtr.labs.mlnx'
    :return: arc-switch1030
    """
    host_name_index = 0
    return hostname_string.split('.')[host_name_index]


def execute_script(cmd, exec_path):
    logger.info("Executing ansible script")
    p = subprocess.Popen(shlex.split(cmd), cwd=exec_path)
    p.communicate()
    logger.info(p.stdout)
    return p.returncode
