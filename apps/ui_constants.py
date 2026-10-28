"""Design system for EveryVideoTTS Studio (Gradio theme, CSS and head scripts).

Colours live in two token tables (LIGHT / DARK). They feed both the Gradio theme
and the ``--evt-*`` CSS variables, so the palette is defined in exactly one place.
Dark is the default look; the header button switches modes and remembers the choice.
"""
import gradio as gr

# ---------------------------------------------------------------------------
# 1. Tokens
# ---------------------------------------------------------------------------
LIGHT = {
    "bg": "#F3F4F8",
    "surface": "#FFFFFF",
    "surface-2": "#F7F8FB",
    "surface-3": "#EDEFF5",
    "border": "#E2E5ED",
    "border-strong": "#CBD1DD",
    "text": "#141824",
    "text-2": "#465064",
    "text-3": "#687186",
    "accent": "#6246EA",
    "accent-hover": "#5335D8",
    "accent-text": "#5236D6",
    "accent-soft": "rgba(98, 70, 234, 0.09)",
    "accent-ring": "rgba(98, 70, 234, 0.26)",
    "success": "#0B8A5F",
    "success-soft": "rgba(11, 138, 95, 0.10)",
    "warning": "#A16207",
    "warning-soft": "rgba(202, 138, 4, 0.12)",
    "danger": "#D12E3E",
    "danger-soft": "rgba(209, 46, 62, 0.08)",
    "danger-border": "rgba(209, 46, 62, 0.30)",
    "shadow": "0 1px 2px rgba(16, 24, 40, 0.04), 0 10px 28px -14px rgba(16, 24, 40, 0.14)",
    "cta-shadow": "0 1px 0 rgba(255,255,255,0.20) inset, 0 10px 22px -12px rgba(98, 70, 234, 0.75)",
    "glow": "rgba(98, 70, 234, 0.07)",
}

DARK = {
    "bg": "#0B0D12",
    "surface": "#12151C",
    "surface-2": "#181C25",
    "surface-3": "#202531",
    "border": "#242A36",
    "border-strong": "#353D4E",
    "text": "#E8EBF2",
    "text-2": "#A7AFC0",
    "text-3": "#7F889C",
    "accent": "#6E58F6",
    "accent-hover": "#806CFF",
    "accent-text": "#AA9CFF",
    "accent-soft": "rgba(124, 102, 255, 0.14)",
    "accent-ring": "rgba(124, 102, 255, 0.36)",
    "success": "#3DD9A0",
    "success-soft": "rgba(61, 217, 160, 0.12)",
    "warning": "#F5C04A",
    "warning-soft": "rgba(245, 192, 74, 0.12)",
    "danger": "#F87C7C",
    "danger-soft": "rgba(248, 124, 124, 0.12)",
    "danger-border": "rgba(248, 124, 124, 0.32)",
    "shadow": "0 1px 0 rgba(255, 255, 255, 0.025) inset, 0 16px 36px -20px rgba(0, 0, 0, 0.7)",
    "cta-shadow": "0 1px 0 rgba(255,255,255,0.16) inset, 0 12px 26px -14px rgba(124, 102, 255, 0.9)",
    "glow": "rgba(124, 102, 255, 0.11)",
}

# Waveform colours are fixed (Gradio takes one value for both modes): mid-tones
# that read on both the light and the dark surface.
WAVEFORM_COLOR = "#8A93A8"
WAVEFORM_PROGRESS_COLOR = "#7C66FF"

_VIOLET = gr.themes.Color(
    c50="#F3F1FF", c100="#E9E5FF", c200="#D4CCFF", c300="#B6A8FF", c400="#9784FF",
    c500="#7C66FF", c600="#6A4FF5", c700="#5A3FDB", c800="#4A34B3", c900="#3D2E8C",
    c950="#241A57", name="evt_violet",
)
_INK = gr.themes.Color(
    c50="#F5F6FA", c100="#ECEEF4", c200="#DCE0E9", c300="#C2C8D5", c400="#8E97AA",
    c500="#6E7789", c600="#4F5769", c700="#323A4B", c800="#252B38", c900="#171B24",
    c950="#0F1218", name="evt_ink",
)


def _pair(name: str, key_light: str, key_dark: str | None = None) -> dict:
    """Theme variable for light + its *_dark twin, taken from the token tables."""
    return {name: LIGHT[key_light], f"{name}_dark": DARK[key_dark or key_light]}


def _both(name: str, value: str) -> dict:
    return {name: value, f"{name}_dark": value}


