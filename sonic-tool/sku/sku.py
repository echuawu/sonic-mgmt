#!/usr/bin/env python3

"""
Mellanox Internal tool to create SKUs for SONiC OS

The script must be located in the root of the sonic-buildimage repo before being executed

Brief Summary of Inputs Required:
1) Platform Family. Eg: MSN4700
2) A reference SKU under that platform
3) Breakout info i.e. SKU_BREAKOUT_INFO
4) Platform specific ingo i.e. PLATFORM_DATA
5) Constants related to buffer calculations
6) Topology and Cable Length Information

Note: Buffer Calculations is based on the buffer_spectrum_2.7 ver

A SKU traditionally consists of the following files:

QOS and Buffers Related:
1) pg_profile_lookup.ini
   - The one provided in the Reference SKU is used
   - Script doesn't have capability to calculate this file currently

2) buffer_defaults_{t0,t1,t2}.j2
   - Will be calcuated based on HEADROOM settings, pg_profile_ini, cable lengths and topology info

3) buffers.json.j2
   - Updated based on DEF_TOPO

4) buffers_dynamic.json.
   - Updated based on DEF_TOPO

5) buffers_defaults_objects.j2
   - The symbolic link used in the reference SKU is copied

6) qos.json.j2
   - The symbolic link used in the reference SKU is copied

PORT Related
7) hwsku.json (Not applicable for 202012)
8) sai.profile
9) sai_{}.xml
10) port_config.
    - 7,8,9,10 inferred based on SKU_BREAKOUT_INFO
"""

__author__ = "Alexander Allen <arallen@nvidia.com>, Vivek Reddy <vkarri@nvidia.com>"
__version__ = "1.0.0"

import os
import json
import re, pdb
import sys

from lxml import etree
from shutil import copy, rmtree
from collections import OrderedDict

BREAKOUT_MAP = {1:0, 2:1, 4:3}

# Update this for a new platform
PLATFORM_DATA = {
    "msn4600c": {
            "physical_lanes": 4,
            "sai_lanes": 8,
            "port_count": 64,
            "speed_map": {1:2, 10:16, 40:32, 50:384, 100:1536},
            "mmu_size": 59392
    },
    "msn4700": {
            "physical_lanes": 8,
            "sai_lanes": 8,
            "port_count": 32,
            "speed_map": {1:2, 10:16, 25:100, 40:32, 50:384, 100:1536, 200:4096},
            "mmu_size": 59392
    },
    "msn2700": {
            "physical_lanes": 4,
            "sai_lanes": 4,
            "port_count": 32,
            "speed_map": {10:28700, 25:939524096, 40:98368, 50:3221487616, 100:11534336},
            "mmu_size": 13619
    },
    "msn2740": {
            "physical_lanes": 4,
            "sai_lanes": 4,
            "port_count": 32,
            "speed_map": {10:28700, 25:939524096, 40:98368, 50:3221487616, 100:11534336},
            "mmu_size": 13619
    }
}

SPEED_ALPHA = {10 : "S", 25: "A", 50 : "D", 100 : "C", 200 : "V" }

COPYRIGHT = """\
{#
    Copyright (c) 2022 NVIDIA CORPORATION & AFFILIATES.
    Apache-2.0
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
#}"""

buffer_traditional_j2 = """
{%- set default_topo = 't0' %}
{%- include 'buffers_config.j2' %}
"""

buffer_dynamic_j2 = """
{%- set default_topo = 't0' %}
{%- set dynamic_mode = 'true' %}
{%- include 'buffers_config.j2' %}
"""

buffer_defaults_templ = """
{% set default_cable = '5m' %}
{% set ingress_lossless_pool_size =  '36405216' %}
{% set ingress_lossless_pool_xoff  =  '11567088' %}
{% set egress_lossless_pool_size =  '60817392' %}
{% set egress_lossy_pool_size =  '36405216' %}

{% import 'buffers_defaults_objects.j2' as defs with context %}

{%- macro generate_buffer_pool_and_profiles_with_inactive_ports(port_names_inactive) %}
{{ defs.generate_buffer_pool_and_profiles_with_inactive_ports(port_names_inactive) }}
{%- endmacro %}

{%- macro generate_profile_lists_with_inactive_ports(port_names_active, port_names_inactive) %}
{{ defs.generate_profile_lists(port_names_active, port_names_inactive) }}
{%- endmacro %}

{%- macro generate_queue_buffers_with_inactive_ports(port_names_active, port_names_inactive) %}
{{ defs.generate_queue_buffers(port_names_active, port_names_inactive) }}
{%- endmacro %}

{%- macro generate_pg_profiles_with_inactive_ports(port_names_active, port_names_inactive) %}
{{ defs.generate_pg_profiles(port_names_active, port_names_inactive) }}
{%- endmacro %}
"""

