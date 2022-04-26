from ngts.tools.infra import update_sys_path_by_community_plugins_path

update_sys_path_by_community_plugins_path()

from plugins.custom_skipif.CustomSkipIf import pytest_runtest_setup  # noqa: E402