_theme_vars: dict = {}
for _name, _key in [
    ("body_text_color", "text"),
    ("body_text_color_subdued", "text-3"),
    ("background_fill_primary", "surface"),
    ("background_fill_secondary", "surface-2"),
    ("border_color_primary", "border"),
    ("border_color_accent", "accent"),
    ("border_color_accent_subdued", "accent-ring"),
    ("color_accent_soft", "accent-soft"),
    ("link_text_color", "accent-text"),
    ("link_text_color_hover", "accent-text"),
    ("link_text_color_active", "accent-text"),
    ("link_text_color_visited", "accent-text"),
    ("code_background_fill", "surface-3"),
    ("block_border_color", "border"),
    ("block_label_text_color", "text-2"),
    ("block_title_text_color", "text-2"),
    ("block_info_text_color", "text-3"),
    ("panel_background_fill", "surface"),
    ("panel_border_color", "border"),
    ("accordion_text_color", "text"),
    ("table_text_color", "text"),
    ("table_border_color", "border"),
    ("table_even_background_fill", "surface"),
    ("table_odd_background_fill", "surface-2"),
    ("table_row_focus", "accent-soft"),
    ("input_background_fill", "surface-2"),
    ("input_background_fill_focus", "surface-2"),
    ("input_background_fill_hover", "surface-2"),
    ("input_border_color", "border"),
    ("input_border_color_hover", "border-strong"),
    ("input_border_color_focus", "accent"),
    ("input_placeholder_color", "text-3"),
    ("checkbox_background_color", "surface-2"),
    ("checkbox_background_color_focus", "surface-2"),
    ("checkbox_background_color_hover", "surface-3"),
    ("checkbox_background_color_selected", "accent"),
    ("checkbox_border_color", "border-strong"),
    ("checkbox_border_color_focus", "accent"),
    ("checkbox_border_color_hover", "border-strong"),
    ("checkbox_border_color_selected", "accent"),
    ("checkbox_label_background_fill", "surface-2"),
    ("checkbox_label_background_fill_hover", "surface-3"),
    ("checkbox_label_background_fill_selected", "accent-soft"),
    ("checkbox_label_border_color", "border"),
    ("checkbox_label_border_color_hover", "border-strong"),
    ("checkbox_label_border_color_selected", "accent"),
    ("checkbox_label_text_color", "text-2"),
    ("checkbox_label_text_color_selected", "text"),
    ("slider_color", "accent"),
    ("loader_color", "accent"),
    ("stat_background_fill", "accent-soft"),
    ("error_background_fill", "danger-soft"),
    ("error_border_color", "danger-border"),
    ("error_text_color", "danger"),
    ("error_icon_color", "danger"),
    ("button_primary_background_fill_hover", "accent-hover"),
    ("button_primary_border_color", "accent"),
    ("button_primary_border_color_hover", "accent-hover"),
    ("button_primary_shadow", "cta-shadow"),
    ("button_primary_shadow_hover", "cta-shadow"),
    ("button_secondary_background_fill", "surface-2"),
    ("button_secondary_background_fill_hover", "surface-3"),
    ("button_secondary_border_color", "border"),
    ("button_secondary_border_color_hover", "border-strong"),
    ("button_secondary_text_color", "text"),
    ("button_secondary_text_color_hover", "text"),
    ("button_cancel_background_fill", "danger-soft"),
    ("button_cancel_background_fill_hover", "danger-soft"),
    ("button_cancel_border_color", "danger-border"),
    ("button_cancel_border_color_hover", "danger"),
    ("button_cancel_text_color", "danger"),
    ("button_cancel_text_color_hover", "danger"),
]:
    _theme_vars.update(_pair(_name, _key))

_theme_vars.update({
    "color_accent": LIGHT["accent"],
    "body_background_fill": (
        f"radial-gradient(1100px 420px at 50% -180px, {LIGHT['glow']}, transparent 70%), {LIGHT['bg']}"
    ),
    "body_background_fill_dark": (
        f"radial-gradient(1100px 420px at 50% -180px, {DARK['glow']}, transparent 70%), {DARK['bg']}"
    ),
    "input_shadow_focus": f"0 0 0 3px {LIGHT['accent-ring']}",
    "input_shadow_focus_dark": f"0 0 0 3px {DARK['accent-ring']}",
    "button_primary_background_fill": (
        f"linear-gradient(180deg, {LIGHT['accent-hover']} 0%, {LIGHT['accent']} 100%)"
    ),
    "button_primary_background_fill_dark": (
        f"linear-gradient(180deg, {DARK['accent-hover']} 0%, {DARK['accent']} 100%)"
    ),
})
for _name, _value in [
    ("block_background_fill", "transparent"),
    ("block_border_width", "0px"),
    ("block_shadow", "none"),
    ("block_label_background_fill", "transparent"),
    ("block_label_border_width", "0px"),
    ("block_title_background_fill", "transparent"),
    ("block_title_border_width", "0px"),
    ("input_border_width", "1px"),
    ("input_shadow", "none"),
    ("panel_border_width", "1px"),
    ("checkbox_label_border_width", "1px"),
    ("button_border_width", "1px"),
    ("shadow_spread", "3px"),
    ("button_primary_text_color", "#FFFFFF"),
    ("button_primary_text_color_hover", "#FFFFFF"),
    ("button_secondary_shadow", "none"),
    ("button_secondary_shadow_hover", "none"),
    ("button_cancel_shadow", "none"),
    ("button_cancel_shadow_hover", "none"),
]:
    _theme_vars.update(_both(_name, _value))

_theme_vars.update({
    "body_text_size": "15px",
    "body_text_weight": "400",
    "prose_text_size": "15px",
    "prose_header_text_weight": "650",
    "block_padding": "0px",
    "block_radius": "14px",
    "block_label_padding": "6px 10px",
    "block_label_radius": "8px",
    "block_label_margin": "0px",
    "block_label_text_size": "13px",
    "block_label_text_weight": "600",
    "block_title_padding": "0px",
    "block_title_radius": "0px",
    "block_title_text_size": "13.5px",
    "block_title_text_weight": "600",
    "block_info_text_size": "13px",
    "block_info_text_weight": "400",
    "container_radius": "14px",
    "embed_radius": "14px",
    "form_gap_width": "0px",
    "layout_gap": "16px",
    "section_header_text_size": "15px",
    "section_header_text_weight": "600",
    "input_radius": "10px",
    "input_padding": "10px 12px",
    "input_text_size": "15px",
    "input_text_weight": "400",
    "checkbox_border_radius": "5px",
    "checkbox_label_padding": "8px 14px",
    "checkbox_label_gap": "8px",
    "checkbox_label_text_size": "14px",
    "checkbox_label_text_weight": "500",
    "checkbox_label_shadow": "none",
    "checkbox_shadow": "none",
    "table_radius": "10px",
    "button_large_padding": "12px 22px",
    "button_large_radius": "11px",
    "button_large_text_size": "15.5px",
    "button_large_text_weight": "600",
    "button_medium_padding": "9px 16px",
    "button_medium_radius": "10px",
    "button_medium_text_size": "14.5px",
    "button_medium_text_weight": "600",
    "button_small_padding": "6px 12px",
    "button_small_radius": "9px",
    "button_small_text_size": "13.5px",
    "button_small_text_weight": "600",
    "button_transition": "background .15s ease, border-color .15s ease, box-shadow .15s ease, color .15s ease",
    "button_transform_hover": "none",
    "button_transform_active": "translateY(1px)",
    "shadow_drop": "0 1px 2px rgba(0, 0, 0, 0.06)",
    "shadow_drop_lg": LIGHT["shadow"],
})

