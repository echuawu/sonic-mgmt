import site
import sys
from lib import constants


def extend_sys_path():
    if constants.VER_SDK_PATH not in sys.path:
        site.addsitedir(constants.VER_SDK_PATH)
    for p in constants.EXTRA_PACKAGE_PATH_LIST:
        if p not in sys.path:
            sys.path.append(p)
