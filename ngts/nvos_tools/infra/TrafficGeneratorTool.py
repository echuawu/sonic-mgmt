import allure
import logging
from ngts.nvos_constants.constants_nvos import NvosConst, SystemConsts
from ngts.nvos_tools.hypervisor.VerifyServerFunctionality import verify_server_is_functional, is_device_up
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import InternalNvosConsts
from ngts.nvos_tools.ib.opensm.OpenSmTool import OpenSmTool
from ngts.nvos_tools.infra.ResultObj import ResultObj
from infra.tools.validations.traffic_validations.ip_over_ib_traffic.ip_over_ib_traffic_runner import IPoIBTrafficChecker
from infra.tools.validations.traffic_validations.ib_traffic.ib_traffic_checker import IBTrafficChecker
from infra.tools.validations.traffic_validations.ib_traffic.ib_traffic_const import IBTrafficConst

logger = logging.getLogger()


class TrafficGeneratorTool:
    @staticmethod
    def send_ib_traffic(players, interfaces, should_success):
        """
        Send ib traffic
        :param interfaces: interfaces fixture
        :param players: players fixture
        :param should_success: True of False
        """
        with allure.step("Generate ib traffic"):
            validation_obj = TrafficGeneratorTool._create_validation_obj(
                interfaces=interfaces,
                traffic_type=InternalNvosConsts.IB_TRAFFIC_LAT_TYPE,
                expected_results=IBTrafficConst.SUCCESS if should_success else IBTrafficConst.FAILURE)

            with allure.step("Send ib traffic"):
                try:
                    logger.info("Sending ib traffic")
                    IBTrafficChecker(players, validation_obj).run_validation()
                    return ResultObj(True, "IB traffic validation ended successfully")
                except BaseException as ex:
                    return ResultObj(False, "IB traffic validation failed - check log for more info.")

    @staticmethod
    def send_ipoib_traffic(players, interfaces, should_success):
        """
        Send IPoIB traffic
        :param interfaces: interfaces fixture
        :param players: players fixture
        :param should_success: True of False
        """
        with allure.step("Generate IPoIB traffic"):
            validation_obj = TrafficGeneratorTool._create_validation_obj(
                interfaces=interfaces,
                traffic_type=InternalNvosConsts.IB_TRAFFIC_IPOIB_TYPE,
                expected_results=IBTrafficConst.SUCCESS if should_success else IBTrafficConst.FAILURE)

            with allure.step("Send IPoIB traffic"):
                try:
                    logger.info("Sending IPoIB traffic")
                    IPoIBTrafficChecker(players, validation_obj).run_validation()
                    return ResultObj(True, "IPoIB traffic validation ended successfully")
                except BaseException as ex:
                    return ResultObj(False, "IPoIB traffic validation failed - " + str(ex))

    @staticmethod
    def _create_validation_obj(interfaces, traffic_type, expected_results):
        with allure.step("Creating validation object in order to generate traffic"):
            logger.info("Creating validation object")
            validation_obj = {'type': traffic_type,
                              'sender': 'ha',
                              'sender_interface': interfaces.ha_dut_1,
                              'receiver': 'hb',
                              'receiver_interface': interfaces.hb_dut_1,
                              'expected_traffic_result': expected_results
                              }
            if traffic_type == InternalNvosConsts.IB_TRAFFIC_IPOIB_TYPE:
                validation_obj['ping_args'] = {'count': 5}

            return validation_obj

    @staticmethod
    def bring_up_traffic_containers(engines, setup_name):
        """
        Bring up traffic containers in case are in down state.
        """
        if hasattr(engines, 'ha') and hasattr(engines, 'hb'):
            with allure.step("Verify traffic server is up"):
                ha_name = engines[NvosConst.HOST_HA_ATTR].noga_query_data['attributes']['Common']['Name']
                server_name = ha_name[:-len(ha_name.split('-')[-1]) - 1]
                verify_server_is_functional(server_name, NvosConst.ROOT_USER, NvosConst.ROOT_PASSWORD)
            with allure.step("Check if traffic containers are already up"):
                ha_ping = is_device_up(engines[NvosConst.HOST_HA].ip)
                hb_ping = is_device_up(engines[NvosConst.HOST_HB].ip)

            if not (ha_ping and hb_ping):
                with allure.step("Run reboot on bring-up containers"):
                    engines.sonic_mgmt.run_cmd(SystemConsts.CONTAINER_BU_TEMPLATE.format(
                        python_path=SystemConsts.PYTHON_PATH, container_bu_script=SystemConsts.CONTAINER_BU_SCRIPT,
                        setup_name=setup_name))

            with allure.step("Verify openSM is running"):
                OpenSmTool.start_open_sm_on_server(engines.dut)
        else:
            logger.info(f'Could not bring-up traffic containers, {NvosConst.HOST_HA} and {NvosConst.HOST_HB} '
                        f'were not found in engines')