theme = gr.themes.Base(
    primary_hue=_VIOLET,
    secondary_hue=_VIOLET,
    neutral_hue=_INK,
    font=[gr.themes.GoogleFont("Be Vietnam Pro", weights=(400, 500, 600, 700)),
          "ui-sans-serif", "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono", weights=(400, 500)),
               "ui-monospace", "SFMono-Regular", "Consolas", "monospace"],
).set(**_theme_vars)


# ---------------------------------------------------------------------------
# 2. CSS
# ---------------------------------------------------------------------------
def _token_block(selector: str, tokens: dict) -> str:
    body = "\n".join(f"    --evt-{k}: {v};" for k, v in tokens.items())
    return f"{selector} {{\n{body}\n}}"


_TOKENS_CSS = _token_block(":root", LIGHT) + "\n" + _token_block(".dark", DARK)

_CSS_BODY = r"""
/* ---------- Base ---------- */
.gradio-container {
    max-width: 1360px !important;
    margin: 0 auto !important;
    padding: clamp(12px, 2vw, 20px) clamp(10px, 2.4vw, 28px) 8px !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
.gradio-container ::selection { background: var(--evt-accent-ring); }
.gradio-container * { scrollbar-width: thin; scrollbar-color: var(--evt-border-strong) transparent; }
#evt-app { gap: 16px; }
/* Gradio adds its own side padding around the app; the container above already has it. */
.gradio-container main.app { padding: 0 !important; }
footer { opacity: .55; transition: opacity .2s; }
footer:hover { opacity: 1; }
.gradio-container .prose { color: var(--evt-text-2); }
.gradio-container .prose code {
    font-size: .88em; padding: 1px 6px; border-radius: 6px;
    background: var(--evt-surface-3); color: var(--evt-text); border: 0;
}
.gradio-container .prose b, .gradio-container .prose strong { color: var(--evt-text); font-weight: 600; }

/* HTML blocks: never clip (Vietnamese diacritics sit above the line box). */
.gradio-container .block:has(> .html-container) { overflow: visible !important; }

/* Gradio groups consecutive inputs into a ".form" box; keep it invisible. */
.gradio-container .form {
    border: 0 !important; background: transparent !important; box-shadow: none !important;
    gap: 16px !important; overflow: visible !important;
}
.gradio-container .row { gap: 16px; }
/* Labels above inputs */
.gradio-container span[data-testid="block-info"] { margin-bottom: 8px; letter-spacing: .005em; }
.gradio-container textarea { line-height: 1.65 !important; }
.gradio-container input[type="number"] { font-variant-numeric: tabular-nums; }
.gradio-container button:disabled, .gradio-container button[disabled] {
    opacity: .45; cursor: not-allowed; box-shadow: none !important; filter: saturate(.6);
}
.gradio-container button.primary:focus-visible,
.gradio-container button.secondary:focus-visible {
    outline: 2px solid var(--evt-accent); outline-offset: 2px;
}
/* Dropdown: keep long names from running under the caret */
.wrap-inner .secondary-wrap input[role="listbox"] { padding-right: 28px; text-overflow: ellipsis; }
.gradio-container ul.options { border: 1px solid var(--evt-border) !important; border-radius: 10px !important;
    box-shadow: var(--evt-shadow) !important; padding: 4px !important; }
.gradio-container ul.options li.item { border-radius: 7px; padding: 8px 10px; }
.gradio-container ul.options li.item.selected,
.gradio-container ul.options li.item:hover { background: var(--evt-accent-soft) !important; }

/* ---------- Top bar ---------- */
.evt-topbar {
    display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;
    padding: 14px 16px 14px 18px; border-radius: 16px;
    background: var(--evt-surface); border: 1px solid var(--evt-border); box-shadow: var(--evt-shadow);
}
.evt-brand { display: flex; align-items: center; gap: 14px; min-width: 0; }
.evt-logo { width: 42px; height: 42px; flex: none; filter: drop-shadow(0 6px 14px rgba(110, 88, 246, .35)); }
.evt-logo svg { width: 100%; height: 100%; display: block; }
.evt-brand-name { font-size: 19px; font-weight: 700; letter-spacing: -.02em; color: var(--evt-text); line-height: 1.25; }
.evt-brand-name span { color: var(--evt-accent-text); font-weight: 600; }
.evt-brand-sub { font-size: 13.5px; color: var(--evt-text-3); margin-top: 2px; line-height: 1.4; }
.evt-topbar-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.evt-edition {
    font-size: 12px; font-weight: 600; padding: 3px 8px; border-radius: 999px; margin-left: 6px;
    color: var(--evt-accent-text); background: var(--evt-accent-soft); vertical-align: 3px; letter-spacing: 0;
}
.evt-pill {
    display: inline-flex; align-items: center; gap: 8px; max-width: 100%;
    padding: 7px 13px; border-radius: 999px; font-size: 13.5px; font-weight: 600;
    background: var(--evt-surface-2); border: 1px solid var(--evt-border); color: var(--evt-text-2);
}
.evt-pill i { width: 8px; height: 8px; border-radius: 50%; background: var(--evt-text-3); flex: none; }
.evt-pill b { color: var(--evt-text); font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.evt-pill.is-ready i { background: var(--evt-success); box-shadow: 0 0 0 3px var(--evt-success-soft); }
.evt-pill.is-loading i { background: var(--evt-warning); animation: evt-pulse 1.2s ease-in-out infinite; }
.evt-pill.is-error { border-color: var(--evt-danger-border); }
.evt-pill.is-error i { background: var(--evt-danger); }
.evt-icon-btn {
    width: 38px; height: 38px; display: inline-grid; place-items: center; border-radius: 10px; cursor: pointer;
    background: var(--evt-surface-2); border: 1px solid var(--evt-border); color: var(--evt-text-2);
    transition: background .15s, color .15s, border-color .15s; text-decoration: none !important;
}
.evt-icon-btn:hover { background: var(--evt-surface-3); color: var(--evt-text); border-color: var(--evt-border-strong); }
.evt-icon-btn svg { width: 18px; height: 18px; }
.evt-icon-btn .evt-ico-sun { display: none; }
.dark .evt-icon-btn .evt-ico-sun { display: block; }
.dark .evt-icon-btn .evt-ico-moon { display: none; }
@keyframes evt-pulse { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }

/* ---------- Cards ---------- */
.evt-card, #evt-model-card {
    background: var(--evt-surface) !important; border: 1px solid var(--evt-border) !important;
    border-radius: 16px !important; box-shadow: var(--evt-shadow) !important;
}
.evt-card { padding: 18px 20px 20px !important; gap: 16px !important; }
#evt-workspace { align-items: flex-start; gap: 16px; }
#evt-output { position: sticky; top: 16px; }

/* Model card = accordion */
#evt-model-card { padding: 4px 20px !important; }
#evt-model-card > .label-wrap {
    padding: 12px 0; font-size: 15px; font-weight: 600; color: var(--evt-text);
}
#evt-model-card > .label-wrap.open { margin-bottom: 4px; }
#evt-model-card > div:last-child { padding-bottom: 16px; }
#evt-model-row { align-items: flex-end; }
#evt-model-row > button { min-height: 46px; height: 46px; padding-top: 0; padding-bottom: 0; }
#evt-model-row fieldset .wrap label { min-height: 46px; padding-top: 0; padding-bottom: 0; }
#evt-model-row input[role="listbox"] { min-height: 30px; }

/* Accordion chevron: replace Gradio's ▼ glyph */
.gradio-container .label-wrap .icon {
    font-size: 0 !important; width: 26px; height: 26px; display: inline-grid !important; place-items: center;
    border-radius: 8px; color: var(--evt-text-3); transition: transform .2s ease, background .15s;
}
.gradio-container .label-wrap:hover .icon { background: var(--evt-surface-3); color: var(--evt-text); }
.gradio-container .label-wrap .icon::before {
    content: ""; width: 7px; height: 7px; border-right: 2px solid currentColor; border-bottom: 2px solid currentColor;
    transform: translateY(2px) rotate(-135deg);
}
/* Sub-accordions inside cards */
.evt-sub-acc { border-top: 1px solid var(--evt-border) !important; border-radius: 0 !important; padding-top: 4px !important; }
.evt-sub-acc > .label-wrap { padding: 10px 0; font-size: 14.5px; font-weight: 600; color: var(--evt-text-2); }
.evt-sub-acc > .label-wrap:hover { color: var(--evt-text); }
.evt-sub-acc > div:last-child { padding-top: 6px; }
.evt-inline-acc { border: 1px solid var(--evt-border) !important; border-radius: 12px !important; padding: 0 14px !important;
    background: var(--evt-surface-2) !important; }
.evt-inline-acc > .label-wrap { padding: 11px 0; font-size: 14px; font-weight: 600; color: var(--evt-text-2); }
.evt-inline-acc > .label-wrap:hover { color: var(--evt-text); }
.evt-inline-acc > div:last-child { padding-bottom: 14px; }

/* ---------- Tabs ---------- */
#evt-tabs > .tab-wrapper { margin-bottom: 18px; padding-bottom: 0 !important; border-bottom: 1px solid var(--evt-border); }
#evt-tabs > .tab-wrapper .tab-container[role="tablist"] { gap: 4px; height: auto !important; border: 0 !important; }
/* Sizing also applies to Gradio's hidden copies of the tab buttons: it measures
   those to decide which tabs fit, so both must have the same width. */
#evt-tabs > .tab-wrapper .tab-container button { font-size: 15px; font-weight: 600; padding: 10px 14px 12px; }
#evt-tabs > .tab-wrapper button[role="tab"] {
    color: var(--evt-text-3); border: 0; background: transparent; position: relative; border-radius: 8px 8px 0 0;
}
#evt-tabs > .tab-wrapper button[role="tab"]:hover { color: var(--evt-text); }
#evt-tabs > .tab-wrapper button[role="tab"].selected { color: var(--evt-text); }
#evt-tabs > .tab-wrapper button[role="tab"].selected::after {
    content: ""; position: absolute; left: 10px; right: 10px; bottom: -1px; height: 2px;
    border-radius: 2px; background: var(--evt-accent);
}
#evt-tabs > .tabitem { padding: 0 !important; border: 0 !important; background: transparent !important; }
#evt-tabs > .tabitem > .column { gap: 16px; }

/* Segmented control (nested tabs: preset voice / voice cloning) */
.evt-seg > .tab-wrapper { border: 0 !important; margin-bottom: 12px; padding-bottom: 0 !important; }
.evt-seg > .tab-wrapper .tab-container[role="tablist"] {
    display: flex !important; width: 100%; gap: 3px; padding: 3px;
    border-radius: 11px; background: var(--evt-surface-2); border: 1px solid var(--evt-border) !important; height: auto !important;
}
.evt-seg > .tab-wrapper .tab-container button { font-size: 14px; font-weight: 600; padding: 8px 14px; }
.evt-seg > .tab-wrapper button[role="tab"] {
    flex: 1 1 0; justify-content: center; text-align: center; border-radius: 8px; border: 0;
    color: var(--evt-text-3); background: transparent;
}
.evt-seg > .tab-wrapper button[role="tab"]:hover { color: var(--evt-text); }
.evt-seg > .tab-wrapper button[role="tab"].selected {
    color: var(--evt-text); background: var(--evt-surface); box-shadow: 0 1px 2px rgba(0,0,0,.12), 0 0 0 1px var(--evt-border);
}
.evt-seg > .tab-wrapper button[role="tab"].selected::after { display: none; }
.evt-seg > .tabitem { padding: 0 !important; border: 0 !important; background: transparent !important; }
.evt-seg > .tabitem > .column { gap: 14px; }

/* ---------- Sections ---------- */
.evt-section-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 2px 0 -6px; min-height: 24px; }
.evt-section-title { display: flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 650; color: var(--evt-text); }
.evt-section-title small { font-size: 13px; font-weight: 400; color: var(--evt-text-3); }
.evt-step {
    width: 24px; height: 24px; border-radius: 8px; display: inline-grid; place-items: center; flex: none;
    font-size: 13px; font-weight: 700; color: var(--evt-accent-text); background: var(--evt-accent-soft);
}
.evt-count { font-size: 13px; color: var(--evt-text-3); font-variant-numeric: tabular-nums; white-space: nowrap; }
.evt-divider { height: 1px; background: var(--evt-border); margin: 4px 0; }
.evt-help { font-size: 13.5px; line-height: 1.6; color: var(--evt-text-3); margin: 0; }
.evt-help b { color: var(--evt-text-2); font-weight: 600; }
.evt-help code, .evt-chip, .evt-mono { font-family: var(--font-mono); }
.evt-help code { font-size: 12.5px; padding: 1px 6px; border-radius: 6px; background: var(--evt-surface-3); color: var(--evt-text-2); }

/* Main text areas */
#evt-text textarea, #evt-conv-script textarea { font-size: 15.5px !important; min-height: 220px; }
#evt-srt-text textarea { font-family: var(--font-mono) !important; font-size: 13.5px !important; line-height: 1.6 !important;
    font-variant-ligatures: none; font-feature-settings: "liga" 0, "calt" 0; }

/* Emotion tag chips */
.evt-chips { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: -4px; }
.evt-chips-label { font-size: 13px; color: var(--evt-text-3); margin-right: 2px; }
.evt-chip {
    font-size: 13px; padding: 5px 11px; border-radius: 999px; cursor: pointer; line-height: 1.3;
    color: var(--evt-accent-text); background: var(--evt-accent-soft); border: 1px solid transparent;
    transition: border-color .15s, background .15s;
}
.evt-chip:hover { border-color: var(--evt-accent-ring); }
.evt-chip:active { transform: translateY(1px); }
.evt-chips-note { font-size: 12.5px; color: var(--evt-text-3); }

/* Primary call to action */
.evt-cta { min-height: 52px; font-size: 16px !important; letter-spacing: .005em; margin-top: 4px; }
.evt-cta-hint, .evt-cta-hint .html-container, .evt-cta-hint .prose { height: auto !important; overflow: visible !important; }
.evt-cta-hint { margin-top: -6px; }
.evt-cta:not(:disabled):not([disabled]) + .evt-cta-hint { display: none !important; }
.evt-cta-hint p { margin: 0; text-align: center; font-size: 13px; color: var(--evt-text-3); }

/* Small secondary buttons that should hug their label */
.evt-btn-fit { flex: 0 0 auto !important; min-width: 0 !important; width: auto !important; align-self: flex-start; }

/* File drop zones: compact */
.evt-file .wrap { padding: 14px !important; }
.evt-file [data-testid="block-label"] { display: none; }
.evt-file { border: 1px dashed var(--evt-border-strong) !important; border-radius: 12px !important; background: var(--evt-surface-2) !important; }
.evt-file:hover { border-color: var(--evt-accent) !important; }
.evt-file .icon-wrap svg, .evt-file .wrap svg { color: var(--evt-text-3); }
.evt-file .or { color: var(--evt-text-3); }

/* Reference audio uploader */
.evt-ref-audio { border: 1px solid var(--evt-border) !important; border-radius: 12px !important; background: var(--evt-surface-2) !important; }

/* Speaker mapping rows */
.evt-spk-head { display: grid; grid-template-columns: minmax(120px, 1fr) 3fr; gap: 16px; font-size: 12.5px;
    font-weight: 600; color: var(--evt-text-3); text-transform: uppercase; letter-spacing: .05em; margin-bottom: -6px; }
.evt-spk-row { align-items: center; gap: 16px !important; }
.evt-spk-name input, .evt-spk-name textarea {
    font-weight: 600 !important; color: var(--evt-text) !important; background: var(--evt-accent-soft) !important;
    border-color: transparent !important; opacity: 1 !important; -webkit-text-fill-color: var(--evt-text);
}

/* ---------- Model card content ---------- */
.evt-model-status { display: flex; gap: 12px; align-items: flex-start; padding: 12px 14px; border-radius: 12px;
    background: var(--evt-surface-2); border: 1px solid var(--evt-border); font-size: 14px; color: var(--evt-text-2); }
.evt-model-status .evt-ms-icon { width: 22px; height: 22px; flex: none; display: grid; place-items: center; margin-top: 1px; }
.evt-model-status .evt-ms-icon svg { width: 20px; height: 20px; }
.evt-model-status .evt-ms-title { font-weight: 600; color: var(--evt-text); margin-bottom: 2px; }
.evt-model-status p { margin: 2px 0 0; line-height: 1.55; }
.evt-model-status.is-ready { border-color: color-mix(in srgb, var(--evt-success) 30%, transparent); }
.evt-model-status.is-ready .evt-ms-icon { color: var(--evt-success); }
.evt-model-status.is-error { border-color: var(--evt-danger-border); background: var(--evt-danger-soft); }
.evt-model-status.is-error .evt-ms-icon { color: var(--evt-danger); }
.evt-model-status.is-loading .evt-ms-icon { color: var(--evt-warning); }
.evt-model-status.is-idle .evt-ms-icon { color: var(--evt-text-3); }
.evt-kv { display: flex; flex-wrap: wrap; gap: 6px 8px; margin-top: 8px; }
.evt-kv span { font-size: 13px; padding: 3px 10px; border-radius: 8px; background: var(--evt-surface-3); color: var(--evt-text-2); }
.evt-kv span b { color: var(--evt-text); font-weight: 600; }
.evt-note { margin-top: 10px; padding: 10px 12px; border-radius: 10px; font-size: 13.5px; line-height: 1.55;
    background: var(--evt-warning-soft); color: var(--evt-text); border: 1px solid color-mix(in srgb, var(--evt-warning) 30%, transparent); }
.evt-spinner { width: 20px; height: 20px; color: var(--evt-accent-text); animation: evt-spin .8s linear infinite; }
@keyframes evt-spin { to { transform: rotate(360deg); } }

/* Model hints */
.evt-hints { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.evt-hint { padding: 14px 16px; border-radius: 12px; background: var(--evt-surface-2); border: 1px solid var(--evt-border); }
.evt-hint h4 { margin: 0 0 6px; font-size: 14px; font-weight: 650; color: var(--evt-text); display: flex; align-items: center; gap: 8px; }
.evt-hint h4 i { width: 8px; height: 8px; border-radius: 3px; background: var(--evt-accent); display: inline-block; }
.evt-hint p { margin: 0; font-size: 13.5px; line-height: 1.6; color: var(--evt-text-2); }
.evt-hint b { color: var(--evt-text); font-weight: 600; }
.evt-hint code { font-family: var(--font-mono); font-size: 12px; padding: 1px 5px; border-radius: 5px; background: var(--evt-surface-3); color: var(--evt-text); }
.evt-hints-foot { grid-column: 1 / -1; font-size: 13px; color: var(--evt-text-3); line-height: 1.6; }
.evt-hints-foot a { color: var(--evt-accent-text); }

/* ---------- Output panel ---------- */
.evt-panel-head { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; }
.evt-panel-title { font-size: 16px; font-weight: 650; color: var(--evt-text); }
.evt-panel-sub { font-size: 13px; color: var(--evt-text-3); }
#evt-audio { border: 1px solid var(--evt-border) !important; border-radius: 12px !important; background: var(--evt-surface-2) !important; padding: 8px 10px 4px !important; }
#evt-audio [data-testid="block-label"] { position: static; display: inline-flex; color: var(--evt-text-3); padding: 2px 2px 6px; }
#evt-actions { gap: 10px !important; }
#evt-actions > button { flex: 1 1 0; }
.evt-footnote { display: flex; gap: 8px; align-items: flex-start; font-size: 12.5px; line-height: 1.5; color: var(--evt-text-3); }
.evt-footnote svg { width: 14px; height: 14px; flex: none; margin-top: 2px; }

/* Generation status */
.evt-status { border-radius: 12px; border: 1px solid var(--evt-border); background: var(--evt-surface-2); padding: 14px 16px; }
.evt-status.is-idle { display: flex; gap: 14px; align-items: center; padding: 26px 18px; border-style: dashed; }
.evt-status.is-idle .evt-empty-ico { width: 44px; height: 44px; flex: none; border-radius: 12px; display: grid; place-items: center;
    color: var(--evt-accent-text); background: var(--evt-accent-soft); }
.evt-status.is-idle .evt-empty-ico svg { width: 22px; height: 22px; }
.evt-status.is-idle b { display: block; font-size: 14.5px; color: var(--evt-text); font-weight: 600; margin-bottom: 2px; }
.evt-status.is-idle p { margin: 0; font-size: 13.5px; line-height: 1.5; color: var(--evt-text-3); }
.evt-status-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 8px; }
.evt-badge { display: inline-flex; align-items: center; gap: 7px; font-size: 12.5px; font-weight: 650; letter-spacing: .02em;
    padding: 3px 10px 3px 8px; border-radius: 999px; background: var(--evt-accent-soft); color: var(--evt-accent-text); }
.evt-badge i { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.is-working .evt-badge i { animation: evt-pulse 1.1s ease-in-out infinite; }
.is-done .evt-badge { background: var(--evt-success-soft); color: var(--evt-success); }
.is-error .evt-badge { background: var(--evt-danger-soft); color: var(--evt-danger); }
.is-warning .evt-badge, .is-stopped .evt-badge { background: var(--evt-warning-soft); color: var(--evt-warning); }
.evt-status.is-error { border-color: var(--evt-danger-border); }
.evt-status-step { font-size: 13px; font-weight: 600; color: var(--evt-text-2); font-variant-numeric: tabular-nums; }
.evt-status-msg { font-size: 14px; line-height: 1.55; color: var(--evt-text); overflow-wrap: anywhere; }
.evt-progress { position: relative; height: 6px; border-radius: 999px; background: var(--evt-surface-3); overflow: hidden; margin: 12px 0 8px; }
.evt-progress > span { position: absolute; inset: 0 auto 0 0; border-radius: inherit; transition: width .35s ease;
    background: linear-gradient(90deg, var(--evt-accent), var(--evt-accent-hover)); }
.evt-progress.is-indeterminate > span { width: 35%; animation: evt-indet 1.3s ease-in-out infinite; }
@keyframes evt-indet { 0% { left: -35%; } 100% { left: 100%; } }
.evt-status-meta { display: flex; justify-content: space-between; gap: 8px; font-size: 12.5px; color: var(--evt-text-3); font-variant-numeric: tabular-nums; }
.evt-metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(118px, 1fr)); gap: 8px; margin-top: 12px; }
.evt-metric { padding: 8px 10px; border-radius: 10px; background: var(--evt-surface); border: 1px solid var(--evt-border); min-width: 0; }
.evt-metric span { display: block; font-size: 12px; color: var(--evt-text-3); margin-bottom: 2px; }
.evt-metric b { font-size: 14.5px; font-weight: 650; color: var(--evt-text); font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.evt-status-note { margin-top: 10px; font-size: 13px; line-height: 1.5; color: var(--evt-text-2); padding-left: 10px; border-left: 2px solid var(--evt-warning); }

/* SRT summary */
.evt-srt-summary { border-radius: 12px; border: 1px solid var(--evt-border); background: var(--evt-surface-2); padding: 14px 16px; }
.evt-srt-summary.is-empty { border-style: dashed; color: var(--evt-text-3); font-size: 13.5px; padding: 12px 16px; }
.evt-srt-summary.is-error { border-color: var(--evt-danger-border); background: var(--evt-danger-soft); color: var(--evt-text); font-size: 14px; }
.evt-srt-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.evt-srt-preview { list-style: none; margin: 12px 0 0; padding: 0; display: grid; gap: 6px; }
.evt-srt-preview li { display: grid; grid-template-columns: auto 1fr; gap: 12px; font-size: 13.5px; line-height: 1.5; color: var(--evt-text-2); }
.evt-srt-preview .evt-tc { font-family: var(--font-mono); font-size: 12px; color: var(--evt-text-3); padding-top: 2px; white-space: nowrap; }
.evt-srt-preview .evt-spk { font-weight: 600; color: var(--evt-accent-text); }
.evt-srt-more { margin-top: 8px; font-size: 12.5px; color: var(--evt-text-3); }

/* Examples table inside voice cloning */
.gradio-container .gallery, .gradio-container table.table { border-radius: 10px; }

/* Legacy classes (Intel XPU edition) */
.status-box textarea, .estimate-box textarea { text-align: center; font-family: inherit; }

/* ---------- Responsive ---------- */
@media (max-width: 1024px) {
    .evt-hints { grid-template-columns: 1fr; }
    #evt-output { position: static; }
}
@media (max-width: 768px) {
    .evt-topbar { padding: 12px 14px; }
    .evt-logo { width: 36px; height: 36px; }
    .evt-brand-name { font-size: 17px; }
    .evt-chips-note { display: none; }
    .evt-brand-sub { display: none; }
    .evt-card { padding: 16px 14px 18px !important; }
    #evt-model-card { padding: 2px 14px !important; }
    #evt-tabs > .tab-wrapper .tab-container button { font-size: 14px; padding: 9px 9px 11px; }
    #evt-tabs > .tab-wrapper .tab-container[role="tablist"] { gap: 0; }
    .evt-srt-stats { grid-template-columns: 1fr 1fr; }
    #evt-text textarea, #evt-conv-script textarea { min-height: 180px; }
    .evt-status.is-idle { padding: 18px 14px; }
}
"""

