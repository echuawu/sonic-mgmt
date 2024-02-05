from infra.tools.general_constants.constants import DefaultConnectionValues
from ngts.nvos_constants.constants_nvos import MultiPlanarConsts
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import Port
from ngts.nvos_tools.infra.Fae import Fae
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.tools.test_utils import allure_utils as allure
from retry import retry


class MultiPlanarTool:

    @staticmethod
    def override_platform_file(system, engines, new_platform):
        """
        override platform file on switch.
        """
        engine = engines.dut
        player = engines['sonic_mgmt']

        # in case of installing xdr simulation, save the origin file in order to restore at the end of the test
        # if new_platform != MultiPlanarConsts.ORIGIN_FILE:
        #     with allure.step("Save the origin platform.json file"):
        #         engine.copy_file(source_file=MultiPlanarConsts.SIMULATION_FILE,
        #                          dest_file=MultiPlanarConsts.ORIGIN_FULL_PATH,
        #                          file_system=MultiPlanarConsts.PLATFORM_PATH,
        #                          direction='get')

        with allure.step("Override platform.json file"):
            file_path = MultiPlanarConsts.SIMULATION_PATH + new_platform
            player.upload_file_using_scp(dest_username=DefaultConnectionValues.ADMIN,
                                         dest_password=DefaultConnectionValues.DEFAULT_PASSWORD,
                                         dest_folder=MultiPlanarConsts.INTERNAL_PATH,
                                         dest_ip=engine.ip,
                                         local_file_path=file_path)

            engine.run_cmd("sudo mv {}{} {}".format(MultiPlanarConsts.INTERNAL_PATH, new_platform,
                                                    MultiPlanarConsts.PLATFORM_FULL_PATH))

        with allure.step("Remove config_db.json and port_mapping.json files"):
            engine.run_cmd("sudo rm -f /etc/sonic/config_db.json")
            engine.run_cmd("sudo rm -f /etc/sonic/port_mapping.json")

        with allure.step("Perform system reboot"):
            system.reboot.action_reboot(params='force').verify_result()

    @staticmethod
    def select_random_aggregated_port(devices):
        with allure.step("Select a random aggregated port"):
            aggregated_port_name = RandomizationTool.select_random_value(devices.dut.AGGREGATED_PORT_LIST). \
                get_returned_value()
            selected_fae_aggregated_port = Fae(port_name=aggregated_port_name)
            return selected_fae_aggregated_port

    @staticmethod
    def select_random_fnm_port(devices):
        with allure.step("Select a random fnm port"):
            fnm_port_name = RandomizationTool.select_random_value(devices.dut.FNM_PORT_LIST). \
                get_returned_value()
            selected_fae_fnm_port = Fae(port_name=fnm_port_name)
            return selected_fae_fnm_port

    @staticmethod
    def select_random_plane_port(devices, fae_aggregated_port):
        with allure.step("Choose a random plane port (of the aggregated port)"):
            plane_name = RandomizationTool.select_random_value(devices.dut.PLANE_PORT_LIST).get_returned_value()
            plane_port_name = fae_aggregated_port.port.name + plane_name
            selected_fae_plane_port = Fae(port_name=plane_port_name)
            return selected_fae_plane_port

    @staticmethod
    @retry(Exception, tries=4, delay=2)
    def _get_split_ports(port="sw10p1"):
        all_ports = Port.get_list_of_ports()
        split_ports = []
        split_port_names = [port]
        for port_iterator in all_ports:
            if port_iterator.name in split_port_names:
                split_ports.append(port_iterator)
        if not split_ports:
            raise Exception("Didn't find split ports on the system")
        return split_ports

    @staticmethod
    def _get_split_child_ports(parent_port):
        list_of_all_ports = Port.get_list_of_ports()
        child_ports = []
        for port in list_of_all_ports:
            if parent_port.name in port.name and port.name[-2] == 's':
                child_ports.append(port)
        return child_ports
