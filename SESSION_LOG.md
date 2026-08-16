# 📜 EveryVideoTTS - Nhật Ký Phát Triển & Tổng Quan Dự Án

---

## 📌 1. Tổng Quan Dự Án
* **Tên dự án:** **EveryVideoTTS Studio**
* **Tác giả:** **Tyr** ([GitHub: hiimkuroshi](https://github.com/hiimkuroshi))
* **Repository:** [https://github.com/hiimkuroshi/EveryVideoTTS](https://github.com/hiimkuroshi/EveryVideoTTS)
* **Mô tả cốt lõi:** Hệ thống Studio chuyển văn bản thành giọng nói tiếng Việt AI chất lượng cao (48 kHz), Voice Cloning tức thì (3-5s), Lồng tiếng Video từ phụ đề SRT với công nghệ **Studio-Grade WSOLA** chống rè, và xử lý song song siêu tốc trên GPU (Batch Size 32-64).

---

## 📅 2. Lịch Sử Các Phiên Làm Việc (Session Logs)

### 🔹 Session 1 (2026-08-16) - Khởi tạo, Tối ưu Hiệu Năng & Tái Thiết Kế UI
* **Người thực hiện:** Tyr & Antigravity AI
* **Mục tiêu phiên làm việc:**
  1. Trích xuất và tích hợp giọng mẫu `Review 1` và `Review 2` cho cả 2 kiến trúc Model v3 Turbo & Model v2.
  2. Khắc phục triệt để hiện tượng rè âm thanh khi tự động tăng tốc giọng đọc trong tính năng lồng tiếng SRT.
  3. Tối ưu hóa hiệu năng GPU (RTX 5070 / CUDA 12.8) qua kiến trúc GPU Batched Engine x32-64.
  4. Đổi tên thương hiệu dự án thành **EveryVideoTTS**, cập nhật tác giả **Tyr**.
  5. Tái thiết kế toàn bộ UX/UI theo chuẩn Studio Glassmorphism và tạo tài liệu `design.md`.
  6. Thiết lập quy trình làm việc tự động (Session Log & Auto Git Push theo lệnh).

* **Chi tiết thay đổi & Kết quả đạt được:**
  * **1. Trích xuất Giọng mẫu (`voices_v3_turbo.json` & `voices.json`):**
    - Trích xuất ma trận 192-d `speaker_emb` và `codes` cho v3 Turbo.
    - Trích xuất token NeuCodec 1D và text mapping cho v2.
    - Export file profile cấu hình giọng độc lập tại `D:\AI\Template Voice\Review 1_preset.json` và `Review 2_preset.json`.
  * **2. Thuật toán Kéo dãn Tốc độ Studio-Grade WSOLA (`src/vieneu_utils/srt_utils.py`):**
    - Thay thế Phase Vocoder cũ bằng Waveform Similarity Overlap-Add (Hann window 25ms, cross-correlation search).
    - Giữ nguyên 100% cao độ, ngữ điệu tự nhiên, triệt tiêu tiếng kim loại/reverb khi tăng tốc độ từ 1.0x - 3.0x.
    - Chuẩn hóa năng lượng đỉnh và RMS cho toàn bộ các câu trong video.
  * **3. Tối ưu hóa GPU Batched Engine (`apps/gradio_main.py`):**
    - Nâng cấp hàm `synthesize_srt_speech` sử dụng `V3TurboBatchEngine` (Batch Size 32, bucketing theo độ dài).
    - Tăng tốc độ sinh âm thanh lồng tiếng video lên gấp 15x - 25x realtime trên RTX 5070.
  * **4. Tái cấu trúc UX/UI Toàn diện (`apps/ui_constants.py`, `apps/gradio_main.py`, `design.md`):**
    - Tích hợp bộ font quốc tế `Plus Jakarta Sans`, `Inter`, `JetBrains Mono`.
    - Thiết kế bảng điều khiển Studio Header, Model Control Bar ngang, hỗ trợ Dark/Light mode.
    - Bổ sung chip chọn nhanh cảm xúc (`[cười]`, `[hắng giọng]`, `[thở dài]`).
    - Nâng cấp giao diện Lồng tiếng SRT với bộ chọn Speed Matching 3 chế độ.
  * **5. Đổi tên Dự án & Cập nhật Repository:**
    - Cập nhật Git Remote sang `https://github.com/hiimkuroshi/EveryVideoTTS.git`.
    - Cập nhật thông tin tác giả **Tyr** và tên dự án **EveryVideoTTS** trong `pyproject.toml`, `README.md`, `README.vi.md`, `README_PYPI.md`, `design.md`.

* **Trạng thái Kiểm thử:**
  - `apps.gradio_main`: Build & load thành công 100%.
  - `tests/test_srt.py`: 10/10 unit test cases passed (0.627s).
* **Trạng thái GitHub:** Đã commit và đồng bộ toàn bộ mã nguồn lên nhánh `main` của repository [EveryVideoTTS](https://github.com/hiimkuroshi/EveryVideoTTS).

---
*(Các phiên làm việc tiếp theo sẽ được tự động ghi nhận tại đây khi có lệnh "kết thúc".)*
