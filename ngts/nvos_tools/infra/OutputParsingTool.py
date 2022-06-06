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

                if IbInterfaceConsts.LINK not in output_dictionary[port_name].keys():
                    return ResultObj(False, "link field can't be found in the output")
                if IbInterfaceConsts.LINK_STATE not in output_dictionary[port_name]["link"].keys():
                    return ResultObj(False, "state field can't be found in the output")
                if IbInterfaceConsts.TYPE not in output_dictionary[port_name].keys():
                    return ResultObj(False, "type field can't be found in the output")
                if output_dictionary[port_name][IbInterfaceConsts.TYPE] == IbInterfaceConsts.IB_PORT_TYPE and \
                   IbInterfaceConsts.DESCRIPTION not in output_dictionary[port_name].keys():
                    return ResultObj(False, "description field can't be found in the output")

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

                if output_dictionary[port_name][IbInterfaceConsts.TYPE] == IbInterfaceConsts.IB_PORT_TYPE:
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
        with allure.step('Create a dictionary according to provided JSON string'):
            output_dictionary = json.loads(output_json)
            return ResultObj(True, "", output_dictionary)
