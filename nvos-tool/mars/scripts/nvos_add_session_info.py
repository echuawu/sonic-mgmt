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

    def _parse_sonic_version(self, output):
        version = re.compile(r"nvos software version: +([^\s]+)\s", re.IGNORECASE)
        platform = re.compile(r"platform: +([^\s]+)\s", re.IGNORECASE)
        asic = re.compile(r"asic: +([^\s]+)\s", re.IGNORECASE)

        res = {
            "version": version.findall(output)[0] if version.search(output) else "",
            "platform": platform.findall(output)[0] if platform.search(output) else "",
            "asic": asic.findall(output)[0] if asic.search(output) else ""
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
        print("Run NvosAddSessionInfo.get_dynamic_info")
        machines_players = self.conf_obj.get_active_players()
        print("machine_players=" + str(machines_players))

        if isinstance(machines_players, list):
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
        repo_name = self.conf_obj.get_extra_info().get("sonic_mgmt_repo_name")

        cmd = "ansible -m command -i inventory {DUT_NAME}-{TOPOLOGY} -a 'show version'"
        cmd = cmd.format(DUT_NAME=dut_name, TOPOLOGY=topology)
        print("cmd=" + cmd)

        try:
            conn = RemoteRPC(machine)
            conn.import_module("os")
            conn.import_module("mlxlib.common.execute")

            conn.modules.os.chdir(os.path.join(remote_workspace, repo_name, "ansible"))
            conn.modules.os.environ["HOME"] = "/root"

            p = conn.modules.execute.run_process(cmd, shell=True)
            (rc, output) = conn.modules.execute.wait_process(p)
            print("rc=" + str(rc))
            print("output=" + str(output))
            if rc != 0:
                print("Execute command failed!")
                return (1, {})

            return (0, self._parse_sonic_version(output))
