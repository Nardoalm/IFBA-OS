# IFBA OS installer status

## Candidate implementation — 2026-11-20

The current source adds Calamares to the Ubuntu 26.04 (`resolute`) live-image build for both `amd64` and `arm64`. Ubuntu publishes Calamares 3.3.14 and its common settings for both target architectures. The upstream Calamares GitHub repository is archived, so this integration uses Ubuntu's package and a small project-owned configuration instead of depending on upstream settings. The installer is an **experimental candidate**, not a supported installation path.

The live desktop entry and desktop shortcut open a UEFI-only launcher. It explains that disposable-disk installation, reboot, and login have not been validated, and asks the user to continue only in a VM with a disposable virtual disk. Calamares is started through `pkexec`. The installer UI begins with no partition choice selected, shows partition labels, retains manual partitioning, requires 25 GiB of storage, uses ext4 by default, and asks for confirmation immediately before writing. The configuration recommends a 512 MiB EFI System Partition, permits an existing 300 MiB EFI partition, and uses `/boot/efi`. Run the live media in UEFI mode; the project has not validated legacy BIOS installation.

The install sequence copies the live SquashFS, which now retains the target kernel and initramfs under `/boot` as well as the separate live boot files. It removes the passwordless live `ubuntu` account and its home, removes the SDDM live autologin and Casper sudoers configuration, and purges Casper from the target before initramfs generation. It removes the live installer menu entries from the target while leaving Calamares modules installed until the running installer has finished. It then creates the user's account and configures SDDM, locale, keyboard, initramfs, and GRUB. The installer user page defaults to no autologin, disables a separate root password, requests a password of at least eight characters, and places the account in Ubuntu's `sudo` group. Locale selection is available in Calamares; the live locale and keyboard guess use pt-BR, and the timezone starts at `America/Bahia`. The user's account name cannot be `ubuntu`.

The build installs architecture-matched signed UEFI GRUB and shim packages into the copied system. Calamares is configured with Ubuntu's GRUB EFI entry ID, EFI fallback installation, and `/boot/efi`. EFI package availability was checked in Ubuntu `resolute` for both architectures. This package and configuration review does not prove the installed bootloader works, that Secure Boot works, or that an installed system can reboot.

## Validation status and required next step

Completed locally:

- Reviewed the project build recipe and confirmed that the live account is passwordless and SDDM autologins it.
- Reviewed the Ubuntu-packaged Calamares 3.3.14 sources. The `removeuser` module runs `userdel -f -r`; the shell-process and module settings were checked against the packaged configuration and schemas.
- Confirmed Calamares, Ubuntu common settings, signed UEFI GRUB, and shim package availability for `amd64` and `arm64` in `resolute`.
- Ran installer static contract checks, shell syntax checks, YAML parsing, and the relevant desktop packaging tests.

Not completed:

- The existing UTM VM has an existing 64 GiB disk and was not used for installation. No real disk or existing VM disk was formatted.
- The host has about 3.5 GiB free, below the project's 30 GiB ISO-build requirement. No new ISO was built, and current output ISOs do not contain this candidate.
- The Calamares window has not been opened in a newly built IFBA live session.
- No installation to a new disposable virtual disk, UEFI reboot, login, or installed-system log review has occurred.
- Secure Boot, disk encryption, preservation of another OS, and installation under either architecture remain unvalidated.

Do not describe IFBA OS as installable or recommend installation until both architecture images pass installation to newly created disposable UEFI VM disks, reboot, user login, and post-install log review. Do not use the existing UTM disk or a real disk for this acceptance test.
