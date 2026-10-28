"""Small HTML renderers for EveryVideoTTS Studio.

Everything the UI shows as rich HTML (top bar, model status, job status, SRT
summary, hints) is built here so ``gradio_main.py`` only wires components.
Backend messages keep their emoji prefixes (✅ ❌ ⚠️ ⏹️ ⏳); the renderers read
the prefix to pick a state and show it with colour and a badge instead.
"""
from __future__ import annotations

import html
import re

REPO_URL = "https://github.com/hiimkuroshi/EveryVideoTTS"
ISSUES_URL = REPO_URL + "/issues"
DISCORD_URL = "https://discord.com/invite/yJt8kzjzWZ"

# --- Icons (inline SVG, stroke = currentColor) --------------------------------
_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>')
ICON_CHECK = _SVG.format('<circle cx="12" cy="12" r="9"/><path d="m8.5 12.5 2.5 2.5 4.5-5"/>')
ICON_ALERT = _SVG.format('<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5"/><path d="M12 16.2h.01"/>')
ICON_CHIP = _SVG.format('<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3'
                        'M2 9h3M2 15h3M19 9h3M19 15h3"/>')
ICON_SPINNER = ('<svg class="evt-spinner" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
                '<circle cx="12" cy="12" r="9" stroke="currentColor" stroke-opacity=".25" stroke-width="2.5"/>'
                '<path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg>')
ICON_WAVE = _SVG.format('<path d="M3 12h1M7 8v8M11 5v14M15 9v6M19 7v10M22 12h-1"/>')
ICON_SHIELD = _SVG.format('<path d="M12 3 5 6v5c0 4.5 3 8.3 7 10 4-1.7 7-5.5 7-10V6l-7-3z"/>')
ICON_SUN = ('<svg class="evt-ico-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2'
            'M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>')
ICON_MOON = ('<svg class="evt-ico-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
             '<path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z"/></svg>')
ICON_GITHUB = ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-3.16 '
               '19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6'
               '.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.08 2.91.83.09-.65.35-1.08.63-1.33-2.22-.25-4.55-1.11-4.55'
               '-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02a9.56 9.56 0 0 1 5 0c1.91-1.3'
               ' 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.69-4.57 4.93.36.31.68.92'
               '.68 1.85v2.75c0 .27.18.58.69.48A10 10 0 0 0 12 2z"/></svg>')
LOGO_SVG = (
    '<svg viewBox="0 0 40 40" aria-hidden="true"><defs><linearGradient id="evt-logo-g" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#8B7BFF"/><stop offset="1" stop-color="#5A3FDB"/></linearGradient></defs>'
    '<rect width="40" height="40" rx="11" fill="url(#evt-logo-g)"/><g fill="#fff">'
    '<rect x="8" y="16" width="3.4" height="8" rx="1.7"/><rect x="13.7" y="11" width="3.4" height="18" rx="1.7"/>'
    '<rect x="19.4" y="14" width="3.4" height="12" rx="1.7"/><rect x="25.1" y="8.5" width="3.4" height="23" rx="1.7"/>'
    '<rect x="30.8" y="15" width="3.4" height="10" rx="1.7" opacity=".7"/></g></svg>'
)


# --- Text helpers -------------------------------------------------------------
_LEADING_SYMBOLS = re.compile(r"^[^\w\[\(\"“'`]+", re.UNICODE)
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_CODE = re.compile(r"`([^`]+)`")


def strip_symbols(text: str) -> str:
    """Drop leading emoji / bullets / punctuation from a status line."""
    return _LEADING_SYMBOLS.sub("", (text or "").strip()).strip()


def inline_md(text: str) -> str:
    """Escape text and keep the two Markdown marks backend messages use (**bold**, `code`)."""
    out = html.escape(text or "")
    out = _BOLD.sub(r"<b>\1</b>", out)
    return _CODE.sub(r"<code>\1</code>", out)


def fmt_clock(seconds: float) -> str:
    seconds = max(0, int(round(seconds or 0)))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


