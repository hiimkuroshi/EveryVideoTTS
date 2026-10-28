# 🎨 Thiết kế giao diện EveryVideoTTS Studio

Tài liệu mô tả hệ thống thiết kế và bố cục của web UI (`vieneu-web`, Gradio).
Mã nguồn liên quan:

| File | Vai trò |
| :--- | :--- |
| `apps/ui_constants.py` | Bảng màu (token sáng / tối), theme Gradio, toàn bộ CSS, script trong `<head>`, bản dịch chữ dựng sẵn của Gradio |
| `apps/ui_components.py` | Hàm dựng HTML: thanh tiêu đề, trạng thái model, thẻ tiến độ, tóm tắt SRT, gợi ý model |
| `apps/ui_utils.py` | `stream_with_status`: chuyển luồng `(audio, trạng thái)` của backend thành thẻ tiến độ + ETA |
| `apps/gradio_main.py` | Bố cục và nối sự kiện (bản chính) |
| `apps/gradio_xpu.py` | Bản Intel Arc, dùng chung theme/CSS/thành phần |

---

## 1. Nguyên tắc

* **Studio tối làm mặc định**, có chế độ sáng đầy đủ. Lựa chọn được nhớ trong trình duyệt (`localStorage`), có thể ép bằng `?__theme=light|dark`.
* **Nội dung trước, cấu hình sau:** khung model tự thu gọn khi model sẵn sàng; tuỳ chọn ít dùng nằm trong mục thu gọn (*Tinh chỉnh nâng cao*, *Gợi ý chọn model*, *Nhập từ PDF*).
* **Một nguồn sự thật cho màu sắc:** mọi màu nằm trong hai bảng `LIGHT` / `DARK`, sinh ra cả biến theme Gradio lẫn biến CSS `--evt-*`.
* **Trạng thái luôn nhìn thấy:** thanh tiêu đề cho biết model nào đang dùng; khung Kết quả cho biết đang làm gì, tới đâu, còn bao lâu.
* **Tiếng Việt toàn bộ**, kể cả chữ dựng sẵn của Gradio (khung tải file, ghi âm, footer) qua `gr.I18n`.

---

## 2. Token

### Màu

| Token | Sáng | Tối | Dùng cho |
| :--- | :--- | :--- | :--- |
| `bg` | `#F3F4F8` | `#0B0D12` | Nền trang (kèm quầng sáng tím rất nhẹ ở đỉnh) |
| `surface` | `#FFFFFF` | `#12151C` | Thẻ (card) |
| `surface-2` | `#F7F8FB` | `#181C25` | Ô nhập, khung phụ trong thẻ |
| `surface-3` | `#EDEFF5` | `#202531` | Hover, chip, code |
| `border` / `border-strong` | `#E2E5ED` / `#CBD1DD` | `#242A36` / `#353D4E` | Viền |
| `text` / `text-2` / `text-3` | `#141824` / `#465064` / `#687186` | `#E8EBF2` / `#A7AFC0` / `#7F889C` | Chữ chính / phụ / chú thích (đều ≥ 4.5:1 trên nền thẻ) |
| `accent` | `#6246EA` | `#6E58F6` | Nút chính, tab đang chọn, viền focus |
| `success` / `warning` / `danger` | `#0B8A5F` / `#A16207` / `#D12E3E` | `#3DD9A0` / `#F5C04A` / `#F87C7C` | Hoàn tất / cần chú ý / lỗi, nút Dừng |

Waveform dùng màu cố định `#8A93A8` (chưa phát) và `#7C66FF` (đã phát), đọc được trên cả hai nền.

### Chữ

* **Be Vietnam Pro** (400–700) — font thiết kế cho tiếng Việt, dấu rõ ở mọi cỡ.
* **JetBrains Mono** — nội dung SRT, mốc thời gian, tag cảm xúc (tắt ligature để `-->` hiển thị đúng ký tự).
* Cỡ: chữ thường 15px, ô văn bản chính 15.5px / line-height 1.65, nhãn 13.5px đậm, chú thích 13px, tiêu đề mục 15px, nút chính 16px.

### Hình khối

* Bo góc: thẻ 16px, ô nhập 10px, nút 10–11px, chip tròn.
* Khoảng cách: 16px giữa các khối; thẻ có padding 18–20px (14px trên điện thoại).

---

## 3. Bố cục

```
┌──────────────────────────────────────────────────────────────┐
│ [logo] EveryVideoTTS Studio      ● v3-Turbo (int8) · Sẵn sàng │  Thanh tiêu đề
├──────────────────────────────────────────────────────────────┤
│ Cấu hình model  (tự thu gọn khi sẵn sàng)                  ⌃ │
│  Model [▾]   Thiết bị (Auto|CPU|CUDA)   [ Tải model ]        │
│  ✓ Model đã sẵn sàng · Model · Thiết bị · Backend · Codec    │
│  › Gợi ý chọn model                                          │
├────────────────────────────────────┬─────────────────────────┤
│ Đọc văn bản | Hội thoại | SRT      │ Kết quả   (dính khi cuộn)│
│ ...nội dung tab...                 │ thẻ trạng thái / tiến độ │
│ [        Nút hành động        ]    │ trình phát audio         │
│ › Tinh chỉnh nâng cao              │ [Tải xuống WAV] [Dừng]   │
└────────────────────────────────────┴─────────────────────────┘
```

