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
    Nov 6, 2019

@author:
    xinw@mellanox.com

@changed:
    on June 4, 2023 by slutati@nvidia.com

@Location:
   /.autodirect/sw_regression/system/SONIC/MARS/bin/cmds/sonic_add_session_info.py

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

BF2_PLATFORM = 'arm64-nvda_bf-mbf2h536c'
BF3_PLATFORM = 'arm64-nvda_bf-9009d3b600cvaa'
BF_PLATFORMS = [BF2_PLATFORM, BF3_PLATFORM]


class SonicAddSessionInfo(SessionAddInfo):
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

    def _parse_sonic_version(self, output, topology):
        version = re.compile(r"sonic software version: +([^\s]+)\s", re.IGNORECASE)
        platform_re = re.compile(r"platform: +([^\s]+)\s", re.IGNORECASE)
        hwsku = re.compile(r"hwsku: +([^\s]+)\s", re.IGNORECASE)
        asic = re.compile(r"asic: +([^\s]+)\s", re.IGNORECASE)
        platform = platform_re.findall(output)[0] if platform_re.search(output) else ""
        if platform in BF_PLATFORMS:
            if platform == BF2_PLATFORM:
                chip_type = 'BF2'
            else:
                chip_type = 'BF3'
        else:
            chip_type = int(str(re.search(r"(\d{4})", platform).group(1))[0]) - 1 if platform else ""
            chip_type = "SPC{}".format(chip_type) if chip_type else ""
        res = {
            "version": version.findall(output)[0] if version.search(output) else "",
            "platform": platform,
            "hwsku": hwsku.findall(output)[0] if hwsku.search(output) else "",
            "asic": asic.findall(output)[0] if asic.search(output) else "",
            "topology": topology,
            "chip_type": chip_type
        }

        return res

    def get_dynamic_info(self):
        """
        Implementation for getting the SONiC info for SONiC regression runs.
        Currently it will get the following:
            1. version
            2. platform
            3. hwsku
            4. asic

        @return:
            Tuple with return code and dictionary of additional info to add.
        """
        print("Run SonicAddSessionInfo.get_dynamic_info")

        machines_players = self.conf_obj.get_active_players()
        print("machine_players={0}".format(str(machines_players)))

        if isinstance(machines_players, list):
            machine = machines_players[0]
        else:
            machine = machines_players
        print("machine={0}".format(str(machine)))

        remote_workspace = '/root/mars/workspace'
        if not remote_workspace:
            logger.error("'sonic_mgmt_workspace' must be defined in extra_info section of setup conf")
            return (1, {})
        print("remote_workspace={0}".format(str(remote_workspace)))

        dut_name = self.conf_obj.get_extra_info().get("dut_name")
        topology = self.conf_obj.get_extra_info().get("topology")
        repo_name = self.conf_obj.get_extra_info().get("sonic_mgmt_repo_name")

        cmd = "ansible -m command -i inventory {DUT_NAME}-{TOPOLOGY} -a 'show version'"
        cmd = cmd.format(DUT_NAME=dut_name, TOPOLOGY=topology)
        print("cmd={0}".format(cmd))

        try:
            conn = RemoteRPC(machine)
            conn.import_module("os")
            conn.import_module("mlxlib.common.execute")

            conn.modules.os.chdir(os.path.join(remote_workspace, repo_name, "ansible"))
            conn.modules.os.environ["HOME"] = "/root"

            p = conn.modules.execute.run_process(cmd, shell=True)
            (rc, output) = conn.modules.execute.wait_process(p)
            print("rc={0}".format(str(rc)))
            print("output={0}".format(str(output)))

            if rc != 0:
                print("Execute command failed!")
                return (1, {})
            res = self._parse_sonic_version(output, topology)
            return (0, res)
        except Exception as e:
            logger.error("Failed to execute command: %s" % cmd)
            logger.error("Exception error: %s" % repr(e))
            return (1, {})