# --- Section heads --------------------------------------------------------------
def section_head(title: str, step: int | None = None, sub: str = "", count_for: str | None = None) -> str:
    step_html = f'<span class="evt-step">{step}</span>' if step is not None else ""
    sub_html = f"<small>{html.escape(sub)}</small>" if sub else ""
    count_html = f'<span class="evt-count" data-for="{count_for}"></span>' if count_for else ""
    return (f'<div class="evt-section-head"><div class="evt-section-title">{step_html}'
            f'{html.escape(title)}{sub_html}</div>{count_html}</div>')


def panel_head(title: str, sub: str = "") -> str:
    sub_html = f'<span class="evt-panel-sub">{html.escape(sub)}</span>' if sub else ""
    return f'<div class="evt-panel-head"><span class="evt-panel-title">{html.escape(title)}</span>{sub_html}</div>'


def help_text(text_md: str) -> str:
    return f'<p class="evt-help">{inline_md(text_md)}</p>'


def emotion_chips(target_id: str) -> str:
    chips = "".join(
        f'<button type="button" class="evt-chip" onclick="evtInsertTag(\'{target_id}\', \'{tag}\')" '
        f'title="Chèn {tag} vào vị trí con trỏ">{tag}</button>'
        for tag in ("[cười]", "[hắng giọng]", "[thở dài]")
    )
    return (f'<div class="evt-chips"><span class="evt-chips-label">Chèn cảm xúc</span>{chips}'
            f'<span class="evt-chips-note">· thử nghiệm, chỉ v3</span></div>')


def footnote_watermark() -> str:
    return (f'<div class="evt-footnote">{ICON_SHIELD}<span>Audio được gắn watermark ẩn '
            f'để định danh nội dung do AI tạo.</span></div>')


# --- Top bar ------------------------------------------------------------------
def render_header(state: str = "idle", model_name: str = "", edition: str = "") -> str:
    if state == "ready":
        pill = f'<span class="evt-pill is-ready"><i></i><b>{html.escape(model_name or "Model")}</b> · Sẵn sàng</span>'
    elif state == "loading":
        pill = '<span class="evt-pill is-loading"><i></i>Đang tải model…</span>'
    elif state == "error":
        pill = '<span class="evt-pill is-error"><i></i>Tải model thất bại</span>'
    else:
        pill = '<span class="evt-pill"><i></i>Chưa tải model</span>'
    edition_html = f'<span class="evt-edition">{html.escape(edition)}</span>' if edition else ""
    return f"""
<header class="evt-topbar">
  <div class="evt-brand">
    <div class="evt-logo">{LOGO_SVG}</div>
    <div>
      <div class="evt-brand-name">EveryVideoTTS <span>Studio</span>{edition_html}</div>
      <div class="evt-brand-sub">Giọng đọc tiếng Việt 48 kHz · Lồng tiếng phụ đề · Clone giọng</div>
    </div>
  </div>
  <div class="evt-topbar-right">
    {pill}
    <a class="evt-icon-btn" href="{REPO_URL}" target="_blank" rel="noopener noreferrer"
       title="Mã nguồn trên GitHub" aria-label="Mã nguồn trên GitHub">{ICON_GITHUB}</a>
    <button type="button" class="evt-icon-btn" onclick="evtToggleTheme()"
       title="Đổi giao diện sáng / tối" aria-label="Đổi giao diện sáng / tối">{ICON_MOON}{ICON_SUN}</button>
  </div>
</header>"""


# --- Model status -------------------------------------------------------------
def model_state(message: str) -> str:
    msg = (message or "").strip()
    if msg.startswith("✅"):
        return "ready"
    if msg.startswith("❌"):
        return "error"
    if "Chưa tải model" in msg[:40] or not msg:
        return "idle"
    return "loading"


_KV_LINE = re.compile(r"^([^:]{1,24}):\s*(.+)$")


