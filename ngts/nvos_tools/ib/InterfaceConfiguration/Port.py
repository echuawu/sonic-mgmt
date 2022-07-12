import logging
from .IbInterface import IbInterface
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.ib.InterfaceConfiguration.IbInterfaceDecorators import *
from ngts.cli_wrappers.nvue.nvue_interface_show_clis import OutputFormat
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.cli_wrappers.nvue.nvue_ib_interface_clis import NvueIbInterfaceCli
from ngts.cli_wrappers.openapi.openapi_ib_interface_clis import OpenApiIbInterfaceCli
from ngts.nvos_tools.infra.TrafficGeneratorTool import TrafficGeneratorTool
from ngts.constants.constants_nvos import ApiType
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import IbInterfaceConsts, NvosConsts
import allure

logger = logging.getLogger()


class PortRequirements:
    default_port_requirements = {IbInterfaceConsts.NAME: "",
                                 IbInterfaceConsts.DESCRIPTION: "",
                                 IbInterfaceConsts.LINK_MTU: "",
                                 IbInterfaceConsts.LINK_SPEED: "",
                                 IbInterfaceConsts.LINK_IB_SPEED: "",
                                 IbInterfaceConsts.LINK_STATE: "",
                                 IbInterfaceConsts.LINK_LOGICAL_PORT_STATE: "",
                                 IbInterfaceConsts.LINK_PHYSICAL_PORT_STATE: "",
                                 IbInterfaceConsts.TYPE: ""}
    port_requirements = None

    def __init__(self):
        self.port_requirements = self.default_port_requirements

    def set_port_name(self, name):
        self.port_requirements[IbInterfaceConsts.NAME] = name

    def set_port_description(self, description):
        self.port_requirements[IbInterfaceConsts.DESCRIPTION] = description

    def set_port_speed(self, speed):
        self.port_requirements[IbInterfaceConsts.LINK_SPEED] = speed

    def set_port_ib_speed(self, ib_speed):
        self.port_requirements[IbInterfaceConsts.LINK_IB_SPEED] = ib_speed

    def set_port_state(self, state):
        self.port_requirements[IbInterfaceConsts.LINK_STATE] = state

    def set_port_type(self, req_type):
        self.port_requirements[IbInterfaceConsts.TYPE] = req_type


class Port:
    name = ""
    show_output_dictionary = {}
    name_in_redis = ""
    ib_interface = None
    api_obj = {ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}

    def __init__(self, name, show_output_dictionary, name_in_redis):
        self.name = name
        self.show_output_dictionary = show_output_dictionary
        self.name_in_redis = name_in_redis
        self.ib_interface = IbInterface(self)

    @staticmethod
    def get_list_of_ports_connected_to_traffic_server(players, interfaces, dut_engine=None):
        """
        Return a list of ports which are connected to a traffic server
        """
        if not dut_engine:
            dut_engine = TestToolkit.engines.dut

        with allure.step('Get a list of ports which state is up'):
            port_requirements_object = PortRequirements()
            port_requirements_object.set_port_state(NvosConsts.LINK_STATE_UP)
            port_requirements_object.set_port_type(IbInterfaceConsts.IB_PORT_TYPE)
            up_port_list = Port.get_list_of_ports(None, port_requirements_object)

        with allure.step("Clear selected port counters before sending the traffic"):
            for port in up_port_list:
                port.ib_interface.link.stats.clear_stats(dut_engine)

        with allure.step('Send traffic to identify which ports are connected to a server'):
            TrafficGeneratorTool.send_ib_traffic(players, interfaces, True).verify_result()

        with allure.step('Select only ports connected to a traffic server'):
            traffic_ports = []
            for port in up_port_list:
                in_bytes_counter = port.ib_interface.link.stats.in_bytes.get_operational(dut_engine)
                out_bytes_counter = port.ib_interface.link.stats.out_bytes.get_operational(dut_engine)
                if in_bytes_counter != 0 or out_bytes_counter != 0:
                    traffic_ports.append(port)
            return traffic_ports

    @staticmethod
    def get_list_of_ports(dut_engine=None, port_requirements_object=None):
        """
        Returns a list of port according to port_requirements
        :param dut_engine: ssh dut engine
        :param port_requirements_object: PortRequirements object
        :return: a list of Port objects
        """
        with allure.step('Search for ports that meet provided requirements'):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut

            logging.info("get_list_of_ports - Searching for relevant ports")
            output_dictionary = OutputParsingTool.parse_show_all_interfaces_output_to_dictionary(
                Port.show_interface(dut_engine)).verify_result()

            port_list = []

            if not port_requirements_object or not port_requirements_object.port_requirements:
                logging.info("get_list_of_ports - port_requirements not provided. Selecting all ports.")
                for port_name in output_dictionary.keys():
                    port_list.append(Port(port_name, "", ""))
                return port_list

            for port_name, port_details in output_dictionary.items():
                select_port = True

                for field_name, port_requirements_list in port_requirements_object.port_requirements.items():

                    if field_name == IbInterfaceConsts.NAME and port_requirements_list and \
                       port_requirements_list != port_name:
                        select_port = False
                        break
                    elif port_requirements_list and field_name in port_details.keys() and \
                            port_details[field_name] != port_requirements_list:
                        select_port = False
                        break

                if select_port:
                    port_list.append(Port(port_name, {}, ""))
                    logging.info("get_list_of_ports - {port_name} meets the requirements".format(port_name=port_name))

            return port_list

    def update_output_dictionary(self, dut_engine=None):
        """
        Execute "show" command and create the output dictionary for a specific port
        :param dut_engine: ssh engine
        """
        with allure.step('Execute "show" command and create the output dictionary for {port_name}'.format(
                port_name=self.name)):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut

            logging.info("Updating output dictionary of '{port_name}'".format(port_name=self.name))
            self.show_output_dictionary = OutputParsingTool.parse_show_interface_output_to_dictionary(
                Port.show_interface(dut_engine, self.name)).get_returned_value()

    @staticmethod
    def show_interface(dut_engine=None, port_names="", output_format=OutputFormat.json):
        """
        Executes show interface
        :param output_format: OutputFormat
        :param port_names: ports on which to run show command
        :param dut_engine: ssh engine
        :return: str/json output
        """
        with allure.step('Execute show interface for {port_names}'.format(port_names=port_names)):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut

            logging.info("Executing show interface for {port_names}".format(port_names=port_names))
            return Port.api_obj[TestToolkit.tested_api].show_interface(engine=dut_engine,
                                                                       port_name=port_names,
                                                                       output_format=output_format)
