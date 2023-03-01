import allure
import logging
import pytest
import random
from retry import retry


logger = logging.getLogger()


def test_services_dependency(engines, devices):
    """
    Verifying the NVOS services dependency
    stop one of them and validate the other stop too
    validate they restart after it
    """
    for dependent_services_list in devices.dut.dependent_services:
        chosen_service = random.choice(dependent_services_list)
        try:
            with allure.step("Stop service {}".format(chosen_service)):
                logger.info("Stop service {}".format(chosen_service))
                engines.dut.run_cmd('sudo systemctl stop {}'.format(chosen_service))

            with allure.step("Validate all the relevant services are down"):
                logger.info("Validate all the relevant services are down")
                validate_services_down(engines, dependent_services_list.copy())

        finally:
            with allure.step("Validate all the relevant services are up"):
                logger.info("Validate all the relevant services are up")
                validate_services_up(engines, dependent_services_list)


@retry(Exception, tries=10, delay=2)
def validate_services_down(engines, services_list):
    active_services = []
    inactive_services = []
    for service in services_list:
        cmd_output = engines.dut.run_cmd('sudo systemctl is-active {}'.format(service))
        if 'inactive' not in cmd_output:
            active_services.append(service)
        else:
            inactive_services.append(service)
    if active_services:
        for service in inactive_services:   # so we will not fail when one of them rerun
            services_list.remove(service)
        raise Exception("The next dockers are still up: {}".format(active_services))
    logger.info("All services are down")


@retry(Exception, tries=16, delay=5)
def validate_services_up(engines, services_list):
    inactive_services = []
    for service in services_list:
        cmd_output = engines.dut.run_cmd('sudo systemctl is-active {}'.format(service))
        if 'inactive' in cmd_output:
            inactive_services.append(service)
    if inactive_services:
        raise Exception("The next services are still down: {}".format(inactive_services))
    logger.info("All services are up")


def test_dockers_dependency(engines, devices):
    """
    Verifying the NVOS dockers dependency
    stop one of them and validate the other stop too
    validate they restart after it
    """
    for dependent_dockers_list in devices.dut.dependent_dockers:
        chosen_docker = random.choice(dependent_dockers_list)
        try:
            with allure.step("Kill docker {}".format(chosen_docker)):
                logger.info("Kill docker {}".format(chosen_docker))
                engines.dut.run_cmd('docker kill {}'.format(chosen_docker))

            with allure.step("Validate all the relevant dockers are down"):
                logger.info("Validate all the relevant dockers are down")
                validate_dockers_down(engines, dependent_dockers_list.copy())
        finally:
            with allure.step("Validate all the relevant dockers are up"):
                logger.info("Validate all the relevant dockers are up")
                validate_dockers_up(engines, dependent_dockers_list)


@retry(Exception, tries=10, delay=2)
def validate_dockers_down(engines, dockers_list):
    active_dockers = []
    inactive_dockers = []
    for docker in dockers_list:
        cmd_output = engines.dut.run_cmd('docker ps |grep {}'.format(docker))
        if cmd_output:
            active_dockers.append(docker)
        else:
            inactive_dockers.append(docker)
    if active_dockers:
        for docker in inactive_dockers:     # so we will not fail when one of them rerun
            dockers_list.remove(docker)
        raise Exception("The next dockers are still up: {}".format(active_dockers))
    logger.info("All dockers are down")


@retry(Exception, tries=16, delay=5)
def validate_dockers_up(engines, dockers_list):
    inactive_dockers = []
    for docker in dockers_list:
        cmd_output = engines.dut.run_cmd('docker ps |grep {}'.format(docker))
        if not cmd_output:
            inactive_dockers.append(docker)
    if inactive_dockers:
        raise Exception("The next dockers are still down: {}".format(inactive_dockers))
    logger.info("All dockers are up")