def render_model_status(message: str) -> str:
    state = model_state(message)
    lines = [ln.strip() for ln in (message or "").splitlines() if ln.strip()]

    if state == "idle":
        return (f'<div class="evt-model-status is-idle"><div class="evt-ms-icon">{ICON_CHIP}</div><div>'
                f'<div class="evt-ms-title">Chưa tải model</div><p>Chọn model và thiết bị rồi bấm '
                f'<b>Tải model</b>. Lần đầu cần tải trọng số từ Hugging Face nên có thể mất vài phút.</p></div></div>')

    if state == "loading":
        first = strip_symbols(lines[0]) if lines else "Đang tải model…"
        m = re.match(r"^(.*?)(?:…|\.\.\.)\s*(.*)$", first)
        title, rest = (m.group(1), m.group(2)) if m else (first, "")
        rest_html = f"<p>{inline_md(rest.strip())}</p>" if rest.strip() else ""
        return (f'<div class="evt-model-status is-loading"><div class="evt-ms-icon">{ICON_SPINNER}'
                f'</div><div><div class="evt-ms-title">{inline_md(title.strip())}…</div>{rest_html}</div></div>')

    if state == "error":
        first = strip_symbols(lines[0]) if lines else "Lỗi khi tải model"
        title, sep, detail = first.partition(": ")
        detail_lines = ([detail] if sep else []) + [strip_symbols(ln) for ln in lines[1:]]
        detail_html = "".join(f"<p>{inline_md(d)}</p>" for d in detail_lines if d)
        return (f'<div class="evt-model-status is-error"><div class="evt-ms-icon">{ICON_ALERT}</div><div>'
                f'<div class="evt-ms-title">{inline_md(title if sep else first)}</div>{detail_html}</div></div>')

    # ready
    title = strip_symbols(lines[0]) if lines else "Model đã sẵn sàng"
    kv, notes, paras = [], [], []
    for ln in lines[1:]:
        if ln.startswith("⚠"):
            notes.append(strip_symbols(ln))
            continue
        clean = strip_symbols(ln)
        m = _KV_LINE.match(clean)
        if m and "**" not in m.group(1):
            kv.append(f"<span>{html.escape(m.group(1))}: <b>{inline_md(m.group(2))}</b></span>")
        elif clean:
            paras.append(f"<p>{inline_md(clean)}</p>")
    kv_html = f'<div class="evt-kv">{"".join(kv)}</div>' if kv else ""
    notes_html = "".join(f'<div class="evt-note">{inline_md(n)}</div>' for n in notes)
    return (f'<div class="evt-model-status is-ready"><div class="evt-ms-icon">{ICON_CHECK}</div><div>'
            f'<div class="evt-ms-title">{inline_md(title)}</div>{kv_html}{"".join(paras)}{notes_html}</div></div>')


def model_accordion_label(state: str, model_name: str = "") -> str:
    if state == "ready" and model_name:
        return f"Model: {model_name}  ·  bấm để đổi"
    return "Cấu hình model"


def render_model_hints() -> str:
    return f"""
<div class="evt-hints">
  <div class="evt-hint"><h4><i></i>Máy chỉ có CPU</h4>
    <p>Dùng <b>VieNeu-TTS-v3-Turbo (int8)</b> để nhanh nhất. Chọn bản <b>v3-Turbo</b> thường khi cần
    chất lượng cao hơn, đổi lại chậm hơn trên CPU.</p></div>
  <div class="evt-hint"><h4><i></i>Máy có GPU NVIDIA</h4>
    <p><b>v3 Turbo</b> (early access): 48 kHz, clone giọng, tag cảm xúc. Cần ổn định tuyệt đối thì dùng
    <b>VieNeu-TTS-v2 (GPU)</b>. Không thấy bản GPU? Cài lại bằng <code>uv sync --group gpu</code>.</p></div>
  <div class="evt-hint"><h4><i></i>Model tuỳ chỉnh</h4>
    <p>Chọn <b>Custom Model</b> để nạp LoRA hoặc model finetune từ <b>VieNeu-TTS</b> /
    <b>VieNeu-TTS-0.3B</b>. Hướng dẫn finetune: <code>finetune/README.md</code>.</p></div>
  <div class="evt-hints-foot">Clone giọng chỉ có từ v3 (và v2 GPU). Tag cảm xúc <code>[cười]</code>
    <code>[hắng giọng]</code> <code>[thở dài]</code> đang thử nghiệm và có thể chưa ổn định.
    Gặp lỗi? Báo tại <a href="{ISSUES_URL}" target="_blank" rel="noopener noreferrer">GitHub Issues</a> hoặc
    <a href="{DISCORD_URL}" target="_blank" rel="noopener noreferrer">Discord VieNeu-TTS</a>.</div>
</div>"""


