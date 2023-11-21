import logging
import json
import allure
from .ResultObj import ResultObj
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import IbInterfaceConsts
logger = logging.getLogger()


class OutputParsingTool:

    @staticmethod
    def parse_show_interface_output_to_dictionary(output_json):
        """
        Creates a dictionary according to provided JSON output of "show interface <name>"
        :param output_json: json output
        :return: a dictionary

                 Example of the input json:

                 {
                    "description": "...",
                    "link": {
                        "logical-state": "Initialized",
                        "physical-state": "LinkUp",
                        "ib-subnet": "infiniband-default",
                        "lanes": "4X",
                        ...
                        "speed": "100G",
                        "ib-speed: "edr",
                        ...
                        "state": {
                            "up": {}
                        },
                        ...
                        "stats": {
                            "in-bytes": 0,
                            ...
                        }
                    }
                    "pluggable": {
                        "cable-length": "2",
                        ...
                        "vendor-sn": "..."
                    }
                    "type": "swp"
                }


                Example of returned dictionary:
                {
                    "description": "...",
                    "link": {
                        "logical-state": "Initialized",
                        "physical-state": "LinkUp",
                        "ib-subnet": "infiniband-default",
                        "lanes": "4X",
                        ...
                        "speed": "100G",
                        "ib-speed: "edr",
                        ...
                        "state": "up"       <------------
                        },
                        ...
                        "stats": {
                            "in-bytes": 0,
                            ...
                        }
                    }
                    "pluggable": {
                        "cable-length": "2",
                        ...
                        "vendor-sn": "..."
                    }
                    "type": "swp"
                }
        """
        with allure.step('Create a dictionary according to provided JSON output of "show interface <name>" command'):
            output_dictionary = json.loads(output_json)

            if IbInterfaceConsts.LINK not in output_dictionary.keys():
                return ResultObj(False, "link field can't be found in the output")

            if IbInterfaceConsts.LINK_STATE not in output_dictionary[IbInterfaceConsts.LINK].keys():
                return ResultObj(False, "state field can't be found in the output")

            output_dictionary[IbInterfaceConsts.LINK][IbInterfaceConsts.LINK_STATE] =\
                list(output_dictionary[IbInterfaceConsts.LINK][IbInterfaceConsts.LINK_STATE].keys())[0]

            return ResultObj(True, "", output_dictionary)

    @staticmethod
    def parse_show_interface_link_output_to_dictionary(output_json):
        """
        Creates a dictionary according to provided JSON output of "show interface <name> link"
            :param output_json: json output
            :return: a dictionary

                     Example of the input json:

                     {
                        "logical-state": "Initialized",
                        "physical-state": "LinkUp",
                        "ib-subnet": "infiniband-default",
                        "lanes": "4X",
                        ...
                        "speed": "100G",
                        "ib-speed: "edr",
                        ...
                        "state": {
                            "up": {}
                        },
                        ...
                        "stats": {
                            "in-bytes": 0,
                            ...
                    }



                    Output:

                    {
                        "logical-state": "Initialized",
                        "physical-state": "LinkUp",
                        "ib-subnet": "infiniband-default",
                        "lanes": "4X",
                        ...
                        "speed": "100G",
                        "ib-speed: "edr",
                        ...
                        "state": "up",
                        ...
                        "stats": {
                            "in-bytes": 0,
                            ...
                        }

        """
        with allure.step('Create a dictionary according to provided JSON output of "show interface link" command'):
            if '2004l' in output_json:
                output_json = ''.join(output_json.split('\n')[1:])

            output_dictionary = json.loads(output_json)

            if IbInterfaceConsts.LINK_STATE not in output_dictionary.keys():
                return ResultObj(False, "state field can't be found in the output")

            output_dictionary[IbInterfaceConsts.LINK_STATE] = \
                list(output_dictionary[IbInterfaceConsts.LINK_STATE].keys())[0]

            return ResultObj(True, "", output_dictionary)

    @staticmethod
    def parse_show_interface_pluggable_output_to_dictionary(output_json):
        """
        Creates a dictionary according to provided JSON output of "show interface <name> pluggalbe"
        :param output_json: json output
        :return: a dictionary

                     Example:

                     {
                        "cable-length": "2",
                        ...
                        "vendor-sn": "..."
                    }

        """
        with allure.step('Create a dictionary according to provided JSON output of "show interface pluggable" command'):
            if '2004l' in output_json:
                output_json = ''.join(output_json.split('\n')[1:])
            output_dictionary = json.loads(output_json)
            return ResultObj(True, "", output_dictionary)

    @staticmethod
    def parse_show_interface_stats_output_to_dictionary(output_json):
        """
        Creates a dictionary according to provided JSON output of "show interface <name> link stats"
        :param output_json: json output
        :return: a dictionary
        """
        with allure.step('Create a dictionary according to provided JSON output of "show interface stats" command'):
            output_dictionary = json.loads(output_json)
            return ResultObj(True, "", output_dictionary)

    @staticmethod
    def parse_show_all_interfaces_output_to_dictionary(output_json):
        """
         Creates a dictionary according to provided JSON output of "show interface"
         :param output_json: json output
         :return: a dictionary

         Example:
         {                                                {
             "port1": {                                     "port1": {
                 "link": {                                      "mtu": 1500
                     "mtu": 1500,                               "speed": "1G"
                     "speed": "1G",    ---------->              "state": "up"
                     "state": {                                 "type": "ib"
                        up": {}                              },
                     }                                       ...
                 },                                        }
                 "type": "ib"
             }
            ...
         }

         """
        with allure.step('Create a dictionary according to provided JSON output of "show interface" command'):
            output_dictionary = json.loads(output_json)
            dictionary_to_return = {}

            for port_name in output_dictionary.keys():

                if IbInterfaceConsts.LINK not in output_dictionary[port_name].keys() or \
                        IbInterfaceConsts.LINK_STATE not in output_dictionary[port_name]["link"].keys() or \
                        IbInterfaceConsts.TYPE not in output_dictionary[port_name].keys():
                    logger.warning(f"'link'/'state'/'type' fields can't be found for port {port_name}")
                    continue

                dictionary_to_return[port_name] = {}

                for link_field in output_dictionary[port_name][IbInterfaceConsts.LINK].keys():

                    if link_field == IbInterfaceConsts.LINK_STATE:
                        tmp_val = list(output_dictionary[port_name][IbInterfaceConsts.LINK][IbInterfaceConsts.LINK_STATE].
                                       keys())[0]
                        dictionary_to_return[port_name][IbInterfaceConsts.LINK_STATE] = tmp_val
                    else:
                        dictionary_to_return[port_name][link_field] = \
                            output_dictionary[port_name][IbInterfaceConsts.LINK][link_field]

                dictionary_to_return[port_name][IbInterfaceConsts.TYPE] = \
                    output_dictionary[port_name][IbInterfaceConsts.TYPE]

                if output_dictionary[port_name][IbInterfaceConsts.TYPE] == IbInterfaceConsts.IB_PORT_TYPE and \
                        IbInterfaceConsts.DESCRIPTION in output_dictionary[port_name].keys():
                    dictionary_to_return[port_name][IbInterfaceConsts.DESCRIPTION] = \
                        output_dictionary[port_name][IbInterfaceConsts.DESCRIPTION]

            return ResultObj(True, "", dictionary_to_return)

    @staticmethod
    def parse_json_str_to_dictionary(output_json):
        """
        Creates a dictionary according to provided JSON string
        :param output_json: json output
        :return: a dictionary
        """
        if isinstance(output_json, dict):
            return ResultObj(True, "", output_json)  # if output is already dict -> do nothing

        if '2004l' in output_json:
            output_json = ''.join(output_json.split('\n')[1:])
        if output_json == '{}' or output_json == '':
            return ResultObj(True, "", {})
        with allure.step('Create a dictionary according to provided JSON string'):
            output_dictionary = json.loads(output_json)
            return ResultObj(True, "", output_dictionary)

    @staticmethod
    def parse_show_system_techsupport_output_to_list(output_json):
        """
        Creates a dictionary according to provided JSON output of "show system tech-support"
            :param output_json: json output
            :return: a list of techsupports files

                     Example of the input json:
                        {
                          "1": {
                            "path": "/var/dump/nvos_dump_jaguar-25_20220619_070154.tar.gz"
                          },
                          "2": {
                            "path": "/var/dump/nvos_dump_jaguar-25_20220619_070725.tar.gz"
                          },
                          "3": {
                            "path": "/var/dump/nvos_dump_jaguar-25_20220619_073216.tar.gz"
                          },
                          "4": {
                            "path": "/var/dump/nvos_dump_jaguar-25_20220619_073506.tar.gz"
                          }
                        }
                    output:
                        ["/var/dump/nvos_dump_jaguar-25_20220619_070154.tar.gz",
                        "/var/dump/nvos_dump_jaguar-25_20220619_070725.tar.gz",
                        "/var/dump/nvos_dump_jaguar-25_20220619_073216.tar.gz",
                        "/var/dump/nvos_dump_jaguar-25_20220619_073506.tar.gz"]
        """
        if output_json == {}:
            return ResultObj(True, "no tech-support files", [])
        paths = json.loads(output_json).values()
        with allure.step('Create a list according to provided JSON string'):
            paths = [list(path.values()) for path in paths]
            output_list = [path for xs in paths for path in xs]
            logger.info(output_list)
            return ResultObj(True, "", output_list)

    @staticmethod
    def parse_config_history(output_json):
        """

        :param output_json: the output after running nv config history --output json
        :return: list of dictionaries
        Example:
        input =
            {
                'rev_8_apply_1':
                    {
                        date': '2023-09-05 10:29:25',
                        'interface': 'CLI',
                        'message': 'Config update by admin',
                        'reason': 'Config update',
                        'rev-id': '8',
                        'user': 'admin'
                    },
                'rev_7_apply_1':
                    {
                        'date': '2023-09-05 10:29:02',
                        'interface': 'CLI',
                        'message': 'Config update by admin',
                        'reason': 'Config update',
                        'rev-id': '7',
                        'user': 'admin'
                    }
            }

        output:
        [
            {
                'ref': 'rev_8_apply_1',
                date': '2023-09-05 10:29:25',
                'interface': 'CLI',
                'message': 'Config update by admin',
                'reason': 'Config update',
                'rev-id': '8',
                'user': 'admin'
            },
            {
                'ref': 'rev_7_apply_1'',
                date': '2023-09-05 10:29:02',
                'interface': 'CLI', 'message':
                'Config update by admin',
                'reason': 'Config update',
                'rev-id': '7',
                'user': 'admin'
            }
        ]
        """
        with allure.step('Create a list of dictionaries according to provided JSON output of "config history" command'):
            if output_json == '' or output_json == []:
                return ResultObj(True, "", [])

            if output_json.startswith("Currently pending"):
                output_json = output_json.split('\n', 1)[1]

            output_dict = json.loads(output_json)
            list_to_return = [{'ref': key, **value} for key, value in output_dict.items()]

        return ResultObj(True, "", list_to_return)

    @staticmethod
    def parse_lslogins_cmd(lslogins_output):
        """

            Example:
            Input:
                    Username:                           admin
                    UID:                                1000
                    Gecos field:                        System Administrator
                    Home directory:                     /home/admin
                    Shell:                              /bin/bash
                    No login:                           no
                    Primary group:                      admin
                    GID:                                1000
                    Supplementary groups:               nvapply,adm,sudo,docker,redis,nvset
                    Supplementary group IDs:            996,4,27,999,1001,997
                    Last login:                         15:32
                    Last terminal:                      pts/2
                    Last hostname:                      10.228.130.172
                    Hushed:                             no
                    Running processes:                  9

                    Last logs:
                    15:01 sudo[202963]: pam_unix(sudo:session): session closed for user root
                    15:03 sshd[202910]: Received disconnect from 10.228.130.172 port 50244:11: disconnected by user
                    15:03 sshd[202910]: Disconnected from user admin 10.228.130.172 port 50244
            Output:
                {
                    Username: admin,
                    UID: 1000
                    Gecos field: System Administrator
                    ...
                    Running processes: 9
                    Last logs: [ ]
        :param lslogins_output:
        :return:
        """
        if 'lslogins: cannot found ' in lslogins_output:
            return ResultObj(True, lslogins_output, lslogins_output)
        result = {}
        lines = lslogins_output.splitlines()
        logs = lines[lines.index('') + 1:]
        lines = lines[:lines.index('')]

        for line in lines:
            splitted_line = line.split(':', 1)
            result[splitted_line[0]] = splitted_line[1].strip()

        result['Last logs'] = logs[1:]
        return ResultObj(True, "", result)

    @staticmethod
    def parse_linux_cmd_output_to_dic(output):
        """
        ****** THE FOLLOWING OUTPUT STR (example from running 'timedatectl' command):
                   Local time: Mon 2023-01-16 18:53:18 IST
               Universal time: Mon 2023-01-16 16:53:18 UTC
                     RTC time: Mon 2023-01-16 16:53:18
                    Time zone: Asia/Jerusalem (IST, +0200)
    System clock synchronized: no
                  NTP service: n/a
              RTC in local TZ: no

        ****** WILL BECOME THE FOLLOWING DICT:
        {
            'Local time': 'Mon 2023-01-16 18:53:18 IST',
            'Universal time': 'Mon 2023-01-16 16:53:18 UTC'
            ...
        }
        """
        dic = {}

        # split string by '\n'
        output_rows = output.split('\n')

        # parse each row to key, val
        for row in output_rows:
            colon_idx = row.find(':')
            k = row[0: colon_idx].strip()
            v = row[colon_idx + 1:].strip()
            dic[k] = v

        return ResultObj(True, "", dic)
