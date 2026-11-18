#!/bin/sh
set -eu

student_name="Estudante"
if [ -n "${IFBA_OS_DISPLAY_NAME:-}" ]; then
  student_name=$IFBA_OS_DISPLAY_NAME
fi

hour=$(date +%H)
if [ "$hour" -lt 12 ]; then
  greeting="Bom dia"
elif [ "$hour" -lt 18 ]; then
  greeting="Boa tarde"
else
  greeting="Boa noite"
fi

printf '<txt><span foreground="#f3f4f6"><b>IFBA OS</b></span>  <span foreground="#49c267">•</span>  <span foreground="#d4d7d8">%s, %s</span></txt>\n' "$greeting" "$student_name"
printf '<tool>Área de trabalho IFBA OS</tool>\n'
