import logging
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import InternalNvosConsts
from .ResultObj import ResultObj

logger = logging.getLogger()


class PollingTool:

    @staticmethod
    def wait_for_ports_state(state, ports, timeout=InternalNvosConsts.DEFAULT_TIMEOUT):
        logging.info("Waiting for ports to reach state '{state}' (timeout: {timeout})".format(
                     state=state, timeout=timeout))

        for port in ports:
            port.ib_interface.wait_for_port_state(state, timeout).verify_result()

        return ResultObj(True, "All ports have reached state '{state}'".format(state=state))
