import gradio as gr

theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="cyan",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont('Inter'), 'ui-sans-serif', 'system-ui'],
).set(
    button_primary_background_fill="linear-gradient(90deg, #6366f1 0%, #0ea5e9 100%)",
    button_primary_background_fill_hover="linear-gradient(90deg, #4f46e5 0%, #0284c7 100%)",
)

css = """
.container { max-width: 1400px; margin: auto; }
.header-box {
    text-align: center;
    margin-bottom: 25px;
    padding: 25px;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-radius: 12px;
    color: white !important;
}
.header-title {
    font-size: 2.5rem;
    font-weight: 800;
    color: white !important;
}
.gradient-text {
    background: -webkit-linear-gradient(45deg, #60A5FA, #22D3EE);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.header-icon {
    color: white;
}
.status-box {
    font-weight: 500;
    border: 1px solid rgba(99, 102, 241, 0.1);
    background: rgba(99, 102, 241, 0.03);
    border-radius: 8px;
}
.status-box textarea {
    text-align: center;
    font-family: inherit;
}
.estimate-box {
    font-weight: 500;
    border: 1px solid rgba(99, 102, 241, 0.1);
    background: rgba(99, 102, 241, 0.03);
    border-radius: 8px;
}
.estimate-box textarea {
    text-align: center;
    font-family: inherit;
}
.model-card-content {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    gap: 15px;
    font-size: 0.9rem;
    text-align: center;
    color: white !important;
}
.model-card-item {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    color: white !important;
}
.model-card-item strong {
    color: white !important;
}
.model-card-item span {
    color: white !important;
}
.model-card-link {
    color: #60A5FA;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s;
}
.model-card-link:hover {
    color: #22D3EE;
    text-decoration: underline;
}
/* Dropdown: Gradio đặt mũi tên position:absolute đè lên ô input rộng 100%,
   nên chữ dài chạy xuống dưới mũi tên. Chừa chỗ cho mũi tên và cắt bằng "…". */
.wrap-inner .secondary-wrap input[role="listbox"] {
    padding-right: 28px;
    text-overflow: ellipsis;
}

/* Warning banner — mọi màu lấy từ token, dark mode chỉ đổi token. */
.warning-banner {
    --wb-bg: #fffbeb;
    --wb-border: #fef3c7;
    --wb-title: #92400e;
    --wb-text: #78350f;
    --wb-divider: #fcd34d;
    --wb-tip-text: #92400e;
    --wb-tip-label: #78350f;
    --wb-link: #b45309;
    /* Thẻ mặc định (GPU, tông vàng) */
    --wb-card-bg: #fef3c7;
    --wb-card-border: #fde68a;
    --wb-card-heading: #b45309;
    --wb-card-text: #78350f;
    --wb-chip-text: #451a03;
    --wb-chip-bg: rgba(251, 191, 36, 0.2);

    background-color: var(--wb-bg);
    border: 1px solid var(--wb-border);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 20px;
    color: var(--wb-text);
}
.warning-banner-item--cpu {
    --wb-card-bg: #dcfce7;
    --wb-card-border: #86efac;
    --wb-card-heading: #15803d;
    --wb-card-text: #166534;
    --wb-chip-text: #14532d;
    --wb-chip-bg: rgba(34, 197, 94, 0.2);
    --wb-link: #15803d;
}
.dark .warning-banner {
    --wb-bg: var(--block-background-fill, #1e293b);
    --wb-border: rgba(251, 191, 36, 0.35);
    --wb-title: #fcd34d;
    --wb-text: #e2e8f0;
    --wb-divider: rgba(251, 191, 36, 0.3);
    --wb-tip-text: #cbd5e1;
    --wb-tip-label: #fbbf24;
    --wb-link: #fcd34d;
    --wb-card-bg: var(--background-fill-secondary, #0f172a);
    --wb-card-border: rgba(251, 191, 36, 0.32);
    --wb-card-heading: #fbbf24;
    --wb-card-text: #e2e8f0;
    --wb-chip-text: #fde68a;
    --wb-chip-bg: rgba(251, 191, 36, 0.16);
}
.dark .warning-banner-item--cpu {
    --wb-card-bg: var(--background-fill-secondary, #0f172a);
    --wb-card-border: rgba(74, 222, 128, 0.32);
    --wb-card-text: #e2e8f0;
    --wb-card-heading: #4ade80;
    --wb-chip-text: #bbf7d0;
    --wb-chip-bg: rgba(74, 222, 128, 0.16);
    --wb-link: #86efac;
}
.warning-banner-title {
    color: var(--wb-title);
    font-weight: 700;
    font-size: 1.1rem;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
}
.warning-banner-grid {
    display: flex;
    gap: 15px;
    flex-wrap: wrap;
}
.warning-banner-item {
    flex: 1;
    min-width: 240px;
    background: var(--wb-card-bg);
    padding: 12px;
    border-radius: 8px;
    border: 1px solid var(--wb-card-border);
}
.warning-banner-item strong {
    color: var(--wb-card-heading);
    display: block;
    margin-bottom: 4px;
    font-size: 0.95rem;
}
.warning-banner-content {
    color: var(--wb-text);
    font-size: 0.9rem;
    line-height: 1.5;
}
.warning-banner-item .warning-banner-content {
    color: var(--wb-card-text);
}
.warning-banner-content b {
    color: var(--wb-chip-text);
    background: var(--wb-chip-bg);
    padding: 1px 4px;
    border-radius: 4px;
}
.warning-banner code {
    font-family: var(--font-mono);
    font-size: 0.85em;
    color: var(--wb-chip-text);
    background: var(--wb-chip-bg);
    border: none;
    padding: 1px 5px;
    border-radius: 4px;
}
.warning-banner a {
    color: var(--wb-link);
    text-decoration: underline;
    text-underline-offset: 2px;
    overflow-wrap: anywhere;
}
.warning-banner-tip {
    margin-top: 12px;
    padding-top: 8px;
    border-top: 1px dashed var(--wb-divider);
    font-size: 0.85rem;
    line-height: 1.5;
    color: var(--wb-tip-text);
}
.warning-banner-tip b {
    color: var(--wb-tip-label);
}
.script-box textarea {
    font-family: 'Inter', sans-serif;
    line-height: 1.6;
}
.speaker-table {
    margin-top: 10px;
}
"""

head_html = """
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🦜</text></svg>">
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