# --- Job status ---------------------------------------------------------------
_STATE_PREFIXES = (("✅", "done"), ("❌", "error"), ("⚠", "warning"), ("⏹", "stopped"))
_BADGES = {"working": "Đang xử lý", "done": "Hoàn tất", "error": "Lỗi",
           "warning": "Cần kiểm tra", "stopped": "Đã dừng"}
_ETA_IN_TEXT = re.compile(r"\s*\(?ước tính còn lại:\s*[^)]*\)?", re.IGNORECASE)


def job_state(status: str) -> str:
    s = (status or "").strip()
    if not s:
        return "idle"
    for prefix, state in _STATE_PREFIXES:
        if s.startswith(prefix):
            return state
    return "working"


def clean_job_message(status: str) -> str:
    msg = strip_symbols(status)
    msg = re.sub(r"^\[\d+\s*/\s*\d+\]\s*", "", msg)  # "[3/12] …": the step label already shows it
    msg = _ETA_IN_TEXT.sub("", msg)
    msg = re.sub(r"\.{3}", "…", msg)
    return re.sub(r"\s{2,}", " ", msg).strip()


def _split_metric(part: str) -> tuple[str, str] | None:
    part = part.strip()
    if not part:
        return None
    if ":" in part:
        label, value = part.split(":", 1)
        label, value = label.strip(), value.strip()
        if value.lower().endswith("realtime"):
            label, value = f"{label} (realtime)", value[: -len("realtime")].strip().replace("x", "×")
        return label, value
    m = re.match(r"(?i)^xử lý trong\s+(.+)$", part)
    if m:
        return "Xử lý", m.group(1)
    if re.match(r"^[\d.,]+\s*s$", part):
        return "Thời gian", part
    m = re.match(r"(?i)^(\d+)\s+(câu|đoạn)$", part)
    if m:
        return m.group(2).capitalize(), m.group(1)
    return None


def _done_view(status: str) -> str:
    text = strip_symbols(status)
    groups = re.findall(r"\(([^()]*)\)", text)
    title = text.split("(", 1)[0].strip() or "Hoàn tất"
    if title.rstrip("!. ") == "Hoàn tất":
        title = "Đã tạo xong giọng nói."
    metrics, tags = [], []
    for part in (groups[0].split(",") if groups else []):
        kv = _split_metric(part)
        if kv:
            metrics.append(kv)
        elif part.strip():
            tags.append(part.strip())
    if tags:
        metrics.append(("Chế độ", " · ".join(tags)))
    metrics_html = "".join(
        f'<div class="evt-metric"><span>{html.escape(k)}</span><b>{html.escape(v)}</b></div>' for k, v in metrics
    )
    notes_html = "".join(
        f'<div class="evt-status-note">{inline_md(strip_symbols(n))}</div>' for n in groups[1:] if n.strip()
    )
    return (f'<div class="evt-status is-done"><div class="evt-status-top"><span class="evt-badge"><i></i>'
            f'{_BADGES["done"]}</span></div><div class="evt-status-msg">{inline_md(title)}</div>'
            f'{f"<div class=evt-metrics>{metrics_html}</div>" if metrics_html else ""}{notes_html}</div>')