* Desktop: hai cột 7 : 5, tối đa 1360px; khung Kết quả dính (sticky) khi cuộn.
* ≤ 1024px: Kết quả xuống dưới, bấm nút tạo sẽ tự cuộn tới Kết quả.
* ≤ 768px: một cột, lề 10–12px, thanh tiêu đề gọn, tab nhỏ lại để cả 3 tab vừa màn hình.

---

## 4. Thành phần

### Thanh tiêu đề
Logo (sóng âm trên nền gradient tím), tên sản phẩm, mô tả ngắn, **badge trạng thái model** (xám: chưa tải · vàng nhấp nháy: đang tải · xanh: sẵn sàng · đỏ: lỗi), nút GitHub và nút đổi sáng/tối.

### Khung Cấu hình model
* Nút *Tải model* đổi thành *Đang tải…* trong lúc nạp.
* Thẻ trạng thái: biểu tượng + tiêu đề + các chip thông tin (Model, Thiết bị, Backend, Codec); cảnh báo (ví dụ LMDeploy không bật được) hiện thành ghi chú vàng.
* *Codec* tự chọn theo model nên không hiển thị.
* *Gợi ý chọn model*: 3 thẻ (máy CPU / máy GPU NVIDIA / model tuỳ chỉnh) + ghi chú về clone giọng, tag cảm xúc và nơi báo lỗi.

### Tab Đọc văn bản
* Ô văn bản có bộ đếm ký tự, tự giãn theo nội dung.
* **Chèn cảm xúc** (chỉ v3): chip `[cười]` `[hắng giọng]` `[thở dài]` chèn đúng vị trí con trỏ.
* *Nhập văn bản từ file PDF* (thu gọn).
* **Giọng đọc**: điều khiển phân đoạn *Giọng có sẵn | Clone giọng*.
* Nút **Tạo giọng nói**; khi chưa có model, dòng gợi ý bên dưới nhắc tải model.

### Tab Hội thoại
Kịch bản `Tên: Lời thoại` → **Quét nhân vật** → bảng **Phân vai** (Nhân vật | Giọng đọc, tối đa 8) → khoảng lặng giữa các lượt → **Tạo hội thoại**. Tab chỉ hiện khi model hỗ trợ (v2, v3).

### Tab Lồng tiếng SRT — 3 bước đánh số
1. **Phụ đề**: kéo thả file hoặc dán nội dung (font mono) → **Phân tích phụ đề** → thẻ tóm tắt: số câu, độ dài timeline, số nhân vật, 3 câu đầu kèm mốc thời gian.
2. **Giọng đọc**: giọng chính + **Phân vai theo nhân vật** (tự mở khi phát hiện nhân vật).
3. **Đồng bộ thời gian**: *Khớp mốc thời gian / Đọc nối tiếp*, độ trễ đầu, chế độ khớp tốc độ (WSOLA), tốc độ tối đa.

### Khung Kết quả
* **Trống**: biểu tượng sóng âm + hướng dẫn ngắn.
* **Đang xử lý**: badge nhấp nháy, bước hiện tại (`Đoạn 3/12`, `Câu 4/20`, `Lô 2/5`), thanh tiến độ (chạy vô định khi không biết tổng), phần trăm và thời gian còn lại ước tính.
* **Hoàn tất**: badge xanh + các ô số liệu đọc từ thông báo của backend (thời gian xử lý, tốc độ so với realtime, số câu, độ dài audio…) + ghi chú (ví dụ số câu đã tự tăng tốc).
* **Lỗi / Đã dừng / Cần kiểm tra**: badge đỏ / vàng kèm thông báo.
* Trình phát chỉ hiện khi có audio, tự phát; nút **Tải xuống WAV** hiện khi xong; nút **Dừng** chỉ hiện trong lúc chạy. Trong lúc chạy các nút tạo bị khoá để tránh chạy chồng.

---

## 5. Ghi chú kỹ thuật

* Gradio tự thêm tiền tố `.gradio-container … .contain` vào mọi selector **bên trong `@media`**, nên rule trong media query chỉ nhắm được phần tử bên trong app. Lề ngoài dùng `clamp()` thay cho media query.
* Gradio đo các bản sao ẩn của nút tab để quyết định tab nào bị đẩy vào menu "···"; CSS cỡ chữ/padding của tab phải áp cho cả bản sao (`.tab-container button`).
* Một dict `gr.update(...)` không được dùng chung cho nhiều output: Gradio `pop("value")` khi áp dụng, output thứ hai sẽ mất giá trị.
* Sau khi tải lại trang, `restore_ui_state_ui` dựng lại danh sách giọng, tab Hội thoại/Clone và model đang chọn từ trạng thái phía server.
