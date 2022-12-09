import time
import logging
import allure

logger = logging.getLogger(__name__)


class TestStartupTime:

    @allure.step
    def test_startup_time_degradation(self, topology_obj, cli_objects):
        """
        Measures time from reboot to the dockers up state.
        Data collected into DB by collect_test_data_to_sql plugin.
        """
        timestamp_before = time.time()
        logger.info(f"Timestamp before reboot is {timestamp_before}")

        logger.info("Rebooting the DUT")
        cli_objects.dut.general.reboot_flow(topology_obj=topology_obj)

        timestamp_after = time.time()
        logger.info(f"Timestamp after reboot {timestamp_after}")

        self.elapsed_time = timestamp_after - timestamp_before
        logger.info(f"Reboot took {self.elapsed_time} seconds")
