import re

from os import listdir

# List all patches in the hw-mgmt directory
for fn in listdir("hw-mgmt"):
    lines = []
    # Skip the series file
    if "series" in fn:
        continue
    # Parse the commit name out of the patch
    with open ("hw-mgmt/{}".format(fn), "r") as f:
        subject = False
        for i, l in enumerate(f.readlines()):
            if subject and l.strip() != "":
                lines[-1] += " " + l.strip()
                continue
            elif subject:
                subject = False
                lines[-1] += "\n"
            if "Subject: " in l:
                subject = True
                l = l.strip()
            # Replace the subject with the filename so the same filename is created during patch gen
            lines.append(re.sub(r"Subject: \[PATCH.*\]", fn.split("-")[0], l))
    with open("hw-mgmt/{}".format(fn), "w") as f:
        for l in lines:
            f.write("{}".format(l))
