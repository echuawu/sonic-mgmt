import logging
import allure

logger = logging.getLogger()


class HWSimulator:

    @staticmethod
    def simulate_health_issue_change_fw_file(engine, new_val, file):
        cmd = "sudo sed -i 's/.*/{new_val}/' /var/run/hw-management/thermal/{file}".format(new_val=new_val, file=file)
        engine.run_cmd(cmd)

    @staticmethod
    def simulate_fan_fault(engine, fan_id):
        with allure.step("Simulate fan {} fault".format(fan_id)):
            logger.info("Simulate fan {} fault".format(fan_id))
            file = "fan{}_fault".format(fan_id)
            HWSimulator.simulate_health_issue_change_fw_file(engine, 1, file)

    @staticmethod
    def simulate_fix_fan_fault(engine, fan_id):
        with allure.step("Simulate fix fan {} fault".format(fan_id)):
            logger.info("Simulate fix fan {} fault".format(fan_id))
            file = "fan{}_fault".format(fan_id)
            HWSimulator.simulate_health_issue_change_fw_file(engine, 0, file)

    @staticmethod
    def simulate_fan_speed_fault(engine, fan_id):
        with allure.step("Simulate fan {} speed fault".format(fan_id)):
            logger.info("Simulate fan {} speed fault".format(fan_id))
            file = "fan{}_speed_get".format(fan_id)
            speed_value = engine.run_cmd("cat /var/run/hw-management/thermal/{file}".format(file=file))
            HWSimulator.simulate_health_issue_change_fw_file(engine, 1, file)
            HWSimulator.simulate_fan_fault(engine, fan_id)
            return speed_value

    @staticmethod
    def simulate_fix_fan_speed_fault(engine, fan_id, speed_value):
        with allure.step("Simulate fix fan {} speed fault".format(fan_id)):
            logger.info("Simulate fix fan {} speed fault".format(fan_id))
            file = "fan{}_speed_get".format(fan_id)
            HWSimulator.simulate_health_issue_change_fw_file(engine, speed_value, file)
            HWSimulator.simulate_fix_fan_fault(engine, fan_id)

    @staticmethod
    def simulate_psu_fault(engine, psu_id):
        with allure.step("Simulate psu {} fault".format(psu_id)):
            logger.info("Simulate psu {} fault".format(psu_id))
            file = "psu{}_status".format(psu_id)
            HWSimulator.simulate_health_issue_change_fw_file(engine, 0, file)

    @staticmethod
    def simulate_fix_psu_fault(engine, psu_id):
        with allure.step("Simulate psu {} fault".format(psu_id)):
            logger.info("Simulate psu {} fault".format(psu_id))
            file = "psu{}_status".format(psu_id)
            HWSimulator.simulate_health_issue_change_fw_file(engine, 1, file)
