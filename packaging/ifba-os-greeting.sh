#!/bin/sh
set -eu

student_name=${IFBA_OS_DISPLAY_NAME:-}
if [ -z "$student_name" ] && [ -n "${USER:-}" ]; then
  student_name=$(getent passwd "$USER" | cut -d: -f5 | cut -d, -f1)
fi
case "$student_name" in
  ""|ubuntu|Ubuntu|Estudante) student_name="estudante" ;;
esac
student_name=$(printf '%s' "$student_name" | sed -e 's/\&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g')

printf '<txt><span foreground="#f3f4f6"><b>IFBA OS</b></span>  <span foreground="#49c267">•</span>  <span foreground="#d4d7d8">Olá, %s!</span></txt>\n' "$student_name"
printf '<tool>Área de trabalho IFBA OS</tool>\n'
