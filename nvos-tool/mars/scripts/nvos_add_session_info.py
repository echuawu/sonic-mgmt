"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2001-2017.  ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@date:
    Nov 23, 2022

@author:
    rmahameed@nvidia.com

@changed:

"""
#######################################################################
# Global imports
#######################################################################
import os
import re
import json

#######################################################################
# Local imports
#######################################################################
from mars_open_community.additional_info.session_add_info import SessionAddInfo
from topology.TopologyAPI import TopologyAPI
from mlxlib.remote.mlxrpc import RemoteRPC
from mlxlib.common import trace

logger = trace.set_logger()

SONIC_MGMT_WORKSPACE = '/root/mars/workspace/'


class NvosAddSessionInfo(SessionAddInfo):
    """
    Class to collect session info.
    Contains the conf_obj, extra_info dict if exist and session_info from the
    cmd if exists
    """

    def __init__(self, conf_obj, extra_info=None, session_info=None):
        """
        Constructor
        @param conf_obj:
            The configuration object, can get all the conf information from it.
        @param extra_info:
            Extra info dict from setup conf
        @param session_info:
            Info from the cmd info
        """
        SessionAddInfo.__init__(self, conf_obj, extra_info, session_info)

    def _parse_system_version(self, show_system_output, show_device_output, topology, code_coverage_run, sanitizer_run):
        version = re.compile(r'"product-release": "(.*)"', re.IGNORECASE)
        platform_re = re.compile(r'"platform": "(.*)"', re.IGNORECASE)
        asic = re.compile(r'"type": "(.*)"', re.IGNORECASE)
        res = {
            "version": version.findall(show_system_output)[0] if version.search(show_system_output) else "",
            "platform": platform_re.findall(show_system_output)[0] if platform_re.search(show_system_output) else "",
            "topology": topology,
            "asic": asic.findall(show_device_output)[0] if asic.search(show_device_output) else "",
            "is_code_coverage_run": code_coverage_run,
            "is_sanitizer_run": sanitizer_run,
        }

        return res

    def get_dynamic_info(self):
        """
        Implementation for getting the NVOS info for NVOS regression runs.
        Currently it will get the following:
            1. version
            2. platform
            3. asic

        @return:
            Tuple with return code and dictionary of additional info to add.
        """
        print("Run NVOS AddSessionInfo.get_dynamic_info")

        machines_players = self.conf_obj.get_active_players()
        print("machine_players=" + str(machines_players))

        if type(machines_players) is list:
            machine = machines_players[0]
        else:
            machine = machines_players
        print("machine=" + str(machine))

        remote_workspace = SONIC_MGMT_WORKSPACE
        if not remote_workspace:
            logger.error("'sonic_mgmt_workspace' must be defined in extra_info section of setup conf")
            return (1, {})
        print("remote_workspace=" + str(remote_workspace))

        dut_name = self.conf_obj.get_extra_info().get("dut_name")
        topology = self.conf_obj.get_extra_info().get("topology")
        code_coverage_run = self.conf_obj.get_extra_info().get("code_coverage_run")
        sanitizer_run = self.conf_obj.get_extra_info().get("sanitizer_run")
        repo_name = self.conf_obj.get_extra_info().get("sonic_mgmt_repo_name")

        nvue_sswitch_user = os.getenv("NVU_SWITCH_USER")
        nvue_sswitch_pass = os.getenv("NVU_SWITCH_NEW_PASSWORD")

        cmd_system = "ansible -m command --extra-vars 'ansible_ssh_user={USER} ansible_ssh_pass={PASSWORD}' -i inventory {DUT_NAME}-{TOPOLOGY} -a 'nv show system -o json'"
        cmd_device = "ansible -m command --extra-vars 'ansible_ssh_user={USER} ansible_password={PASSWORD}' -i inventory {DUT_NAME}-{TOPOLOGY} -a 'nv show ib device -o json'"
        cmd_system = cmd_system.format(USER=nvue_sswitch_user, PASSWORD=nvue_sswitch_pass, DUT_NAME=dut_name, TOPOLOGY=topology)
        cmd_device = cmd_device.format(USER=nvue_sswitch_user, PASSWORD=nvue_sswitch_pass, DUT_NAME=dut_name, TOPOLOGY=topology)
        print("cmd=" + cmd_system)
        print("cmd=" + cmd_device)

        try:
            conn = RemoteRPC(machine)
            conn.import_module("os")
            conn.import_module("mlxlib.common.execute")

            conn.modules.os.chdir(os.path.join(remote_workspace, repo_name, "ansible"))
            conn.modules.os.environ["HOME"] = "/root"

            p_system = conn.modules.execute.run_process(cmd_system, shell=True)
            p_device = conn.modules.execute.run_process(cmd_device, shell=True)
            rc_system, system_output = conn.modules.execute.wait_process(p_system)

            rc_device, device_output = conn.modules.execute.wait_process(p_device)
            print("rc_system=" + str(rc_system))
            print("output_system=" + str(system_output))
            print("rc_device=" + str(rc_device))
            print("output_device" + str(device_output))

            if rc_system != 0:
                print("Execute command failed!")
                return 1, {}
            res = self._parse_system_version(system_output, device_output, topology, code_coverage_run, sanitizer_run)
            return 0, res
        except Exception as e:
            logger.error("Failed to execute command: %s" % cmd_system)
            logger.error("Exception error: %s" % repr(e))
            return 1, {}
