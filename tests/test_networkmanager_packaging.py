"""Regression checks for NetworkManager defaults in live and installed systems."""

import configparser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class NetworkManagerPackagingTests(unittest.TestCase):
    def test_vendor_global_unmanaged_rule_is_shadowed_and_ethernet_is_managed(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        override = configparser.ConfigParser(interpolation=None)
        override.read_string(
            build.split('<<\'NMCONF\'\n', 1)[1].split('\nNMCONF', 1)[0]
        )
        ethernet = configparser.ConfigParser(interpolation=None)
        ethernet.read_string(
            build.split('<<\'NMDEVICE\'\n', 1)[1].split('\nNMDEVICE', 1)[0]
        )

        self.assertIn('/etc/NetworkManager/conf.d/10-globally-managed-devices.conf', build)
        self.assertEqual(override["keyfile"]["unmanaged-devices"], "")
        self.assertEqual(ethernet["device-ifba-managed-ethernet"]["match-device"], "type:ethernet")
        self.assertEqual(ethernet["device-ifba-managed-ethernet"]["managed"], "1")

    def test_dhcp_profile_autoconnects_without_binding_a_specific_interface(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        profile = configparser.ConfigParser(interpolation=None)
        profile.read_string(
            build.split('<<\'NETWORK\'\n', 1)[1].split('\nNETWORK', 1)[0]
        )

        self.assertEqual(profile["connection"]["id"], "IFBA OS Ethernet")
        self.assertEqual(profile["connection"]["type"], "ethernet")
        self.assertEqual(profile["connection"]["autoconnect"], "true")
        self.assertEqual(profile["ipv4"]["method"], "auto")
        self.assertEqual(profile["ipv6"]["method"], "auto")
        self.assertNotIn("interface-name", profile["connection"])
        self.assertIn('chmod 0600 "$ROOTFS/etc/NetworkManager/system-connections/ifba-wired.nmconnection"', build)

    def test_networkmanager_is_the_only_enabled_runtime_backend_and_config_survives_install(self):
        build = (ROOT / "scripts/build-iso-container.sh").read_text()
        installer = (ROOT / "packaging/calamares/unpackfs.conf").read_text()

        self.assertIn('multi-user.target.wants/NetworkManager.service', build)
        self.assertIn('ln -sfn /dev/null "$ROOTFS/etc/systemd/system/systemd-networkd.service"', build)
        self.assertIn('ln -sfn /dev/null "$ROOTFS/etc/systemd/system/systemd-networkd.socket"', build)
        self.assertIn('/etc/NetworkManager/conf.d/20-ifba-managed-ethernet.conf', build)
        self.assertIn('/etc/NetworkManager/conf.d/10-globally-managed-devices.conf', build)
        self.assertIn('/etc/NetworkManager/system-connections/ifba-wired.nmconnection', build)
        self.assertIn('/cdrom/casper/filesystem.squashfs', installer)
        self.assertIn('destination: ""', installer)


if __name__ == "__main__":
    unittest.main()