def render_status(status: str = "", eta: str = "", progress: dict | None = None) -> str:
    """Render the job status card.

    progress: {"done": int, "total": int, "label": str} or None (indeterminate).
    """
    state = job_state(status)
    if state == "idle":
        return (f'<div class="evt-status is-idle"><div class="evt-empty-ico">{ICON_WAVE}</div><div>'
                f'<b>Chưa có bản thu</b><p>Nhập nội dung, chọn giọng rồi bấm nút tạo. '
                f'Audio sẽ hiện và tự phát tại đây.</p></div></div>')
    if state == "done":
        return _done_view(status)

    msg = clean_job_message(status)
    if state != "working":
        return (f'<div class="evt-status is-{state}"><div class="evt-status-top"><span class="evt-badge"><i></i>'
                f'{_BADGES[state]}</span></div><div class="evt-status-msg">{inline_md(msg)}</div></div>')

    step_html, bar_html, meta_left = "", "", "Đang chuẩn bị…"
    if progress and progress.get("total"):
        total = max(1, int(progress["total"]))
        done = min(max(0, int(progress.get("done", 0))), total)
        pct = int(round(100 * done / total))
        step_html = f'<span class="evt-status-step">{html.escape(progress.get("label", ""))}</span>'
        bar_html = f'<div class="evt-progress"><span style="width:{max(pct, 3)}%"></span></div>'
        meta_left = f"{pct}% hoàn thành"
    else:
        bar_html = '<div class="evt-progress is-indeterminate"><span></span></div>'
    eta_html = html.escape(eta.replace("\n", " · ")) if eta else ""
    return (f'<div class="evt-status is-working"><div class="evt-status-top"><span class="evt-badge"><i></i>'
            f'{_BADGES["working"]}</span>{step_html}</div><div class="evt-status-msg">{inline_md(msg)}</div>'
            f'{bar_html}<div class="evt-status-meta"><span>{meta_left}</span><span>{eta_html}</span></div></div>')


# --- SRT summary --------------------------------------------------------------
def render_srt_notice(kind: str, text: str) -> str:
    """kind: 'empty' (hint) or 'error'."""
    return f'<div class="evt-srt-summary is-{kind}">{inline_md(text)}</div>'


def render_srt_summary(total: int, first_start: str, last_end: str, timeline_s: float,
                       speakers: list[str], preview: list[tuple[str, str, str, str]]) -> str:
    spk_value = str(len(speakers)) if speakers else "—"
    spk_title = html.escape(", ".join(speakers)) if speakers else "Không có nhãn nhân vật"
    stats = (
        f'<div class="evt-metric"><span>Câu phụ đề</span><b>{total}</b></div>'
        f'<div class="evt-metric"><span>Timeline</span><b>{fmt_clock(timeline_s)}</b></div>'
        f'<div class="evt-metric" title="{spk_title}"><span>Nhân vật</span><b>{spk_value}</b></div>'
    )
    items = "".join(
        f'<li><span class="evt-tc">{html.escape(start)}</span><span>'
        f'{f"<span class=evt-spk>{html.escape(spk)}:</span> " if spk else ""}{html.escape(text)}</span></li>'
        for start, _end, spk, text in preview
    )
    more = total - len(preview)
    more_html = f'<div class="evt-srt-more">+ {more} câu nữa · kết thúc lúc {html.escape(last_end)}</div>' if more > 0 \
        else f'<div class="evt-srt-more">Kết thúc lúc {html.escape(last_end)}</div>'
    spk_line = (f'<div class="evt-srt-more">Nhân vật: <b>{spk_title}</b> — gán giọng riêng ở mục '
                f'<b>Phân vai theo nhân vật</b>.</div>') if speakers else ""
    return (f'<div class="evt-srt-summary"><div class="evt-srt-stats">{stats}</div>'
            f'<ul class="evt-srt-preview">{items}</ul>{more_html}{spk_line}</div>')
