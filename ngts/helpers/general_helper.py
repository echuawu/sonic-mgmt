import re
import datetime as dt
from perscache import Cache
from infra.tools.topology_tools.topology_setup_utils import get_all_setups_per_group
from ngts.constants.constants import SonicConst

cache = Cache()


@cache(ttl=dt.timedelta(hours=36))
def get_all_setups():
    all_setups_platforms = get_all_setups_platform()
    all_setups = list(all_setups_platforms.keys())
    return all_setups


@cache(ttl=dt.timedelta(hours=36))
def get_all_setups_platform():
    canonical_setups_platforms = get_all_setups_per_group(SonicConst.SONIC_CANONICAL_NOGA_GROUP)
    filter_canonical_setups(canonical_setups_platforms)
    community_setups_platforms = get_all_setups_per_group(SonicConst.SONIC_COMMUNITY_NOGA_GROUP)
    canonical_setups_platforms.update(community_setups_platforms)
    all_setups_platforms = canonical_setups_platforms
    return all_setups_platforms


def filter_canonical_setups(canonical_setups_platforms):
    keys_to_remove = []
    for setup_name, platform in canonical_setups_platforms.items():
        match = re.search(r"sonic_(\w+)_", setup_name)
        if setup_name.startswith("CI") or not match:
            keys_to_remove.append(setup_name)
        else:
            switch_platform_name = match.group(1)
            if switch_platform_name == "simx":
                keys_to_remove.append(setup_name)
    for key in keys_to_remove:
        canonical_setups_platforms.pop(key)