css = _TOKENS_CSS + "\n" + _CSS_BODY

# Gradio ships no Vietnamese strings; override the built-in ones the app shows
# (upload zones, recorder, footer). Same dict for "en" (fallback) and "vi".
_VI_STRINGS = {
    "upload_text.click_to_upload": "Bấm để chọn file",
    "upload_text.drop_file": "Kéo thả file vào đây",
    "upload_text.drop_audio": "Kéo thả file audio vào đây",
    "upload_text.paste_clipboard": "Dán từ clipboard",
    "common.or": "hoặc",
    "common.clear": "Xoá",
    "common.download": "Tải xuống",
    "common.edit": "Sửa",
    "common.empty": "Trống",
    "common.error": "Lỗi",
    "common.loading": "Đang tải",
    "common.remove": "Gỡ bỏ",
    "common.settings": "Cài đặt",
    "common.share": "Chia sẻ",
    "common.undo": "Hoàn tác",
    "common.language": "Ngôn ngữ",
    "common.display_theme": "Giao diện",
    "common.record": "Ghi âm",
    "common.stop_recording": "Dừng ghi âm",
    "common.no_devices": "Không tìm thấy thiết bị",
    "audio.allow_recording_access": "Hãy cho phép truy cập micro để ghi âm.",
    "audio.drop_to_upload": "Thả file audio vào đây để tải lên",
    "audio.record_from_microphone": "Ghi âm từ micro",
    "audio.stop_recording": "Dừng ghi",
    "audio.stop": "Dừng",
    "audio.resume": "Tiếp tục",
    "audio.record": "Ghi âm",
    "audio.no_microphone": "Không tìm thấy micro",
    "audio.pause": "Tạm dừng",
    "audio.play": "Phát",
    "audio.waiting": "Đang chờ",
    "file.uploading": "Đang tải lên…",
    "errors.use_via_api": "Dùng qua API",
    "errors.use_via_api_or_mcp": "Dùng qua API hoặc MCP",
    "blocks.waiting_for_inputs": "Đang chờ tải file xong, vui lòng thử lại.",
    "blocks.lost_connection": "Mất kết nối do rời trang. Đang vào lại hàng chờ…",
}
i18n = gr.I18n(en=_VI_STRINGS, vi=_VI_STRINGS)


