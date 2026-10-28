# 🎯 Hướng dẫn sử dụng Custom Model (LoRA, GGUF, Finetune)

## 📖 Giới thiệu

EveryVideoTTS hỗ trợ tải và sử dụng các mô hình tùy chỉnh từ HuggingFace hoặc đường dẫn cục bộ (Local Path), bao gồm:

1.  **LoRA Adapters**: Model fine-tune bằng phương pháp LoRA. (Hỗ trợ tăng tốc với **LMDeploy**!)
2.  **Custom Finetune Models**: Model fine-tune đầy đủ (Full Finetune) dựa trên VieNeu-TTS.
3.  **GGUF Quantized Models**: Model lượng tử hóa GGUF (chạy trên CPU/llama.cpp).

---

## 📌 Mục lục

- [🚀 Cách sử dụng LoRA Adapter (với LMDeploy)](#-cách-sử-dụng-lora-adapter-với-lmdeploy)
- [📦 Cách sử dụng GGUF Model (CPU)](#-cách-sử-dụng-gguf-model-cpu)
- [🔧 Khắc phục sự cố](#-khắc-phục-sự-cố)
- [💡 Tips & Lưu ý](#-tips--lưu-ý)

---

## 🚀 Cách sử dụng LoRA Adapter (với LMDeploy)

Đây là cách tối ưu nhất để chạy giọng fine-tune với tốc độ cao.

### Bước 1: Cấu hình Model
1. Trong khung **Cấu hình model** (đầu trang), ở ô **Model**, chọn **`Custom Model`**.
   - Nếu khung đang thu gọn (đã có model khác), bấm vào thanh **Model: … · bấm để đổi** để mở lại.
2. Các ô nhập cho model tuỳ chỉnh sẽ hiện ra bên dưới.
3. **Model ID**: Nhập Repo ID trên HuggingFace (hoặc đường dẫn folder local).
   - Ví dụ: `pnnbao-ump/VieNeu-TTS-0.3B-lora-ngoc-huyen`
4. **HF token** (tuỳ chọn): Nhập HuggingFace Access Token nếu repo là **Private**.
5. **Base model cho LoRA**: Chọn Base Model tương ứng mà LoRA đã được train trên đó (ô này chỉ hiện khi Model ID có chữ `lora`).
   - *Mẹo*: Hệ thống thường tự động phát hiện (ví dụ tên có "0.3" sẽ chọn bản 0.3B).
6. **Tăng tốc bằng LMDeploy**: **NÊN TICK** để kích hoạt tăng tốc (chỉ có trên GPU NVIDIA).

### Bước 2: Tải Model
1. Bấm nút **Tải model** (nút đổi thành *Đang tải…* trong lúc nạp; badge trên thanh tiêu đề chuyển sang *Sẵn sàng* khi xong).
2. Hệ thống sẽ tự động:
   - Tải LoRA Adapter và Base Model.
   - **Merge** (gộp) chúng lại với nhau (sử dụng GPU nếu có để tăng tốc).
   - Lưu model đã merge vào bộ nhớ đệm (`merged_models_cache/`).
   - Load model đã optimization bằng **LMDeploy**.
3. *Lưu ý*: Quá trình Merge chỉ chạy **một lần đầu tiên**. Lần sau sẽ load cực nhanh từ cache.

### Bước 3: Tạo giọng nói
1. Sau khi tải xong, vào tab **Đọc văn bản**, mục **Giọng đọc** → **Giọng có sẵn**, chọn giọng trong danh sách (lấy từ `voices.json` của repo).
   - *Lưu ý*: Mục **Clone giọng** (tải audio mẫu + nhập nội dung audio mẫu) hiện chỉ mở với model **v3** và **VieNeu-TTS-v2 (GPU)**; với `Custom Model` hãy dùng giọng có sẵn của repo.
2. Nhập văn bản cần đọc vào ô **Văn bản** và bấm **Tạo giọng nói**. Tiến độ và kết quả hiện ở khung **Kết quả** bên phải.

---

## 📦 Cách sử dụng GGUF Model (CPU)

Dành cho máy không có GPU NVIDIA hoặc muốn chạy nhẹ nhàng trên CPU.

1. Trong khung **Cấu hình model**, ở ô **Model**, chọn **`Custom Model`**.
2. **Model ID**: Nhập Repo ID chứa "gguf" trong tên hoặc file.
   - Ví dụ: `pnnbao-ump/VieNeu-TTS-0.3B-q4-gguf` (hoặc repo custom của bạn).
3. Hệ thống sẽ tự động nhận diện từ khóa "gguf" và chuyển sang backend **llama-cpp** (Standard).
4. Các bước tiếp theo tương tự như trên.

---

## 🔧 Khắc phục sự cố

### 1. Lỗi "LMDeploy Init Error" hoặc model không load được
- **Nguyên nhân**: Có thể do thiếu file tokenizer hoặc config trong quá trình merge.
- **Cách khắc phục**:
  - Xóa folder cache của model đó trong thư mục `merged_models_cache/`.
  - Thử tải lại để hệ thống merge lại từ đầu.

### 2. Tiếng nói bị rè hoặc không giống giọng mẫu
- Nếu dùng clone giọng: đảm bảo **Audio giọng mẫu** và **Nội dung của audio mẫu** khớp nhau 100%.
- Kiểm tra xem bạn đã chọn đúng **Base Model** chưa? (LoRA train trên 0.3B không thể chạy trên base 0.5B và ngược lại).

### 3. Model Private không tải được
- Hãy chắc chắn bạn đã nhập đúng token có quyền `read` vào ô **HF token**.

---

## 💡 Tips & Lưu ý

1.  **Cache**: Các model LoRA sau khi merge sẽ chiếm dụng dung lượng ổ cứng trong `merged_models_cache`. Bạn có thể xóa thủ công các folder trong đó nếu muốn giải phóng bộ nhớ.
2.  **Tự động hóa**: Khi Model ID có chữ `lora`, ô **Base model cho LoRA** tự hiện và chọn sẵn base phù hợp (tên có "0.3" → bản 0.3B, còn lại → VieNeu-TTS). Bạn vẫn nên kiểm tra lại trước khi bấm **Tải model**.
3.  **Tốc độ**: Với LMDeploy, tốc độ sinh giọng sẽ nhanh gấp nhiều lần so với backend cũ. Hãy tận dụng GPU!
