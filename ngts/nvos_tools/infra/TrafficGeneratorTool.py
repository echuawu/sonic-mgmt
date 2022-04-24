import allure
import pytest
import logging
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import InternalNvosConsts
from infra.tools.validations.traffic_validations.ib_traffic.ib_traffic_checker import IBTrafficChecker
from infra.tools.validations.traffic_validations.ip_over_ib_traffic.ip_over_ib_traffic_runner import IPoIBTrafficChecker

logger = logging.getLogger()


class TrafficGeneratorTool:

    @staticmethod
    def send_ib_traffic(players):
        """
        Send ib traffic
        :param players: players fixture
        :return:
        """
        with allure.step("Send ib traffic"):
            logger.info("Sending ib traffic")
            validation_obj = {'type': InternalNvosConsts.IB_TRAFFIC_LAT_TYPE,
                              'sender': 'h1',
                              'send_args': {'interface': InternalNvosConsts.IB_TRAFFIC_SENDER_INTERFACE},
                              'receivers':
                                  [
                                  {'receiver': 'h2', 'receive_args':
                                        {'interface': InternalNvosConsts.IB_TRAFFIC_RECEIVER_INTERFACE}}
                              ]
                              }
            IBTrafficChecker(players, validation_obj).run_validation()

    @staticmethod
    def send_ipoib_traffic(players):
        """
        Send IPoIB traffic
        :param players: players fixture
        :return:
        """
        with allure.step("Send IPoIB traffic"):
            logger.info("Sending IPoIB traffic")
            validation_obj = {'type': InternalNvosConsts.IB_TRAFFIC_IPOIB_TYPE,
                              'sender': 'h1',
                              'send_args': {'interface': InternalNvosConsts.IB_TRAFFIC_SENDER_INTERFACE},
                              'ping_args': {'count': 10},
                              'receivers':
                                  [
                                        {'receiver': 'h2',
                                         'receive_args':
                                             {'interface': InternalNvosConsts.IB_TRAFFIC_RECEIVER_INTERFACE}}
                              ]
                              }
            IPoIBTrafficChecker(players, validation_obj).run_validation()
