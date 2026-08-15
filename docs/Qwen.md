# Kiến trúc & Phân tích Kỹ thuật Lucky Patcher PC (LP-PC)

Tài liệu này tổng hợp các nguyên lý thiết kế cốt lõi dựa trên reverse engineering Lucky Patcher gốc, định hướng phát triển cho phiên bản PC.

## 1. Triết lý Thiết kế GUI: "Form Follows Function"

Giao diện LP-PC không phải là trang trí, mà là **bản đồ chức năng (functional blueprint)**. Mỗi thành phần UI ánh xạ trực tiếp đến một module kỹ thuật bên dưới.

### 1.1. Ba Vùng Chức Năng Cốt lõi

| Vùng UI | Thành phần | Ánh xạ Kỹ thuật | Mục đích Workflow |
| :--- | :--- | :--- | :--- |
| **1. Danh sách Ứng dụng** | App List + Color Tags | `scanner.app_classifier`, `scanner.ad_scanner` | **Bước 1: Nhận diện mục tiêu.** Heatmap bảo mật (Xanh: Dễ, Vàng: TB, Đỏ: Khó). |
| **2. Menu Ngữ cảnh** | Context Menu (Hierarchical) | `patcher.*`, `pipelines.*` | **Bước 2: Lựa chọn tấn công.** Phân nhóm: Tools, Permissions, Backup, Info. |
| **3. Bảng điều khiển Hệ thống** | System Dashboard / Toolbox | `core.device_bridge`, `patcher.ws_proxy_server` | **Bước 0 & 3: Môi trường.** Quản lý LSPosed, Proxy IAP, Signature System. |

### 1.2. Hệ thống Mã hóa Màu (Heatmap)
Các nhãn màu trong danh sách ứng dụng không ngẫu nhiên, chúng là kết quả của quá trình quét tĩnh (`classes.dex` & `AndroidManifest.xml`):
*   🟢 **Xanh lá**: Phát hiện License Verification (LVL) có thể bypass.
*   🟡 **Vàng**: Phát hiện In-App Purchase (IAP) hoặc Quảng cáo (Ads).
*   🔴 **Đỏ**: Bảo vệ mạnh (Play Integrity, SafetyNet, Root Detection).
*   ⚪ **Xám**: Ứng dụng hệ thống hoặc không thể can thiệp.

## 2. Luồng Dữ liệu Nội bộ (Internal Data Flow)

Workflow của LP-PC tuân thủ chu trình 4 giai đoạn khép kín:

### Giai đoạn 1: Thu thập Thông tin (Information Gathering)
*   **Trigger**: Khởi động app hoặc Pull-to-refresh.
*   **Hành động**:
    *   Quét `/data/app/`, `/system/app/`.
    *   Giải nén `AndroidManifest.xml` (lấy package name, permissions).
    *   Phân tích `classes.dex` (tìm signatures: `com.google.android.vending.licensing`, `com.google.android.gms.ads`).
*   **Output**: Hồ sơ bảo mật (Security Profile) cho từng app → Cập nhật UI App List.

### Giai đoạn 2: Xử lý & Ra quyết định (Processing & Decision Making)
*   **Trigger**: User chọn action từ Menu Ngữ cảnh.
*   **Hành động**:
    *   Chuyển đổi ý định user ("Crack app này") thành chỉ thị kỹ thuật.
    *   Lựa chọn template patch phù hợp (ví dụ: "Support patch for InApp emulation").
    *   Cấu hình tham số (Redirect server, Always return LICENSED).
*   **Output**: Tập hợp các lệnh patching/hooking cụ thể.

### Giai đoạn 3: Thực thi (Execution)
*   **Trigger**: User nhấn "Apply" hoặc "Start".
*   **Hành động**:
    *   **Static**: Decompile → Patch Smali → Recompile → Resign (Background process).
    *   **Dynamic**: Gửi IPC message tới LSPosed Module để kích hoạt hook runtime.
*   **UI Feedback**: Thanh tiến trình (Progress Bar) và Log cuộn thời gian thực.

### Giai đoạn 4: Xác minh & Phản hồi (Verification & Feedback)
*   **Trigger**: Hoàn tất thực thi.
*   **Hành động**:
    *   Tự động kiểm tra trạng thái (ví dụ: thử launch app, check logcat).
    *   Cập nhật lại nhãn màu và trạng thái trong App List.
*   **Output**: Thông báo Success/Failure kèm gợi ý khắc phục.

## 3. Chi tiết Các Màn hình Chức năng

### 3.1. Custom Patch Creator (Dành cho Expert)
*   **UI**: Danh sách mẫu patch (Templates) + Checkbox tùy chọn + Smali Editor.
*   **Logic**: Engine tìm-kiếm-và-thay-thế (Search-and-Replace) trên mã Smali.
*   **Tính năng**:
    *   Templates: Google License, Amazon License, Samsung License.
    *   Options: "Redirect to custom server", "Always return LICENSED".
    *   Manual Mode: Smali Editor với syntax highlighting.

### 3.2. In-App Purchase (IAP) Manager
*   **UI**: Split view (Emulated IAP Server | Product List).
*   **Logic**: Man-in-the-Middle proxy server chặn Google Billing API.
*   **Hoạt động**:
    *   Start/Stop Local Server (lắng nghe cổng cụ thể).
    *   Danh sách SKU: Cho phép "mua" vĩnh viễn hoặc set giá $0.
    *   Trả về receipt hợp lệ cho ứng dụng mà không cần mạng.

### 3.3. System Module Configuration (Toolbox)
*   **UI**: Danh sách modules (Toggle Switch) + Form cấu hình chi tiết.
*   **Logic**: Injection vào Android Runtime qua LSPosed/Xposed.
*   **Modules**:
    *   Disable Signature Verification.
    *   Hide Root (Magisk/Zygisk hide).
    *   Spoof Device Properties (`Build.FINGERPRINT`, `Build.MODEL`).
    *   Tools: Rebuild Dalvik Cache, Clean Up System.

## 4. Chiến lược Phòng thủ & Đạo đức

*   **Minh bạch**: Hiển thị chính xác những thay đổi trước khi apply (No black-box).
*   **Phân tầng**: UI đơn giản cho người mới, nhưng vẫn mở quyền truy cập sâu (Smali, Hooks) cho chuyên gia.
*   **Mục đích**: Nghiên cứu bảo mật, kiểm thử ứng dụng (Pen-testing), và tùy biến cá nhân. Không khuyến khích vi phạm bản quyền thương mại.

---
*Tài liệu này phục vụ làm kim chỉ nam cho đội ngũ phát triển LP-PC đảm bảo tính tương thích và tối ưu hiệu năng.*
