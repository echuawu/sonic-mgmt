import time

from infra.tools.connection_tools.linux_ssh_engine import LinuxSshEngine
from ngts.tools.test_utils import allure_utils as allure


class LLDPTool:
    file_path = "/tmp/lldp_packets.txt"
    lldp_proto = '0x88cc'

    @staticmethod
    def start_dump_lldp_packets(engine: LinuxSshEngine, interface=""):
        with allure.step(f"Dump lldp {interface} packets into {LLDPTool.file_path}"):
            engine.run_cmd(f"sudo rm -rf {LLDPTool.file_path}")
            interface_str = f"-i {interface}" if interface else ""
            engine.run_cmd(
                f'sudo tcpdump -Q out -lne {interface_str} -vv ether proto {LLDPTool.lldp_proto} > {LLDPTool.file_path} &')

    @staticmethod
    def finish_dump_lldp_packets(engine: LinuxSshEngine):
        with allure.step(f"Kill tcpdump instances"):
            engine.run_cmd("sudo killall tcpdump")

    @staticmethod
    def get_lldp_frames(engine: LinuxSshEngine, interface="", interval=30):
        LLDPTool.start_dump_lldp_packets(engine, interface)
        time.sleep(interval + 1)
        LLDPTool.finish_dump_lldp_packets(engine)
        with allure.step("Get lldp frames output"):
            output = str(engine.run_cmd(f'cat {LLDPTool.file_path}'))
            return output
