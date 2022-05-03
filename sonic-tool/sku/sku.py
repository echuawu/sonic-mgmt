#!/usr/bin/env python3

"""Mellanox Internal tool to create SKUs for SONiC OS"""

__author__ = "Alexander Allen <arallen@nvidia.com>"

import os
import json
import re

from lxml import etree
from shutil import copy

breakout_map = {1:0, 2:1, 4:3}

# HEADROOM SETTINGS
MGMT_POOL = 256
LOSSY_PG = 19
LOSSY_PG_FACTOR = 1
LOSSLESS_PG_FACTOR = 2
SHARED_HEADROOM_FACTOR = 2
SHARED_HEADROOM_ENABLED = True
EGRESS_MONITORING_HEADROOM = 10
EGRESS_MONITORING = True
MIN_PORT_HEADROOM = 10
IPOOL = MIN_PORT_HEADROOM if SHARED_HEADROOM_ENABLED else 0
EPOOL = 9

# PORT SETTINGS
INCLUDE_FEC = False
VXLAN_SRC_PORT = True

# CABLE LENGTHS
T1_UPLINK_LEN = "2000m"
T1_DOWNLINK_LEN = "40m"
T0_UPLINK_LEN = "40m"
T0_DOWNLINK_LEN = "5m"

# MUST VERIFY THIS INFORMATION BEFORE CREATING NEW SKU
platform_data = {
        "msn4600c": {
            "physical_lanes": 4,
            "sai_lanes": 8,
            "port_count": 64,
            "speed_map": {1:2, 10:16, 40:32, 50:384, 100:1536},
            "mmu_size": 59392
            }
        }


def check_sonic_repo():
    if not os.path.exists("device"):
        print("Not at the root directory of a sonic-buildimage repo. Please run again from the root of a SONiC build folder.")
        exit(-1)

def collect_sku_facts():
    platform = input("Target platform [i.e. MSN4600C]: ")

    sku_folder = os.path.join("device", "mellanox", "x86_64-mlnx_{}-r0".format(platform.lower()))

    if not os.path.exists(sku_folder):
        print("Unable to find platfform {} at {}".format(platform, sku_folder))
        exit(-1)

    skus = filter(lambda x: "Mellanox" in x, os.listdir(sku_folder))

    print("Available SKUs: {}".format(", ".join(skus)))

    target_sku = input("Template SKU [i.e. Mellanox-SN4600C-C64]: ")

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


def define_new_sku(platform):
    port_num = platform_data[platform]["port_count"]
    port_count = 0
    port_data = {}

    while port_count < port_num:
        dat = input("Port Config (i.e. 5 2x50G[25G,10G] D) [{}]".format(port_count))

        cnt = int(dat.split(" ")[0])
        split = int(dat.split(" ")[1].split("x")[0])
        speed = int(dat.split(" ")[1].split("x")[1].split("G")[0])
        mode = "G".join(dat.split(" ")[1].split("x")[1].split("G")[1:])
        direction = "DOWN" if dat.split(" ")[2] == "D" else "UP"

        port_data = {**{i: {"split": split, "speed": speed, "mode": mode, "direction": direction} 
            for i in range(port_count, port_count + cnt)}, **port_data}
        
        port_count += cnt

    return port_data


def generate_port_ini(port_data, platform):
    lane_num = platform_data[platform]["physical_lanes"]
    sai_lanes = platform_data[platform]["sai_lanes"]
    lines = []
    lines += ["# name         lanes              alias     index    speed" + ("     fec" if INCLUDE_FEC else "")]

    for p, d in sorted(port_data.items()):
        for i in range(d["split"]):
            out = ""

            eth = "Ethernet{}".format(p*lane_num + i*int(lane_num / d["split"]))
            lanes = ",".join([str(x) for x in range(p*sai_lanes + i*int(lane_num / d["split"]), p*sai_lanes + (i+1)*int(lane_num / d["split"]))])
            al = "etp{}{}".format(p + 1, chr(i + ord("a")) if d["split"] > 1 else "")
            idx = str(p + 1)
            speed = str(d["speed"]*1000)
            fec = "none" # TODO: Add support here

            out += eth + " "*(15 - len(eth))
            out += lanes + " "*(19 - len(lanes))
            out += al + " "*(10 - len(al))
            out += idx + " "*(9 - len(idx))
            out += speed
            if INCLUDE_FEC: out += " "*(10 - len(speed)) + fec

            lines += [out]

    return "\n".join(lines) + "\n"


def generate_hwsku_json(port_data, platform):
    lane_num = platform_data[platform]["physical_lanes"]
    dat = {"interfaces": {}}

    for p, d in sorted(port_data.items()):
        for i in range(d["split"]):
            eth = "Ethernet{}".format(p*lane_num + i*int(lane_num / d["split"]))
            mode = "{}x{}G{}".format(d["split"], d["speed"], d["mode"])

            dat["interfaces"][eth] = {"default_brkout_mode": mode}

    return json.dumps(dat, indent=4) + "\n"


def generate_sai_xml(port_data, sku_files, platform):

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

        element.find("breakout-modes").text = str(breakout_map[port_data[mod]["split"]])
        element.find("port-speed").text = str(platform_data[platform]["speed_map"][port_data[mod]["speed"]])


    return etree.tostring(root, pretty_print=True)


def get_file_names(port_data, platform):

    counts = {}

    for p, d in port_data.items():
        counts[d["speed"]] = counts.get(d["speed"], 0) + d["split"]

    sai_file = "sai_{}_{}.xml".format(platform.replace("msn",""), "_".join(["{}x{}g".format(c, s) for s, c in counts.items()]))

    sku_string = ("D{}".format(counts[50]) if 50 in counts else "") + ("C{}".format(counts[100]) if 100 in counts else "") + ("S{}".format(counts[10]) if 10 in counts else "")

    sku_name = "Mellanox-{}-{}".format(platform.replace("msn", "SN").upper(), sku_string)

    return sku_name, sai_file


