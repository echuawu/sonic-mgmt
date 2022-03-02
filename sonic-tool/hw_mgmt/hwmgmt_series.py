import sys

from shutil import copy

# Generate kernel version string from arguments
KVERSION = ".".join(sys.argv[1][1:].split(".")[0:2])

search = True
skip_header = 0

missing = []
integrate = []

# Parse the patch status table to get upstream commit for each patch
with open("hw-mgmt/recipes-kernel/linux/Patch_Status_Table.txt", "r") as f:
    for l in f.readlines():
        if search:
            if "Kernel-{}".format(KVERSION) in l:
                search = False
            continue
        if skip_header < 3:
            skip_header += 1
            continue
        if "-----" in l:
            break

        patch, commit, note, switch, _ = [d.strip() for d in l[1:-1].split("|")]

        if commit == "" and patch.split("-")[0] not in sys.argv[2].split(","):
            missing.append((patch, commit, note, switch))
        else:
            integrate.append((patch, commit))

# Generate a series file with all the patches we want to integrate
with open("linux/hw-mgmt/series", "w") as f:
    for p in integrate:
        print(p[0])
        copy("hw-mgmt/recipes-kernel/linux/linux-{}/{}".format(KVERSION, p[0]), "linux/hw-mgmt/")
        f.write("{}\n".format(p[0]))

# Generate a table we can put in our PR which has all the integrated patches and links to upstream
with open("report", "w") as f:
    f.write("Patch | Upstream|\n")
    f.write("|------------|-----------------------------|\n")
    for p in integrate:
        f.write("|{}| https://github.com/torvalds/linux/commit/{}|\n".format(p[0], p[1]))
    f.write("|------------|-----------------------------|\n")

# Generate a simple report of any patches we choose not to integrate for analysis
with open("missing", "w") as f:
    for p in missing:
        f.write("{}, {}, {}, {}\n".format(p[0],p[1],p[2],p[3]))
