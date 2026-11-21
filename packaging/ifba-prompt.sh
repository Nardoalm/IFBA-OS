# IFBA OS interactive Bash prompt; no shell behavior is changed in scripts.
case $- in
  *i*)
    __ifba_set_prompt() {
      local status=$?
      if [ "$status" -eq 0 ]; then
        PS1='\[\e[38;5;78m\]\u@\h\[\e[0m\] \[\e[38;5;244m\]\w\[\e[0m\]\n\[\e[38;5;78m\]>\[\e[0m\] '
      else
        PS1='\[\e[38;5;203m\]! \[\e[38;5;78m\]\u@\h\[\e[0m\] \[\e[38;5;244m\]\w\[\e[0m\]\n\[\e[38;5;78m\]>\[\e[0m\] '
      fi
    }
    PROMPT_COMMAND=__ifba_set_prompt
    ;;
esac
