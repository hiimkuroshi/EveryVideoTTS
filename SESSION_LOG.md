# 📜 EveryVideoTTS - Nhật Ký Phát Triển & Tổng Quan Dự Án

---

## 📌 1. Tổng Quan Dự Án
* **Tên dự án:** **EveryVideoTTS Studio**
* **Tác giả:** **Tyr** ([GitHub: hiimkuroshi](https://github.com/hiimkuroshi))
* **Repository:** [https://github.com/hiimkuroshi/EveryVideoTTS](https://github.com/hiimkuroshi/EveryVideoTTS)
* **Mô tả cốt lõi:** Hệ thống Studio chuyển văn bản thành giọng nói tiếng Việt AI chất lượng cao (48 kHz), Voice Cloning tức thì (3-5s), Lồng tiếng Video từ phụ đề SRT với công nghệ **Studio-Grade WSOLA** chống rè, và xử lý song song siêu tốc trên GPU (Batch Size 32-64).

---

## 📅 2. Lịch Sử Các Phiên Làm Việc (Session Logs)

### 🔹 Session 1 (2026-08-16) - Khởi tạo & Tối ưu hóa Toàn diện
* **Các tính năng đã phát triển:**
  1. **Tính năng Lồng tiếng SRT (SRT Video Dubbing)**:
     - Tự động parse và phân tích phụ đề SRT.
     - Hỗ trợ căn chỉnh mốc thời gian (Strict Sync & Sequential).
     - Phân vai đa nhân vật tự động từ cú pháp `Tên: Lời thoại`.
  2. **Thuật toán Khớp Tốc độ Studio-Grade WSOLA (Time-Domain)**:
     - Khắc phục triệt để hiện tượng vỡ tiếng, rè kim loại của Phase Vocoder cũ.
     - Đồng nhất 100% âm lượng và độ động giữa các câu tăng tốc và câu bình thường.
  3. **Tăng tốc GPU Batched Engine x32**:
     - Tối ưu hóa cho card đồ họa NVIDIA GeForce RTX 5070.
     - Xử lý song song 32-64 câu phụ đề cùng lúc, tăng tốc độ gấp 15x-25x realtime.
  4. **Tích hợp Giọng Mẫu Mới**:
     - Trích xuất và thêm các giọng: `Review 1` và `Review 2` cho cả **Model v3 Turbo** và **Model v2**.
  5. **Tái cấu trúc UX/UI Hiện Đại**:
     - Thiết kế giao diện Glassmorphism Studio với typography chuẩn quốc tế.
     - Đổi tên dự án thành **EveryVideoTTS**, cập nhật thông tin tác giả **Tyr**.
* **Trạng thái GitHub:** Đã đồng bộ lên commit mới nhất trên nhánh `main`.

---
*(Các phiên làm việc tiếp theo sẽ được cập nhật tự động tại đây khi có lệnh "kết thúc".)*
