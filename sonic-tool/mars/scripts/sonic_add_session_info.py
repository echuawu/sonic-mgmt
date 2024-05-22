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
import ast
#######################################################################
# Local imports
#######################################################################
from mars_open_community.additional_info.session_add_info import SessionAddInfo
from topology.TopologyAPI import TopologyAPI
from mlxlib.remote.mlxrpc import RemoteRPC
from mlxlib.common import trace

logger = trace.set_logger()

SONIC_SESSION_FACTS_PREFIX = "sonic_session_facts:"


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

    def _parse_dict_string_from_output(self, output):
        """
        The function parses the result from the stdout output of the script
        ngts/scripts/sonic_add_session_info/test_sonic_add_session_info.py
        @param output:
            The output of the script test_sonic_add_session_info.py
        @return:
            A tuple (rc, output) - rc is 0 if the parsing was successful and 1 otherwise. The output is a dictionary
            with the information collected from test_sonic_add_session_info (empty dictionary if failed)
            i.e. {'version': 'SONiC.bluefield.215-4d25a6679_Internal', 'platform': 'arm64-nvda_bf-9009d3b600cvaa',
            'hwsku': 'Nvidia-9009d3b600CVAA-C1', 'asic': 'nvidia-bluefield', 'topology': 'dpu-1',
            'chip_type': 'BF3', 'sonic_branch': 'master'}"
        """
        pattern = r'{}(.*)'.format(SONIC_SESSION_FACTS_PREFIX)
        match = re.search(pattern, output)
        if match:
            dict_string = match.group(1).strip()
            rc = 0
            output = ast.literal_eval(dict_string)  # For MARS API, the value should return as a dictionary
            print(f"output={str(output)}")
        else:
            print("Couldn't get sonic session info")
            rc = 1
            output = {}
        return rc, output

    def get_dynamic_info(self):
        """
        Implementation for getting the SONiC info for SONiC regression runs.
        Currently it will get the following:
            1. version
            2. platform
            3. hwsku
            4. asic
            5. topology
            6. chip_type
            7. branch

        @return:
            Tuple with return code and dictionary of additional info to add.
        """
        print("Run SonicAddSessionInfo.get_dynamic_info")

        machines_players = self.conf_obj.get_active_players()
        print(f"machine_players={str(machines_players)}")

        if isinstance(machines_players, list):
            machine = machines_players[0]
        else:
            machine = machines_players
        print(f"machine={str(machine)}")
        remote_workspace = '/root/mars/workspace'
        if not remote_workspace:
            logger.error("'sonic_mgmt_workspace' must be defined in extra_info section of setup conf")
            return (1, {})
        print(f"remote_workspace={remote_workspace}")

        repo_name = self.conf_obj.get_extra_info().get("sonic_mgmt_repo_name")
        topology = self.conf_obj.get_extra_info().get("topology")
        setup_name = self.conf_obj.get_extra_info().get("setup_name")
        ngts_script_path = "ngts/scripts/sonic_add_session_info/test_sonic_add_session_info.py"
        script_cmd = (f"PYTHONPATH=/devts:{remote_workspace}/{repo_name}/ /ngts_venv/bin/pytest -p "
                  f"no:ngts.tools.conditional_mark -p no:ngts.tools.loganalyzer -p "
                  f"no:ngts.tools.loganalyzer_dynamic_errors_ignore.la_dynamic_errors_ignore --setup_name={setup_name} "
                  f"--sonic-topo={topology} --sonic_session_facts_prefix={SONIC_SESSION_FACTS_PREFIX} --log-level=INFO "
                  f"--clean-alluredir --alluredir=/tmp/allure-results --showlocals {remote_workspace}/{repo_name}/"
                  f"{ngts_script_path}")
        print(f"script_cmd={script_cmd}")
        try:
            conn = RemoteRPC(machine)
            conn.import_module("os")
            conn.import_module("mlxlib.common.execute")

            conn.modules.os.chdir(os.path.join(remote_workspace, repo_name, "ansible"))
            conn.modules.os.environ["HOME"] = "/root"

            p = conn.modules.execute.run_process(script_cmd, shell=True)
            (rc, output) = conn.modules.execute.wait_process(p)
            print(f"rc={str(rc)}")

            if rc != 0:
                print("Execute command failed!")
                return (1, {})
            rc, output = self._parse_dict_string_from_output(output)
        except Exception as e:
            rc = 1
            output = {}
            print(f"An error occurred:{str(e)}")
        finally:
            return (rc, output)
