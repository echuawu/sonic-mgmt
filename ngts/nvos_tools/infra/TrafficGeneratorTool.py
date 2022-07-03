import allure
import logging
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import InternalNvosConsts
from infra.tools.validations.traffic_validations.ib_traffic.ib_traffic_checker import IBTrafficChecker
from infra.tools.validations.traffic_validations.ip_over_ib_traffic.ip_over_ib_traffic_runner import IPoIBTrafficChecker
from infra.tools.validations.traffic_validations.ib_traffic.ib_traffic_const import IBTrafficConst
from ngts.nvos_tools.infra.ResultObj import ResultObj

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
