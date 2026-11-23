# IFBA OS defaults for interactive Bash sessions.
case $- in
  *i*)
    PS1='\[\e[1;32m\]\u@\h\[\e[0m\]:\w\$ '
    if [ -n "${KONSOLE_VERSION:-}" ] && ! command -v neofetch >/dev/null &&
       command -v fastfetch >/dev/null; then
      alias neofetch='fastfetch --config /usr/share/ifba-os/fastfetch.jsonc'
    fi
    ;;
esac
