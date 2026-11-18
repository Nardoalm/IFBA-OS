# Virtual machine test checklist

Use a disposable QEMU/UTM/VirtualBox VM with 4 GB RAM, 2 CPUs, and 30 GB virtual disk. Attach the generated ISO as a virtual CD and select live boot. Keep networking in NAT mode; do not mount host directories or pass through personal credentials.

Check that the live desktop boots, the wallpaper renders, the welcome app opens, SUAP and AVA links target the official HTTPS domains, package choices are optional, and shutdown/reboot work. This prototype does not install to disk, create institutional accounts, connect to the AI API, or integrate academic data. Record failures and the VM configuration before changing build settings.
