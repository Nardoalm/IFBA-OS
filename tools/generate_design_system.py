#!/usr/bin/env python3
"""Generate IFBA OS desktop color assets from canonical design tokens."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "packaging/design-system/tokens.json"
OUTPUTS = {
    "colors": ROOT / "packaging/color-schemes/IFBA-OS-Dark.colors",
    "plasma_colors": ROOT / "packaging/plasma/desktoptheme/IFBA-WhiteSur-Dark/colors",
    "konsole": ROOT / "packaging/konsole/IFBA Glass.colorscheme",
    "gtk": ROOT / "packaging/gtk/gtk.css",
    "gtk_settings": ROOT / "packaging/gtk/settings.ini",
    "assistant_gtk": ROOT / "packaging/ifba-ai.css",
    "welcome_qt": ROOT / "packaging/design-system/ifba-welcome.qss",
    "motion_profile": ROOT / "packaging/design-system/visual-motionrc",
}


def rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def rgba(value, alpha):
    return "rgba({}, {}, {}, {:.3f})".format(*rgb(value), alpha)


def generate(tokens):
    colors = tokens["colors"]
    spacing = tokens["spacing_px"]
    radius = tokens["radius_px"]
    motion = tokens["motion"]
    easing = motion["easing"]
    kde = tokens["kde_surfaces"]
    palette = {
        "[General]": {"Name": "IFBA OS Dark", "ColorScheme": "IFBA-OS-Dark", "shadeSortColumn": "true"},
        "[Colors:Window]": {"BackgroundNormal": kde["surface"], "BackgroundAlternate": kde["surface_elevated"], "ForegroundNormal": colors["text_primary"], "ForegroundInactive": colors["text_secondary"], "DecorationHover": colors["accent"], "DecorationFocus": colors["focus"]},
        "[Colors:View]": {"BackgroundNormal": kde["background"], "BackgroundAlternate": kde["surface"], "ForegroundNormal": colors["text_primary"], "ForegroundInactive": colors["text_secondary"], "DecorationHover": colors["accent"], "DecorationFocus": colors["focus"]},
        "[Colors:Button]": {"BackgroundNormal": kde["surface_elevated"], "BackgroundAlternate": kde["surface"], "ForegroundNormal": colors["text_primary"], "ForegroundInactive": colors["text_secondary"], "DecorationHover": colors["accent"], "DecorationFocus": colors["focus"]},
        "[Colors:Selection]": {"BackgroundNormal": kde["selection"], "BackgroundAlternate": kde["surface_elevated"], "ForegroundNormal": colors["text_primary"], "ForegroundInactive": colors["text_secondary"]},
        "[Colors:Tooltip]": {"BackgroundNormal": kde["surface_elevated"], "BackgroundAlternate": kde["surface"], "ForegroundNormal": colors["text_primary"], "ForegroundInactive": colors["text_secondary"]},
        "[Colors:Complementary]": {"BackgroundNormal": kde["surface_elevated"], "BackgroundAlternate": kde["surface"], "ForegroundNormal": colors["text_primary"], "ForegroundInactive": colors["text_secondary"]},
        "[Colors:Header]": {"BackgroundNormal": kde["surface"], "BackgroundAlternate": kde["surface_elevated"], "ForegroundNormal": colors["text_primary"], "ForegroundInactive": colors["text_secondary"]},
        "[Colors:Header][Inactive]": {"BackgroundNormal": kde["background"], "BackgroundAlternate": kde["surface"], "ForegroundNormal": colors["text_secondary"], "ForegroundInactive": colors["text_secondary"]},
        "[WM]": {"activeBackground": kde["surface"], "activeForeground": colors["text_primary"], "inactiveBackground": kde["background"], "inactiveForeground": colors["text_secondary"]},
    }
    color_text = []
    for section, values in palette.items():
        color_text.append(section)
        for key, value in values.items():
            if value.startswith("#"):
                value = ",".join(str(channel) for channel in rgb(value))
            color_text.append(f"{key}={value}")
        color_text.append("")

    # GTK 3 uses .titlebutton, while GTK 4 uses the action class on the button.
    gtk_button = "button:not(.titlebutton):not(.close):not(.minimize):not(.maximize):not(.restore)"
    gtk_text = f'''/* Generated from packaging/design-system/tokens.json. */
@define-color window_bg_color {colors['background']};
@define-color view_bg_color {colors['background']};
@define-color card_bg_color {colors['surface']};
@define-color popover_bg_color {colors['surface_elevated']};
@define-color window_fg_color {colors['text_primary']};
@define-color view_fg_color {colors['text_primary']};
@define-color card_fg_color {colors['text_primary']};
@define-color popover_fg_color {colors['text_primary']};
@define-color secondary_fg_color {colors['text_secondary']};
@define-color accent_color {colors['accent']};
@define-color accent_bg_color {colors['accent']};
@define-color accent_fg_color {colors['background']};
@define-color borders {colors['border']};
@define-color error_color {colors['danger']};
@define-color warning_color {colors['warning']};
@define-color success_color {colors['accent']};

* {{
  font-family: "{tokens['typography']['family']}", sans-serif;
  outline-color: {colors['focus']};
}}
window, dialog {{ background-color: @window_bg_color; color: @window_fg_color; }}
entry, textview, list, row, notebook, frame {{
  background-color: @card_bg_color; color: @card_fg_color;
  border-color: @borders; border-radius: {radius['control']}px;
}}
{gtk_button} {{
  color: @window_fg_color; background-image: none; background-color: @card_bg_color;
  border: 1px solid @borders; border-radius: {radius['control']}px;
  padding: {spacing['sm']}px {spacing['md']}px;
}}
{gtk_button}:hover {{ background-color: {rgba(colors['accent'], tokens['opacity']['hover'])}; }}
{gtk_button}:active, {gtk_button}:checked, row:selected {{
  background-color: {rgba(colors['accent'], tokens['opacity']['selection'])}; color: @window_fg_color;
}}
{gtk_button}:focus, entry:focus {{ outline: 2px solid @accent_color; outline-offset: 1px; }}
{gtk_button}:disabled {{ opacity: {tokens['opacity']['disabled']}; }}
tooltip {{ background-color: @popover_bg_color; color: @popover_fg_color; border-radius: {radius['small']}px; }}
'''
    gtk_settings = f'''[Settings]
gtk-application-prefer-dark-theme=1
gtk-font-name={tokens['typography']['family']} {tokens['typography']['base_pt']}
gtk-icon-theme-name=breeze-dark
gtk-theme-name=Breeze-Dark
gtk-decoration-layout=close,minimize,maximize:
'''
    assistant_gtk = f'''/* Generated from packaging/design-system/tokens.json. */
window {{ background-color: {colors['background']}; color: {colors['text_primary']}; font-family: "{tokens['typography']['family']}", sans-serif; font-size: {tokens['typography']['base_pt']}pt; }}
headerbar {{ background-image: none; background-color: {colors['surface']}; color: {colors['text_primary']}; border-bottom: 1px solid {colors['border']}; box-shadow: none; }}
box.sidebar {{ background-color: {colors['surface']}; border-right: 1px solid {colors['border']}; }}
textview, textview text, entry {{ background-color: {colors['surface_elevated']}; color: {colors['text_primary']}; caret-color: {colors['accent']}; border-color: {colors['border']}; border-radius: {radius['control']}px; }}
button {{ color: {colors['text_primary']}; background-image: none; background-color: {colors['surface_elevated']}; border: 1px solid {colors['border']}; border-radius: {radius['control']}px; min-height: 30px; padding: {spacing['xs']}px {spacing['md']}px; transition-duration: {motion['duration_standard_ms']}ms; }}
button:hover {{ background-color: {rgba(colors['accent'], tokens['opacity']['hover'])}; border-color: {colors['focus']}; }}
button:active, button:checked {{ background-color: {rgba(colors['accent'], tokens['opacity']['selection'])}; border-color: {colors['accent']}; }}
button.flat {{ background-color: transparent; border-color: transparent; }}
button.linked {{ border-radius: 0; }}
button.linked:first-child {{ border-radius: {radius['control']}px 0 0 {radius['control']}px; }}
button.linked:last-child {{ border-radius: 0 {radius['control']}px {radius['control']}px 0; }}
label.dim-label {{ color: {colors['text_secondary']}; }}
button:focus, entry:focus, textview:focus {{ border-color: {colors['focus']}; box-shadow: inset 0 0 0 1px {colors['focus']}; }}
button.suggested-action {{ color: {colors['background']}; background-color: {colors['accent']}; border-color: {colors['accent']}; }}
button.suggested-action:hover {{ background-color: {colors['accent_hover']}; }}
button:disabled {{ color: {colors['text_secondary']}; background-color: {colors['surface']}; border-color: {colors['border']}; opacity: {tokens['opacity']['disabled']}; }}
label:disabled {{ color: {colors['text_secondary']}; }}
'''
    welcome_qt = f'''/* Generated from packaging/design-system/tokens.json. */
QMainWindow, QScrollArea, QWidget#welcomeContent {{ background: {colors['background']}; color: {colors['text_primary']}; }}
QFrame#hero {{ background: {colors['surface']}; border: 1px solid {colors['border']}; border-radius: {radius['surface']}px; }}
QLabel#identity {{ color: {colors['background']}; background: {colors['accent']}; border-radius: {radius['control']}px; font-weight: 700; letter-spacing: 1px; }}
QLabel#heroTitle {{ font-size: {tokens['typography']['title_pt']}pt; font-weight: 700; color: {colors['text_primary']}; }}
QLabel#heroSubtitle, QLabel#sectionHint {{ color: {colors['text_secondary']}; }}
QLabel#versionBadge {{ color: {colors['text_primary']}; background: {colors['surface_elevated']}; border: 1px solid {colors['border']}; border-radius: {radius['control']}px; padding: 6px 10px; }}
QLabel#sectionTitle {{ color: {colors['text_primary']}; font-size: {tokens['typography']['large_pt']}pt; font-weight: 650; }}
QFrame#card {{ background: {colors['surface']}; border: 1px solid {colors['border']}; border-radius: {radius['surface']}px; }}
QLabel#cardTitle {{ color: {colors['text_primary']}; font-size: {tokens['typography']['large_pt']}pt; font-weight: 650; }}
QLabel#cardDescription, QLabel#emptyState {{ color: {colors['text_secondary']}; }}
QPushButton {{ color: {colors['text_primary']}; background: {colors['surface_elevated']}; border: 1px solid {colors['border']}; border-radius: {radius['control']}px; padding: {spacing['sm']}px {spacing['md']}px; }}
QPushButton:hover {{ background: {colors['surface_hover']}; border-color: {colors['focus']}; }}
QPushButton:pressed {{ background: {colors['surface_pressed']}; }}
QPushButton:focus {{ border: 2px solid {colors['focus']}; }}
QPushButton#primaryButton {{ color: {colors['background']}; background: {colors['accent']}; border: 1px solid {colors['accent']}; font-weight: 650; min-width: 110px; }}
QPushButton#primaryButton:hover {{ background: {colors['accent_hover']}; }}
QCheckBox {{ color: {colors['text_secondary']}; spacing: {spacing['sm']}px; }}
QCheckBox::indicator {{ width: 17px; height: 17px; }}
QCheckBox::indicator:checked {{ background: {colors['accent']}; border: 1px solid {colors['focus']}; border-radius: {radius['small']}px; }}
QCheckBox::indicator:unchecked {{ background: {colors['surface_elevated']}; border: 1px solid {colors['border']}; border-radius: {radius['small']}px; }}
'''
    motion_profile = f'''# Generated from packaging/design-system/tokens.json.
[Motion]
DurationFastMs={motion['duration_fast_ms']}
DurationStandardMs={motion['duration_standard_ms']}
DurationSlowMs={motion['duration_slow_ms']}
'''
    terminal_colors = {
        "[Background]": {"Color": colors["background"], "Transparency": "12"},
        "[BackgroundIntense]": {"Color": colors["surface"], "Transparency": "12"},
        "[Color0]": {"Color": colors["surface_elevated"]}, "[Color0Intense]": {"Color": colors["text_secondary"]},
        "[Color1]": {"Color": colors["danger"]}, "[Color1Intense]": {"Color": "#FB7185"},
        "[Color2]": {"Color": colors["accent"]}, "[Color2Intense]": {"Color": colors["focus"]},
        "[Color3]": {"Color": colors["warning"]}, "[Color3Intense]": {"Color": "#FDE68A"},
        "[Color4]": {"Color": "#60A5FA"}, "[Color4Intense]": {"Color": "#93C5FD"},
        "[Color5]": {"Color": "#C084FC"}, "[Color5Intense]": {"Color": "#D8B4FE"},
        "[Color6]": {"Color": "#2DD4BF"}, "[Color6Intense]": {"Color": "#5EEAD4"},
        "[Color7]": {"Color": colors["text_secondary"]}, "[Color7Intense]": {"Color": colors["text_primary"]},
        "[Foreground]": {"Color": colors["text_primary"]}, "[ForegroundIntense]": {"Color": "#FFFFFF"},
        "[General]": {"Description": "IFBA Glass", "Opacity": str(tokens["opacity"]["panel"]), "Wallpaper": ""},
    }
    konsole_text = []
    for section, values in terminal_colors.items():
        konsole_text.append(section)
        for key, value in values.items():
            if value.startswith("#"):
                value = ",".join(str(channel) for channel in rgb(value))
            konsole_text.append(f"{key}={value}")
        konsole_text.append("")
    return {
        OUTPUTS["colors"]: "\n".join(color_text),
        OUTPUTS["plasma_colors"]: "\n".join(color_text),
        OUTPUTS["konsole"]: "\n".join(konsole_text),
        OUTPUTS["gtk"]: gtk_text,
        OUTPUTS["gtk_settings"]: gtk_settings,
        OUTPUTS["assistant_gtk"]: assistant_gtk,
        OUTPUTS["welcome_qt"]: welcome_qt,
        OUTPUTS["motion_profile"]: motion_profile,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated files are stale")
    args = parser.parse_args()
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    stale = []
    for path, contents in generate(tokens).items():
        normalized = contents.rstrip() + "\n"
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != normalized:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(normalized, encoding="utf-8")
    if stale:
        parser.error("generated assets are stale: " + ", ".join(stale))


if __name__ == "__main__":
    main()
