import sys

from os import listdir

SONIC_SERIES = "sonic-linux-kernel/patch/series"
LINUX_SERIES = "linux/sonic/series"

lines = []
skip = False

exportpath = LINUX_SERIES

# Iterate the lines in the sonic-linux-kernel patch series file
with open(SONIC_SERIES) as f:
    for l in f.readlines():
        if not skip:
            lines.append(l)

        # Locate the mellanox section
        if "# Mellanox" in l:
            # If we are exporting our newly generated patches add the lines otherwise cut off everything below
            if len(sys.argv) > 1 and sys.argv[1] == "export":
                exportpath = SONIC_SERIES
                lines += ["{}\n".format(p) for p in sorted(listdir("linux/patch/"))]
                lines += ["\n"]
                skip = True
            else:
                break

        if skip and l == "\n":
            skip = False

# Export the SONiC patches that need to be imported prior to Mellanox ones
with open(exportpath, "w") as f:
    for l in lines:
        f.write("{}".format(l))
