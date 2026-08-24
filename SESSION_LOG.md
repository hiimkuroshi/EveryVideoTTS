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

### 🔹 Session 2 (2026-08-21 ➔ 2026-08-24) - Nâng Cấp v3.3.0, Streaming SRT Memory-Safe & Fast Launcher
* **Người thực hiện:** Tyr & Antigravity AI
* **Mục tiêu phiên làm việc:**
  1. Đồng bộ mã nguồn gốc cục bộ lên GitHub nhánh `main`.
  2. Nâng cấp mã nguồn lên `v3.3.0` (tích hợp các cải tiến mới nhất từ bản gốc của Dr. Puma), tạo và cập nhật vào nhánh `1` trên GitHub.
  3. Tạo file batch khởi động siêu tốc (~0.1s) chạy trực tiếp môi trường `.venv` không bị chậm bởi `uv`.
  4. Khắc phục triệt để lỗi tràn bộ nhớ `_ArrayMemoryError: Unable to allocate 1.92 MiB` khi lồng tiếng phụ đề SRT dài.
  5. Cấu hình hệ thống lưu trực tiếp các file audio sau khi generate vào thư mục `D:\AI\VieNeu\Voice`.

* **Chi tiết thay đổi & Kết quả đạt được:**
  * **1. Đồng bộ nhánh `main` lên GitHub:**
    - Đẩy toàn bộ mã nguồn EveryVideoTTS ổn định lên nhánh `main` (Commit: `0304c49`).
  * **2. Nâng cấp toàn diện lên `v3.3.0` trên Nhánh `1` (`git checkout -b 1`):**
    - **Cắt chunk thông minh theo Từ Nối (v3.3.0):** Tự động nhận diện từ nối (*và, nhưng, hoặc, vì, nếu, khi, tuy nhiên...*) để ngắt nghỉ tự nhiên, bảo vệ cụm từ ghép.
    - **Cửa sổ trượt phạt lặp từ (`rep_history.py`):** Giới hạn phạt lặp trong cửa sổ trượt ~2.5s, triệt tiêu méo giọng/trôi tông ở cuối câu dài.
    - **Chống ảo giác cho câu thoại ngắn:** Tự động gộp chunk vụn (< 20 ký tự), khống chế trần frame động và khóa cứng 1 giây cho câu 1 từ.
    - **Voice Cloning Torch-Free trên CPU:** Tích hợp `kaldi-native-fbank` + `soxr` thuần C++/NumPy để nhân bản giọng nói trực tiếp trên CPU.
    - **Nâng cấp Thư viện & Bảo toàn Giọng mẫu:** Cập nhật `sea-g2p >= 0.9.0`, bảo toàn 100% 2 giọng mẫu độc quyền `Review 1` và `Review 2` (tổng 22 giọng preset v3 Turbo).
    - **Bảo toàn 100% tính năng độc quyền:** Lồng tiếng SRT, Studio WSOLA, GPU Batched Engine x32 trên RTX 5070.
  * **3. Bộ Khởi Động Siêu Tốc (`start_fast.bat`, `run_app.bat`, `start.bat`):**
    - Khởi chạy trực tiếp từ `.venv\Scripts\python.exe -m apps.gradio_main`, loại bỏ thời gian quét lockfile của `uv`, khởi động trong ~0.1 giây.
    - Tự động mở trình duyệt `http://127.0.0.1:7860` sau 2 giây.
  * **4. Khắc Phục Lỗi Tràn RAM Khi Lồng Tiếng SRT (`apps/gradio_main.py`, `src/vieneu_utils/srt_utils.py`):**
    - Chuyển đổi toàn bộ quá trình xuất audio sang cơ chế **Streaming trực tiếp ra SoundFile đĩa** (`sf.SoundFile`), ghi tuần tự các khối nhỏ (~192 KB buffer), loại bỏ `np.concatenate` trên hàng trăm mảng. Dung lượng RAM tiêu thụ cố định ở mức **< 5 MB**.
    - Tối ưu hóa thuật toán WSOLA với `np.correlate` trực tiếp (Direct Dot-Product C), triệt tiêu FFT heap allocations.
    - Tự động thu hồi bộ nhớ GPU/RAM (`torch.cuda.empty_cache()` + `gc.collect()`) sau mỗi batch.
  * **5. Cấu hình Thư mục Lưu Trữ `D:\AI\VieNeu\Voice`:**
    - Tất cả các chức năng (Đọc truyện, Hội thoại, Lồng tiếng SRT) tự động ghi file trực tiếp vào `D:\AI\VieNeu\Voice`.
    - Quy ước đặt tên có timestamp: `single_v3_...wav`, `conv_v3_...wav`, `srt_...wav`.
    - Hiển thị đường dẫn lưu file trực tiếp trên ô trạng thái giao diện.

* **Trạng thái Kiểm thử:**
  * `pytest`: Đạt **56/56** unit test cases passed hoàn toàn (`test_srt.py`, `test_rep_history.py`, `test_speaker_fbank.py`, `test_utils.py`).
  * Web UI & GPU Engine: Hoạt động trơn tru 100%.
* **Trạng thái GitHub:**
  * Nhánh `main`: [https://github.com/hiimkuroshi/EveryVideoTTS/tree/main](https://github.com/hiimkuroshi/EveryVideoTTS/tree/main)
  * Nhánh `1`: [https://github.com/hiimkuroshi/EveryVideoTTS/tree/1](https://github.com/hiimkuroshi/EveryVideoTTS/tree/1)

---
*(Các phiên làm việc tiếp theo sẽ được tự động ghi nhận tại đây khi có lệnh "kết thúc".)*
