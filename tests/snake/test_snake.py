import allure
import pytest

def test_snake(duthost, configure_switches):

    last_vrf = configure_switches

    with allure.step("Install iperf"):
        duthost.command("sudo apt update")
        duthost.command("sudo apt install -y iperf3")

    with allure.step("Run iperf"):
        duthost.command("sudo ip vrf exec Vrf0 iperf3 -s -B 10.5.0.1", module_async=True)
        time.sleep(5)
        out = duthost.command("sudo ip vrf exec Vrf{} iperf3 -t 60 -i 10 -c 10.5.0.1 --connect-timeout 5000".format(last_vrf))

        # Apply some objective constraints here for now just check success
        assert "Done" in out["stdout"]

