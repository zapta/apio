"""Test for the "apio drivers" command."""

import pytest
from tests.conftest import ApioRunner
from apio.utils import apio_platforms
from apio.commands.apio import apio_top_cli as apio

# TODO: add a test for ubuntu
# TODO: add a (dummy) test for windows


def test_drivers_darwin_only(apio_runner: ApioRunner):
    """Tests the 'apio drivers' commands on darwin platform."""

    with apio_runner.in_sandbox() as sb:

        # -- Skip this test if not running on a darwin platform
        if not apio_platforms.get_apio_platform().is_darwin:
            pytest.skip("Darwin only test")

        # -- Run 'apio drivers install ftdi'
        result = sb.invoke_apio_cmd(apio, ["drivers", "install", "ftdi"])
        sb.assert_result_ok(result)
        assert (
            "No driver installation is required on this platform"
            in result.output
        )

        # -- Run 'apio drivers uninstall ftdi'
        result = sb.invoke_apio_cmd(apio, ["drivers", "uninstall", "ftdi"])
        sb.assert_result_ok(result)
        assert (
            "No driver installation is required on this platform"
            in result.output
        )

        # -- Run 'apio drivers install serial'
        result = sb.invoke_apio_cmd(apio, ["drivers", "install", "serial"])
        sb.assert_result_ok(result)
        assert (
            "No driver installation is required on this platform"
            in result.output
        )

        # -- Run 'apio drivers uninstall serial'
        result = sb.invoke_apio_cmd(apio, ["drivers", "uninstall", "serial"])
        sb.assert_result_ok(result)
        assert (
            "No driver installation is required on this platform"
            in result.output
        )


def test_drivers_linux_only(apio_runner: ApioRunner):
    """Tests the 'apio drivers' commands on linux platform."""

    with apio_runner.in_sandbox() as sb:

        # -- Skip this test if not running on a linux platform
        if not apio_platforms.get_apio_platform().is_linux:
            pytest.skip("Ubuntu only test")

        # -- Run 'apio drivers install ftdi'
        result = sb.invoke_apio_cmd(apio, ["drivers", "install", "ftdi"])
        sb.assert_result_ok(result)
        print(result.output)
        assert "xyz" in result.output
        # assert (
        #     "No driver installation is required on this platform"
        #     in result.output
        # )

        # -- Run 'apio drivers uninstall ftdi'
        result = sb.invoke_apio_cmd(apio, ["drivers", "uninstall", "ftdi"])
        sb.assert_result_ok(result)
        print(result.output)
        # assert (
        #     "No driver installation is required on this platform"
        #     in result.output
        # )

        # -- Run 'apio drivers install serial'
        result = sb.invoke_apio_cmd(apio, ["drivers", "install", "serial"])
        sb.assert_result_ok(result)
        print(result.output)
        # assert (
        #     "No driver installation is required on this platform"
        #     in result.output
        # )

        # -- Run 'apio drivers uninstall serial'
        result = sb.invoke_apio_cmd(apio, ["drivers", "uninstall", "serial"])
        sb.assert_result_ok(result)
        print(result.output)
        # assert (
        #     "No driver installation is required on this platform"
        #     in result.output
        # )


# def test_drivers_windows_only(apio_runner: ApioRunner):
#     """Tests the 'apio drivers' commands on a windows platform."""

#     with apio_runner.in_sandbox() as sb:

#         # -- Skip this test if not running on a windows platform
#         if not apio_platforms.get_apio_platform().is_windows:
#             pytest.skip("Windows only test")

#         print("TODO: Implement something testable here")
