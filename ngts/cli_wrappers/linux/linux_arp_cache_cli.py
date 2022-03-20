import re
import logging


logger = logging.getLogger()


class LinuxARPCache:
    @staticmethod
    def _get_value_from_output(msg):
        re_pattern = re.compile(r"\d*$")
        value = int(re_pattern.search(msg).group(0))
        return value

    @staticmethod
    def get_gc_thresh(dut_engine, ip_ver, thresh_id):
        get_gc_thresh = "sudo sysctl net.ipv{}.neigh.default.gc_thresh{}"
        output = dut_engine.run_cmd(get_gc_thresh.format(ip_ver, thresh_id))

        return LinuxARPCache._get_value_from_output(output)

    @staticmethod
    def get_route_gc_interval(dut_engine, ip_ver):
        get_route_gc_interval = "sudo sysctl net.ipv{}.route.gc_interval"
        output = dut_engine.run_cmd(get_route_gc_interval.format(ip_ver))

        return LinuxARPCache._get_value_from_output(output)

    @staticmethod
    def get_neigh_gc_interval(dut_engine, ip_ver):
        get_neigh_gc_interval = "sudo sysctl net.ipv{}.neigh.default.gc_interval"
        output = dut_engine.run_cmd(get_neigh_gc_interval.format(ip_ver))

        return LinuxARPCache._get_value_from_output(output)

    @staticmethod
    def set_gc_thresh(dut_engine, ip_ver, thresh_id, value):
        set_gc_thresh = "sudo sysctl -w net.ipv{}.neigh.default.gc_thresh{}={}"
        dut_engine.run_cmd(set_gc_thresh.format(ip_ver, thresh_id, value))

    @staticmethod
    def set_route_gc_interval(dut_engine, ip_ver, value):
        set_route_gc_interval = "sudo sysctl -w net.ipv{}.route.gc_interval={}"
        dut_engine.run_cmd(set_route_gc_interval.format(ip_ver, value))

    @staticmethod
    def set_neigh_gc_interval(dut_engine, ip_ver, value):
        set_neigh_gc_interval = "sudo sysctl -w net.ipv{}.neigh.default.gc_interval={}"
        dut_engine.run_cmd(set_neigh_gc_interval.format(ip_ver, value))