def generate_sai_profile(sku_files, sai_file):
    profile = sku_files["sai.profile"]
    profile = re.sub(r'SAI_VXLAN_SRCPORT_RANGE_ENABLE=.', '', profile)
    if VXLAN_SRC_PORT:
        profile = "SAI_VXLAN_SRCPORT_RANGE_ENABLE=1\n" + profile

    return re.sub(r'sai_.*xml', sai_file, profile)

def get_cable_data(sku_files, speed, length):
    speed_data = sku_files["pg_profile_lookup.ini"]

    for line in speed_data.split("\n"):
        if line[0] == "#":
            continue
        line = re.sub(' +', ' ', line.strip())
        dat = line.split(" ")
        if int(dat[0]) == speed and dat[1] == length:
            return (int(dat[3]) + int(dat[4])) / 1024

def get_headroom_dict(sku_type, sku_files, port_data):
    uplink_len = T0_UPLINK_LEN if sku_type == "t0" else T1_UPLINK_LEN
    downlink_len = T0_DOWNLINK_LEN if sku_type == "t0" else T1_DOWNLINK_LEN
    counts = {}

    for p, d in port_data.items():
        k = "{}_{}".format(d["speed"], d["direction"])
        counts[k] = counts.get(k, 0) + d["split"]

    config_headroom = 0
    open_private_headroom = 0

    for s, c in counts.items():
        speed = int(s.split("_")[0])*1000
        direction = s.split("_")[1]
        length = uplink_len if direction == "UP" else downlink_len
        headroom =  get_cable_data(sku_files, speed, length)

        oper_headroom_size = LOSSY_PG if SHARED_HEADROOM_ENABLED else headroom
        config_headroom += c * headroom * LOSSLESS_PG_FACTOR
        open_private_headroom += c * oper_headroom_size * LOSSLESS_PG_FACTOR

    port_count = sum(counts.values())

    open_private_headroom += port_count*IPOOL
    headroom_pool_size = (config_headroom - open_private_headroom) / SHARED_HEADROOM_FACTOR

    oper_headroom = open_private_headroom + headroom_pool_size
    user_reserved = port_count * (LOSSY_PG*LOSSY_PG_FACTOR + EPOOL)
    system_reserved = port_count * EGRESS_MONITORING_HEADROOM * EGRESS_MONITORING + MGMT_POOL
    mmu_size = platform_data[platform]["mmu_size"]

    ingress_lossless_pool_size = (mmu_size - oper_headroom - user_reserved - system_reserved) * 1024
    egress_lossy_pool_size = ingress_lossless_pool_size
    ingress_lossless_xoff = headroom_pool_size * 1024
    egress_lossless = int(re.search(r"set egress_lossless_pool_size.*'(?P<size>[0-9]*)'", 
        sku_files["buffers_defaults_{}.j2".format(sku_type)]).group("size"))

    return {"ingress_lossless_pool_size": ingress_lossless_pool_size, 
            "ingress_lossless_xoff_size": ingress_lossless_xoff, 
            "egress_lossless_pool_size": egress_lossless, 
            "egress_lossy_pool_size": egress_lossy_pool_size}


def generate_buffer_defaults(sku_type, sku_files, port_data):
    
    buffer_data = sku_files["buffers_defaults_{}.j2".format(sku_type)]

    headroom_data = get_headroom_dict(sku_type, sku_files, port_data)

    for k, v in headroom_data.items():
        buffer_data = re.sub(r"(set {}.*')[0-9]*('.*)".format(k), r"\g<1>{}\g<2>".format(int(v)), buffer_data)

    return buffer_data



# Verify we are operating in a SONiC Repo
check_sonic_repo()

# Get SKU info from user
sku_files, sku_links, platform = collect_sku_facts()

# Get port definitions from user
port_data = define_new_sku(platform)

# Get filenames
sku_name, sai_file = get_file_names(port_data, platform)

# Create sku folder
sku_folder = os.path.join("device", "mellanox", "x86_64-mlnx_{}-r0".format(platform.lower()), sku_name)
os.mkdir(sku_folder)

# Generate files
for fname, data in sku_files.items():
    if fname == "port_config.ini":
        with open(os.path.join(sku_folder, "port_config.ini"), "w") as f:
            f.write(generate_port_ini(port_data, platform))
    elif fname == "hwsku.json":
        with open(os.path.join(sku_folder, "hwsku.json"), "w") as f:
            f.write(generate_hwsku_json(port_data, platform))
    elif "sai_" in fname:
        with open(os.path.join(sku_folder, sai_file), "wb") as f:
            f.write(generate_sai_xml(port_data, sku_files, platform))
    elif fname == "sai.profile":
        with open(os.path.join(sku_folder, "sai.profile"), "w") as f:
            f.write(generate_sai_profile(sku_files, sai_file))
    elif fname == "buffers_defaults_t0.j2":
        with open(os.path.join(sku_folder, "buffers_defaults_t0.j2"), "w") as f:
            f.write(generate_buffer_defaults("t0", sku_files, port_data))
    elif fname == "buffers_defaults_t1.j2":
        with open(os.path.join(sku_folder, "buffers_defaults_t1.j2"), "w") as f:
            f.write(generate_buffer_defaults("t1", sku_files, port_data))
    elif fname in sku_links:
        copy(sku_links[fname], os.path.join(sku_folder, fname), follow_symlinks=False)
    else:
        with open(os.path.join(sku_folder, fname), "w") as f:
            f.write(sku_files[fname])


# Done!
print("SKU Generation Complete at {}".format(sku_folder))