# ---------------------------------------------------------------------------
# 3. Head (favicon + small client-side helpers)
# ---------------------------------------------------------------------------
_FAVICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E"
    "%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E"
    "%3Cstop offset='0' stop-color='%238B7BFF'/%3E%3Cstop offset='1' stop-color='%235A3FDB'/%3E"
    "%3C/linearGradient%3E%3C/defs%3E%3Crect width='40' height='40' rx='11' fill='url(%23g)'/%3E"
    "%3Cg fill='%23fff'%3E%3Crect x='8' y='16' width='3.4' height='8' rx='1.7'/%3E"
    "%3Crect x='13.7' y='11' width='3.4' height='18' rx='1.7'/%3E"
    "%3Crect x='19.4' y='14' width='3.4' height='12' rx='1.7'/%3E"
    "%3Crect x='25.1' y='8.5' width='3.4' height='23' rx='1.7'/%3E"
    "%3Crect x='30.8' y='15' width='3.4' height='10' rx='1.7' opacity='.7'/%3E%3C/g%3E%3C/svg%3E"
)

head_html = f"""
<link rel="icon" type="image/svg+xml" href="{_FAVICON}">
<meta name="theme-color" content="#0B0D12">
<script>
(function () {{
  // Dark is the default look. A choice made with the header button is remembered.
  var pref = 'dark';
  try {{ pref = localStorage.getItem('evt-theme') || 'dark'; }} catch (e) {{}}
  try {{
    var url = new URL(window.location.href);
    var forced = url.searchParams.get('__theme');
    if (forced === 'light' || forced === 'dark') {{ pref = forced; }}
    else {{ url.searchParams.set('__theme', pref); window.history.replaceState(null, '', url.toString()); }}
  }} catch (e) {{}}
  function apply(mode) {{ if (document.body) document.body.classList.toggle('dark', mode === 'dark'); }}
  if (document.body) apply(pref); else document.addEventListener('DOMContentLoaded', function () {{ apply(pref); }});

  window.evtToggleTheme = function () {{
    var mode = document.body.classList.contains('dark') ? 'light' : 'dark';
    apply(mode);
    try {{ localStorage.setItem('evt-theme', mode); }} catch (e) {{}}
    try {{
      var u = new URL(window.location.href); u.searchParams.set('__theme', mode);
      window.history.replaceState(null, '', u.toString());
    }} catch (e) {{}}
  }};

  // Insert an emotion tag at the caret of a Gradio textbox (by elem_id).
  window.evtInsertTag = function (id, tag) {{
    var ta = document.querySelector('#' + id + ' textarea');
    if (!ta) return;
    var s = ta.selectionStart == null ? ta.value.length : ta.selectionStart;
    var e = ta.selectionEnd == null ? s : ta.selectionEnd;
    var before = ta.value.slice(0, s), after = ta.value.slice(e);
    var ins = (before && !/\\s$/.test(before) ? ' ' : '') + tag + (after && !/^\\s/.test(after) ? ' ' : '');
    ta.value = before + ins + after;
    var pos = before.length + ins.length;
    ta.focus();
    try {{ ta.setSelectionRange(pos, pos); }} catch (err) {{}}
    ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
  }};

  // Live character counters: <span class="evt-count" data-for="elem_id">.
  function tick() {{
    var nodes = document.querySelectorAll('.evt-count[data-for]');
    for (var i = 0; i < nodes.length; i++) {{
      var ta = document.querySelector('#' + nodes[i].getAttribute('data-for') + ' textarea');
      if (!ta) continue;
      var n = ta.value.length;
      var txt = n.toLocaleString('vi-VN') + ' ký tự';
      if (nodes[i].textContent !== txt) nodes[i].textContent = txt;
    }}
  }}
  setInterval(tick, 400);

  // Gradio sizes textareas once at mount, before this page's line-height applies,
  // which can hide the last line. Ask it to re-measure when content overflows.
  function fitTextareas() {{
    var tas = document.querySelectorAll('#evt-text textarea, #evt-conv-script textarea, #evt-srt-text textarea');
    for (var i = 0; i < tas.length; i++) {{
      var ta = tas[i];
      if (ta.style.overflowY === 'hidden' && ta.scrollHeight > ta.clientHeight + 4 && document.activeElement !== ta) {{
        ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
      }}
    }}
  }}
  setInterval(fitTextareas, 1000);

  // On narrow screens, bring the result panel into view after starting a job.
  window.evtScrollToOutput = function () {{
    if (window.innerWidth > 1024) return;
    var el = document.getElementById('evt-output');
    if (el) setTimeout(function () {{ el.scrollIntoView({{ behavior: 'smooth', block: 'start' }}); }}, 150);
  }};
}})();
</script>
"""

