import logging
import allure
import os.path
import pytest

logger = logging.getLogger()


@pytest.mark.general
def test_adjust_switch_for_community_tests(topology_obj):
    """
    Removes 2 first lines from 'show command' output.

     flow:
     1. Rename existing show script to show.orig
     2. Create and save new show script
    :param topology_obj: topology_obj fixture
    """
    engine = topology_obj.players['dut']['engine']
    with allure.step("Rename original show script to show.orig"):
        path_to_show_cmd = engine.run_cmd("which show")
        path_to_show_cmd_orig = path_to_show_cmd + '.orig'
        # sudo cp /usr/local/bin/show /usr/local/bin/show.orig
        try:
            output = engine.run_cmd("sudo rm {}".format(path_to_show_cmd_orig))
        except Exception:
            logging.warning("Failed to remove show.orig file: " + output)
        engine.run_cmd("sudo cp {origin} {new_name}".format(origin=path_to_show_cmd, new_name=path_to_show_cmd_orig))

    with allure.step("Create new show script"):
        engine.run_cmd("sudo rm {}".format(path_to_show_cmd))
        line_to_write = '{origin_path} $1 $2 $3 | tail -n +3'.format(origin_path=path_to_show_cmd_orig)
        engine.run_cmd("sudo touch {origin_path}".format(origin_path=path_to_show_cmd))
        engine.run_cmd("sudo chmod 777 {origin_path}".format(origin_path=path_to_show_cmd))
        engine.run_cmd("sudo echo \'#!/bin/sh\' >> {file}".format(line=line_to_write, file=path_to_show_cmd))
        engine.run_cmd("sudo echo \'{line}\' >> {file}".format(line=line_to_write, file=path_to_show_cmd))


@pytest.mark.general
def test_restore_origin_setup_after_adjustments_for_community_tests(topology_obj):
    """
    Restore the origin show script

    :param topology_obj: topology_obj fixture
    """
    engine = topology_obj.players['dut']['engine']
    with allure.step("Restore the origin show script"):
        new_show_path = engine.run_cmd("which show")
        origin_show_path = new_show_path + '.orig'
        if "No such file or directory" not in engine.run_cmd("ls {}".format(origin_show_path)):
            engine.run_cmd("sudo rm {}".format(new_show_path))
            engine.run_cmd("sudo cp {origin} {new_name}".format(origin=origin_show_path, new_name=new_show_path))
            engine.run_cmd("sudo rm {}".format(origin_show_path))
