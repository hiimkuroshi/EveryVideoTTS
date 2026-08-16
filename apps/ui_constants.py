import gradio as gr

theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="blue",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont('Plus Jakarta Sans'), gr.themes.GoogleFont('Inter'), 'system-ui', 'sans-serif'],
    font_mono=[gr.themes.GoogleFont('JetBrains Mono'), 'ui-monospace', 'monospace'],
).set(
    body_background_fill="*neutral_50",
    body_background_fill_dark="*neutral_950",
    block_background_fill="white",
    block_background_fill_dark="*neutral_900",
    block_border_width="1px",
    block_border_color="*neutral_200",
    block_border_color_dark="*neutral_800",
    block_radius="14px",
    block_shadow="0 2px 10px -1px rgba(0, 0, 0, 0.04)",
    button_primary_background_fill="linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%)",
    button_primary_background_fill_hover="linear-gradient(135deg, #4338ca 0%, #2563eb 100%)",
    button_primary_text_color="white",
    button_primary_border_color="transparent",
    button_primary_shadow="0 4px 12px rgba(79, 70, 229, 0.25)",
    button_primary_shadow_hover="0 6px 16px rgba(79, 70, 229, 0.35)",
    button_secondary_background_fill="*neutral_100",
    button_secondary_background_fill_hover="*neutral_200",
    button_secondary_background_fill_dark="*neutral_800",
    button_secondary_background_fill_hover_dark="*neutral_700",
    button_large_radius="10px",
    button_small_radius="8px",
    input_background_fill="*neutral_50",
    input_background_fill_dark="*neutral_950",
    input_border_color="*neutral_200",
    input_border_color_dark="*neutral_800",
    input_border_color_focus="*primary_500",
    input_radius="10px",
    slider_color="*primary_600",
)

css = """
/* === BASE LAYOUT & TYPOGRAPHY === */
.container {
    max-width: 1440px !important;
    margin: 0 auto !important;
    padding: 0 12px !important;
}

body, gradio-app {
    font-feature-settings: "cv02", "cv03", "cv04", "cv11";
    -webkit-font-smoothing: antialiased;
}

/* === STUDIO HEADER === */
.studio-header {
    background: linear-gradient(135deg, #090d16 0%, #111827 50%, #1e1b4b 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    padding: 28px 32px;
    margin-bottom: 24px;
    box-shadow: 0 12px 36px -4px rgba(0, 0, 0, 0.35), 0 0 0 1px rgba(255, 255, 255, 0.05);
    color: #f8fafc !important;
    position: relative;
    overflow: hidden;
}

.studio-header::before {
    content: "";
    position: absolute;
    top: -50%;
    right: -20%;
    width: 380px;
    height: 380px;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.18) 0%, rgba(59, 130, 246, 0) 70%);
    pointer-events: none;
    border-radius: 50%;
}

.header-top-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
}

.header-brand {
    display: flex;
    align-items: center;
    gap: 14px;
}

.header-logo-icon {
    font-size: 2.4rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    width: 54px;
    height: 54px;
    box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.2);
}

.header-title-text {
    font-size: 1.85rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.2;
    color: #ffffff;
    margin: 0;
}

.header-subtitle {
    font-size: 0.88rem;
    font-weight: 500;
    color: #94a3b8;
    margin-top: 2px;
}

.header-chips-row {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}

.chip-item {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 100px;
    font-size: 0.82rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.chip-author {
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.35);
    color: #a5b4fc !important;
}

.chip-author:hover {
    background: rgba(99, 102, 241, 0.25);
    color: #c7d2fe !important;
    transform: translateY(-1px);
}

.chip-repo {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #e2e8f0 !important;
}

.chip-repo:hover {
    background: rgba(255, 255, 255, 0.12);
    color: #ffffff !important;
    transform: translateY(-1px);
}

.chip-badge {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #6ee7b7 !important;
}

/* === STUDIO CONTROL CARDS === */
.control-panel-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px -2px rgba(15, 23, 42, 0.04);
}

.dark .control-panel-card {
    background: #0f172a;
    border-color: #1e293b;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.25);
}

/* === STATUS & ESTIMATE BOXES === */
.status-box, .estimate-box {
    border-radius: 12px !important;
    border: 1px solid rgba(99, 102, 241, 0.15) !important;
    background: rgba(99, 102, 241, 0.03) !important;
    padding: 12px !important;
    font-family: inherit;
    font-size: 0.9rem;
    line-height: 1.5;
}

.status-box textarea, .estimate-box textarea {
    font-family: inherit !important;
    font-size: 0.92rem !important;
    text-align: center;
}

/* === QUICK EMOTION TAGS === */
.emotion-tag-container {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    margin: 8px 0 14px 0;
}

.emotion-tag-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 500;
    background: rgba(99, 102, 241, 0.08);
    border: 1px solid rgba(99, 102, 241, 0.2);
    color: #4f46e5;
    cursor: pointer;
    transition: all 0.15s ease;
    user-select: none;
}

.emotion-tag-pill:hover {
    background: rgba(99, 102, 241, 0.15);
    border-color: rgba(99, 102, 241, 0.35);
    transform: translateY(-1px);
}

.dark .emotion-tag-pill {
    background: rgba(99, 102, 241, 0.15);
    border-color: rgba(99, 102, 241, 0.3);
    color: #a5b4fc;
}

/* === ACTION BUTTONS === */
.btn-primary-action {
    background: linear-gradient(135deg, #4f46e5 0%, #2563eb 100%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 10px 20px !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.25) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.btn-primary-action:hover {
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4) !important;
    transform: translateY(-1px) !important;
}

.btn-stop-action {
    background: #fee2e2 !important;
    border: 1px solid #fca5a5 !important;
    color: #b91c1c !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
}

.btn-stop-action:hover {
    background: #fecaca !important;
    border-color: #f87171 !important;
    color: #991b1b !important;
    transform: translateY(-1px) !important;
}

.dark .btn-stop-action {
    background: rgba(239, 68, 68, 0.15) !important;
    border-color: rgba(239, 68, 68, 0.35) !important;
    color: #fca5a5 !important;
}

/* === RESULT & AUDIO METRICS CARD === */
.audio-metric-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(15, 23, 42, 0.03);
    border: 1px solid rgba(15, 23, 42, 0.06);
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 0.85rem;
    color: #475569;
    margin-bottom: 10px;
}

.dark .audio-metric-bar {
    background: rgba(255, 255, 255, 0.03);
    border-color: rgba(255, 255, 255, 0.08);
    color: #94a3b8;
}

.audio-metric-item {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-weight: 600;
}

/* === SRT & PODCAST SPEAKER TABLE === */
.speaker-table {
    border-radius: 12px;
    overflow: hidden;
    margin-top: 12px;
}

.srt-speed-banner {
    background: linear-gradient(135deg, rgba(79, 70, 229, 0.05) 0%, rgba(59, 130, 246, 0.05) 100%);
    border: 1px solid rgba(79, 70, 229, 0.15);
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 16px;
}

.srt-speed-title {
    font-weight: 700;
    font-size: 0.95rem;
    color: #3730a3;
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 4px;
}

.dark .srt-speed-title {
    color: #a5b4fc;
}

.srt-speed-desc {
    font-size: 0.85rem;
    color: #4b5563;
    line-height: 1.4;
}

.dark .srt-speed-desc {
    color: #9ca3af;
}
"""

head_html = """
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🎬</text></svg>">
<meta name="theme-color" content="#090d16">
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
