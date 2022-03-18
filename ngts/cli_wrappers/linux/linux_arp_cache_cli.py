import re
import logging


logger = logging.getLogger()


class LinuxARPCache:

    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def _get_value_from_output(msg):
        re_pattern = re.compile(r"\d*$")
        value = int(re_pattern.search(msg).group(0))
        return value

    def get_gc_thresh(self, ip_ver, thresh_id):
        get_gc_thresh = "sudo sysctl net.ipv{}.neigh.default.gc_thresh{}"
        output = self.engine.run_cmd(get_gc_thresh.format(ip_ver, thresh_id))

        return self._get_value_from_output(output)

    def get_route_gc_interval(self, ip_ver):
        get_route_gc_interval = "sudo sysctl net.ipv{}.route.gc_interval"
        output = self.engine.run_cmd(get_route_gc_interval.format(ip_ver))

        return self._get_value_from_output(output)

    def get_neigh_gc_interval(self, ip_ver):
        get_neigh_gc_interval = "sudo sysctl net.ipv{}.neigh.default.gc_interval"
        output = self.engine.run_cmd(get_neigh_gc_interval.format(ip_ver))

        return self._get_value_from_output(output)

    def set_gc_thresh(self, ip_ver, thresh_id, value):
        set_gc_thresh = "sudo sysctl -w net.ipv{}.neigh.default.gc_thresh{}={}"
        self.engine.run_cmd(set_gc_thresh.format(ip_ver, thresh_id, value))

    def set_route_gc_interval(self, ip_ver, value):
        set_route_gc_interval = "sudo sysctl -w net.ipv{}.route.gc_interval={}"
        self.engine.run_cmd(set_route_gc_interval.format(ip_ver, value))

    def set_neigh_gc_interval(self, ip_ver, value):
        set_neigh_gc_interval = "sudo sysctl -w net.ipv{}.neigh.default.gc_interval={}"
        self.engine.run_cmd(set_neigh_gc_interval.format(ip_ver, value))