class SKUGenerator():
    SKU = {}
    def __init__(self, input_file):
        with open(input_file) as fd:
            self.SKU = json.load(fd)
        self.check_sonic_repo()

    # Verify we are operating in a SONiC Repo
    def check_sonic_repo(self):
        if not os.path.exists("device"):
            print("Not at the root directory of a sonic-buildimage repo. Please run again from the root of a SONiC build folder.")
            exit(-1)

    def collect_sku_facts(self):
        platform = self.SKU["SKU_BREAKOUT_INFO"]["platform"]
        sku_folder = os.path.join("device", "mellanox", "x86_64-mlnx_{}-r0".format(platform.lower()))

        if not os.path.exists(sku_folder):
            print("Unable to find platform {} at {}".format(platform, sku_folder))
            exit(-1)

        skus = filter(lambda x: "Mellanox" in x or "ACS-MSN" in x, os.listdir(sku_folder))

        print("DBG: Available Reference SKUs: {}".format(", ".join(skus)))

        target_sku = self.SKU["SKU_BREAKOUT_INFO"]["reference_sku"]

        template_folder = os.path.join(sku_folder, target_sku)

        if not os.path.exists(template_folder):
            print("Unable to find SKU {} at {}".format(target_sku, template_folder))
            exit(-1)

        sku_files = {}
        links = {}
        for f in os.listdir(template_folder):
            ap = os.path.join(template_folder, f)
            if os.path.islink(ap):
                links[f] = ap
            with open(ap, "r") as fp:
                sku_files[f] = fp.read()

        return sku_files, links, platform.lower()


    def define_new_sku(self, platform):
        num_port = PLATFORM_DATA[platform]["port_count"]
        port_count = 0
        port_data = {}
        phy_lanes = PLATFORM_DATA[platform]["physical_lanes"]

        for dat in self.SKU["SKU_BREAKOUT_INFO"]["links"]:
            cnt = dat["num_physical"]
            split, mode = dat["def_breakout"].split("x")
            split = int(split)
            speed, tail = mode.split("[")
            speed = int(speed.split("G")[0])
            tail = "[" + tail
            lanes = dat["num_lanes_to_use"]
            if lanes == phy_lanes:
                mode = dat["def_breakout"]
            else:
                mode = str(split) + "x" + str(speed) + "G" + "({})".format(lanes) + tail
            direction = dat["direction"]

            port_data = {**{i: {"split": split, "speed": speed, "mode": mode, "direction": direction, "lanes": lanes}
                for i in range(port_count, port_count + cnt)}, **port_data}

            port_count += cnt

        if port_count != num_port:
            print("ERR: Number of links should sum up to {}, but the info for {} is recieved".format(num_port, port_count))
            exit(-1)

        return port_data


    def generate_port_ini(self, port_data, platform):
        lane_offset = PLATFORM_DATA[platform]["physical_lanes"]
        sai_lanes = PLATFORM_DATA[platform]["sai_lanes"]
        lines = []
        lines += ["# name         lanes              alias     index    speed" + ("     fec" if self.SKU["INCLUDE_FEC"] else "")]

        for p, d in sorted(port_data.items()):
            for i in range(d["split"]):
                out = ""

                lane_seek = int(d["lanes"] / d["split"])
                eth = "Ethernet{}".format(p*lane_offset + i*lane_seek)
                lanes = ",".join([str(x) for x in range(p*sai_lanes + i*lane_seek, p*sai_lanes + (i+1)*lane_seek)])
                al = "etp{}{}".format(p + 1, chr(i + ord("a")) if d["split"] > 1 else "")
                idx = str(p + 1)
                speed = str(d["speed"]*1000)
                fec = "none" # TODO: Add support here

                out += eth + " "*(15 - len(eth))
                out += lanes + " "*(19 - len(lanes))
                out += al + " "*(10 - len(al))
                out += idx + " "*(9 - len(idx))
                out += speed
                if self.SKU["INCLUDE_FEC"]: out += " "*(10 - len(speed)) + fec

                lines += [out]

        return "\n".join(lines) + "\n"


    def generate_hwsku_json(self, port_data, platform):
        lane_num = PLATFORM_DATA[platform]["physical_lanes"]
        dat = {"interfaces": {}}

        for p, d in sorted(port_data.items()):
            for i in range(d["split"]):
                lane_seek = int(d["lanes"] / d["split"])
                eth = "Ethernet{}".format(p*lane_num + i*lane_seek)
                dat["interfaces"][eth] = {"default_brkout_mode": d["mode"]}

        return json.dumps(dat, indent=4) + "\n"


    def generate_sai_xml(self, port_data, sku_files, platform):

        sai_file = next(filter(lambda x: "sai_" in x, sku_files.keys()))

        root = etree.fromstring(sku_files[sai_file])

        for element in root.iter("port-info"):
            mod = int(element.findtext("module"))

            split = port_data[mod]["split"]
            if len(element.findall("split")) > 0:
                element.find("split").text = str(split)
            else:
                splt = etree.SubElement(element, "split")
                splt.text = str(split)

            width = port_data[mod]["lanes"]
            element.find("width").text = str(width)

            element.find("breakout-modes").text = str(BREAKOUT_MAP[port_data[mod]["split"]])
            element.find("port-speed").text = str(PLATFORM_DATA[platform]["speed_map"][port_data[mod]["speed"]])


        return etree.tostring(root, pretty_print=True)


    def get_file_names(self, port_data, platform):

        counts = {}

        for p, d in port_data.items():
            counts[d["speed"]] = counts.get(d["speed"], 0) + d["split"]

        counts = OrderedDict(sorted(counts.items()))

        sai_file = "sai_{}_{}.xml".format(platform.replace("msn",""), "_".join(["{}x{}g".format(c, s) for s, c in counts.items()]))

        # sort according to the speed
        sku_string = ""
        for speed, num in counts.items():
            sku_string = sku_string + SPEED_ALPHA[speed] + str(num)

        sku_name = "Mellanox-{}-{}".format(platform.replace("msn", "SN").upper(), sku_string)

        return sku_name, sai_file


    def generate_sai_profile(self, sku_files, sai_file):
        profile = sku_files["sai.profile"]
        profile = re.sub(r'SAI_VXLAN_SRCPORT_RANGE_ENABLE=.', '', profile)
        if self.SKU["VXLAN_SRC_PORT"]:
            profile = "SAI_VXLAN_SRCPORT_RANGE_ENABLE=1\n" + profile

        return re.sub(r'sai_.*xml', sai_file, profile)

    def get_cable_data(self, sku_files, speed, length):
        speed_data = sku_files["pg_profile_lookup.ini"]
        for line in speed_data.split("\n"):
            if len(line) == 0 or line[0] == "#":
                continue
            line = re.sub(' +', ' ', line.strip())
            dat = line.split(" ")
            if int(dat[0]) == speed and dat[1] == length:
                return (int(dat[3]) + int(dat[4])) / 1024

    def get_headroom_dict(self, sku_type, sku_files, port_data, platform):
        counts = {}

        file = "buffers_defaults_{}.j2".format(sku_type)

        for p, d in port_data.items():
            k = "{}_{}".format(d["speed"], d["direction"])
            counts[k] = counts.get(k, 0) + d["split"]

        config_headroom = 0
        open_private_headroom = 0

        for s, c in counts.items():
            speed = int(s.split("_")[0])*1000
            direction = s.split("_")[1]
            length = self.SKU["CABLE_LENGTH"][sku_type][direction]
            headroom =  self.get_cable_data(sku_files, speed, length)

            oper_headroom_size = self.SKU["LOSSY_PG_MIN_HEADROOM"] if self.SKU["SHARED_HEADROOM_ENABLED"] else headroom
            config_headroom += c * headroom * self.SKU["LOSSLESS_PG_FACTOR"][direction]
            open_private_headroom += c * oper_headroom_size * self.SKU["LOSSLESS_PG_FACTOR"][direction]
            print(c, speed, direction, length, headroom, self.SKU["LOSSLESS_PG_FACTOR"][direction], oper_headroom_size, config_headroom, open_private_headroom)

        # print("Final config_headroom: {}, open_private_headroom: {}".format(config_headroom, open_private_headroom))
        port_count = sum(counts.values())

        IPOOL = self.SKU["MIN_PORT_HEADROOM"] if self.SKU["SHARED_HEADROOM_ENABLED"] else 0
        open_private_headroom += port_count*IPOOL
        headroom_pool_size = (config_headroom - open_private_headroom) / self.SKU["SHARED_HEADROOM_FACTOR"]
        oper_headroom = open_private_headroom + headroom_pool_size
        user_reserved = port_count * (self.SKU["LOSSY_PG_MIN_HEADROOM"]*self.SKU["LOSSY_PG_FACTOR"] + self.SKU["EPOOL"])
        system_reserved = port_count * (self.SKU["MGMT_PG_HEADROOM"] + self.SKU["EGRESS_MIRRORING_HEADROOM"]) + self.SKU["MGMT_POOL"]
        mmu_size = PLATFORM_DATA[platform]["mmu_size"]

        ingress_lossless_pool_size = (mmu_size - oper_headroom - user_reserved - system_reserved) * 1024
        egress_lossy_pool_size = ingress_lossless_pool_size
        ingress_lossless_xoff = headroom_pool_size * 1024
        if file in sku_files:
            egress_lossless = int(re.search(r"set egress_lossless_pool_size.*'(?P<size>[0-9]*)'",  sku_files[file]).group("size"))
        else:
            egress_lossless = mmu_size * 1024

        pool_sizes = {"ingress_lossless_pool_size": ingress_lossless_pool_size,
                "ingress_lossless_pool_xoff": ingress_lossless_xoff, 
                "egress_lossless_pool_size": egress_lossless, 
                "egress_lossy_pool_size": egress_lossy_pool_size}

        # print("Pool Size for topo: {}, {}".format(sku_type, pool_sizes))

        return pool_sizes


    def generate_buffer_defaults(self, sku_type, sku_files, port_data, platform):

        print("\n")
        print("Generating buffers_defaults_{}.j2 ".format(sku_type))

        file = "buffers_defaults_{}.j2".format(sku_type)

        buffer_data = COPYRIGHT + buffer_defaults_templ

        headroom_data = self.get_headroom_dict(sku_type, sku_files, port_data, platform)

        for k, v in headroom_data.items():
            buffer_data = re.sub(r"(set {}.*')[0-9]*('.*)".format(k), r"\g<1>{}\g<2>".format(int(v)), buffer_data)

        def_len = self.SKU["CABLE_LENGTH"][sku_type]["default_cable"]

        buffer_data = re.sub(r"(set default_cable.*')[0-9]*m('.*)", r"\g<1>{}\g<2>".format(def_len), buffer_data)

        return buffer_data

    def generate_buffer_json(self, sku_files, fname):
        if "dynamic" in fname:
            text = COPYRIGHT + buffer_dynamic_j2
        else:
            text = COPYRIGHT + buffer_traditional_j2
        return re.sub(r"(set default_topo.*').*('.*)", r"\g<1>{}\g<2>".format(self.SKU["DEF_TOPO"]), text)

    def generateSKU(self):
        # Get SKU info from user
        sku_files, sku_links, platform = self.collect_sku_facts()

        # Get port definitions from user
        port_data = self.define_new_sku(platform)

        # Get filenames
        sku_name, sai_file = self.get_file_names(port_data, platform)

        # Create sku folder
        sku_folder = os.path.join("device", "mellanox", "x86_64-mlnx_{}-r0".format(platform.lower()), sku_name)

        # Remove if the folder already exists
        if os.path.exists(sku_folder):
            rmtree(sku_folder)

        os.mkdir(sku_folder)

        print(sku_links.keys())

        # Generate files
        if self.SKU.get("IMAGE_BRANCH", "master") != "202012":
            with open(os.path.join(sku_folder, "hwsku.json"), "w") as f:
                f.write(self.generate_hwsku_json(port_data, platform))

        with open(os.path.join(sku_folder, "port_config.ini"), "w") as f:
            f.write(self.generate_port_ini(port_data, platform))

        with open(os.path.join(sku_folder, "sai.profile"), "w") as f:
            f.write(self.generate_sai_profile(sku_files, sai_file))

        with open(os.path.join(sku_folder, sai_file), "wb") as f:
            f.write(self.generate_sai_xml(port_data, sku_files, platform))

        with open(os.path.join(sku_folder, "buffers_defaults_t0.j2"), "w") as f:
            f.write(self.generate_buffer_defaults("t0", sku_files, port_data, platform))

        with open(os.path.join(sku_folder, "buffers_defaults_t1.j2"), "w") as f:
            f.write(self.generate_buffer_defaults("t1", sku_files, port_data, platform))

        if self.SKU.get("T2_TOPO", False):
            with open(os.path.join(sku_folder, "buffers_defaults_t2.j2"), "w") as f:
                f.write(self.generate_buffer_defaults("t2", sku_files, port_data, platform))

        for fname in ["buffers_defaults_objects.j2", "qos.json.j2", ]:
            copy(sku_links[fname], os.path.join(sku_folder, fname), follow_symlinks=False)

        with open(os.path.join(sku_folder, "pg_profile_lookup.ini"), "w") as f:
            f.write(sku_files["pg_profile_lookup.ini"])

        for fname in ["buffers.json.j2", "buffers_dynamic.json.j2"]:
            with open(os.path.join(sku_folder, fname), "w") as f:
                f.write(self.generate_buffer_json(sku_files, fname))

        # # Done!
        print("SKU Generation Complete at {}".format(sku_folder))

def main():
    if len(sys.argv) != 2:
        print("Please pass input file as argument")
        exit(1)

    input_file = sys.argv[1]
    sku_generator = SKUGenerator(input_file)
    sku_generator.generateSKU()


if __name__ == '__main__':
    main()