DEFAULT_TEXT_GPU = "Hà Nội, trái tim của Việt Nam, là một thành phố ngàn năm văn hiến với bề dày lịch sử và văn hóa độc đáo. Bước chân trên những con phố cổ kính quanh Hồ Hoàn Kiếm, du khách như được du hành ngược thời gian, chiêm ngưỡng kiến trúc Pháp cổ điển hòa quyện với nét kiến trúc truyền thống Việt Nam. Mỗi con phố trong khu phố cổ mang một tên gọi đặc trưng, phản ánh nghề thủ công truyền thống từng thịnh hành nơi đây như phố Hàng Bạc, Hàng Đào, Hàng Mã. Ẩm thực Hà Nội cũng là một điểm nhấn đặc biệt, từ tô phở nóng hổi buổi sáng, bún chả thơm lừng trưa hè, đến chè Thái ngọt ngào chiều thu. Những món ăn dân dã này đã trở thành biểu tượng của văn hóa ẩm thực Việt, được cả thế giới yêu mến. Người Hà Nội nổi tiếng với tính cách hiền hòa, lịch thiệp nhưng cũng rất cầu toàn trong từng chi tiết nhỏ, từ cách pha trà sen cho đến cách chọn hoa sen tây để thưởng trà."
DEFAULT_TEXT_TURBO = (
    "Trước đây, hệ thống điện chủ yếu sử dụng direct current, nhưng Tesla đã chứng minh rằng alternating current is more efficient for long-distance transmission. Nhờ đó, điện có thể được truyền đi xa hơn với ít tổn thất năng lượng hơn. Đây là một bước tiến cực kỳ quan trọng trong ngành điện.\n\n"
    "Một trong những phát minh nổi tiếng của ông là Tesla coil, một thiết bị có thể tạo ra điện áp rất cao và những tia sét nhân tạo. This device is still used today in demonstrations và trong một số ứng dụng nghiên cứu. Khi nhìn thấy những tia điện này, nhiều người cảm thấy vừa ấn tượng vừa hơi đáng sợ."
)

# v3 Turbo demo text — khoe giọng tự nhiên + tag cảm xúc [cười] (tính năng mới, thử nghiệm).
DEFAULT_TEXT_V3 = (
    "Xin chào mọi người! [hắng giọng] Như bạn đang nghe thấy đấy, tốc độ xử lý của mình cực kỳ nhanh và mượt mà, giúp phản hồi gần như ngay lập tức theo thời gian thực. Chính vì vậy, mình rất phù hợp để ứng dụng trực tiếp vào các hệ thống Chatbot thông minh, trợ lý ảo, hoặc làm tổng đài viên tự động cho các doanh nghiệp. Tiện lợi quá đúng không ạ? [cười] Hi vọng phiên bản nâng cấp v3 này sẽ mang lại trải nghiệm tuyệt vời cho dự án của bạn."
)
