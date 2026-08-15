# QWEN.md — Command & Environment Execution Rules

Mục tiêu file này: giúp agent dùng shell/command/env hiệu quả, ít lỗi,
ít lặp lại, giống hành vi của Claude Code. Áp dụng cho MỌI task có
chạy lệnh, không chỉ coding task.

---

## 1. Nguyên tắc chung khi chạy command

- **Không đoán, luôn xác minh trước.** Trước khi sửa/xoá file, chạy
  lệnh kiểm tra trạng thái hiện tại (`cat`, `ls`, `git status`, `grep`)
  thay vì giả định nội dung dựa trên trí nhớ.
- **1 lệnh = 1 mục đích rõ ràng.** Không gộp nhiều thao tác không liên
  quan vào một lệnh dài khó debug.
- **Luôn dùng flag non-interactive.** Không chạy lệnh chờ input thủ
  công (vd: thiếu `-y`, `--yes`, `-f` khi cần) — agent sẽ bị treo.
  Ví dụ: `pip install -y`, `apt-get install -y`, `git merge --no-edit`.
- **Ưu tiên lệnh idempotent.** Chạy lại 2 lần không gây lỗi/side effect
  kép (vd: `mkdir -p` thay vì `mkdir`, `git add -A` thay vì add từng
  file thủ công nhiều lần).
- **Không chạy lệnh phá hoại mà không xác nhận:** `rm -rf`,
  `git push --force`, `DROP TABLE`, migrate DB, ghi đè file cấu hình
  production. Luôn hỏi người dùng trước, hoặc dry-run trước
  (`--dry-run`, `git diff` trước khi apply).

---

## 2. Nhận diện môi trường trước khi hành động

Trước khi chạy bất kỳ lệnh cài đặt/build nào, xác định:

```bash
# OS / shell
uname -a 2>/dev/null || ver
echo $SHELL

# Ngôn ngữ / runtime version đang có
python --version; python3 --version
node --version; npm --version

# Có virtualenv/venv đang active không
echo $VIRTUAL_ENV

# Package manager nào đang dùng trong project
ls | grep -E "requirements.txt|pyproject.toml|package.json|Pipfile|poetry.lock"
```

Quy tắc:
- Nếu có `venv`/`.venv` trong project → activate trước khi cài package,
  không cài global bừa bãi.
- Nếu có `poetry.lock`/`pnpm-lock.yaml`/`yarn.lock` → dùng đúng package
  manager đó, không trộn (vd: đừng `npm install` khi project dùng `pnpm`).
- Không cài lại package đã có trong lockfile mà không kiểm tra version
  conflict trước.

---

## 3. Thứ tự thao tác chuẩn cho mỗi task

1. **Khảo sát** — đọc file/dir liên quan (`ls`, `find`, `grep -r`, `cat`)
   trước khi sửa gì.
2. **Plan ngắn** — nếu task >1 bước, liệt kê plan 3-5 bước trước khi
   gọi lệnh đầu tiên.
3. **Thực thi từng bước nhỏ** — mỗi thay đổi lớn nên tách thành các
   lệnh/edit nhỏ, dễ rollback.
4. **Xác minh ngay sau khi thay đổi** — chạy lệnh kiểm tra kết quả
   (test, lint, build, `git diff`) trước khi coi bước đó là xong.
5. **Tổng kết** — báo cáo ngắn gọn: đã làm gì, lệnh nào chạy, kết quả
   ra sao, bước tiếp theo (nếu có).

Không được báo "hoàn thành" nếu chưa chạy bước xác minh (test/build/lint).

---

## 4. Xử lý output hiệu quả

- **Trim output dài.** Không dump toàn bộ log hàng nghìn dòng vào
  context. Dùng `| tail -n 50`, `| head -n 50`, `| grep -i error`,
  hoặc redirect ra file rồi đọc phần cần thiết.
- **Tách stdout/stderr khi debug lỗi:**
  ```bash
  command > out.log 2> err.log; echo "exit: $?"
  ```
- **Luôn kiểm tra exit code**, không chỉ nhìn text output:
  ```bash
  command; echo "EXIT_CODE=$?"
  ```
- Với lệnh chạy lâu (build, train, crawl) → chạy nền + poll thay vì
  block toàn bộ session:
  ```bash
  nohup command > log.txt 2>&1 &
  echo $!   # lưu PID để kiểm tra sau
  ```

---

## 5. Song song hoá khi có thể

- Các lệnh **độc lập, không phụ thuộc nhau** (vd: chạy test module A
  và module B, hoặc lint nhiều file riêng biệt) → gọi song song thay
  vì tuần tự, để giảm thời gian chờ.
- Các lệnh **có phụ thuộc** (vd: `npm install` phải xong trước
  `npm run build`) → luôn tuần tự, không parallelize.
- Không chạy song song 2 lệnh cùng ghi vào 1 file/resource (race
  condition).

---

## 6. Quy tắc riêng cho Git

```bash
git status                # luôn kiểm tra trước khi commit
git diff                  # xem lại thay đổi trước khi add
git add -A
git commit -m "type: mô tả ngắn gọn, đúng scope thay đổi"
```

- Không `git push --force` vào branch chung (main/master/dev) trừ khi
  được yêu cầu tường minh.
- Commit message theo convention: `fix:`, `feat:`, `refactor:`,
  `chore:`, `docs:` — mô tả đúng những gì thực sự đổi, không generic
  kiểu "update code".
- Trước khi tạo PR: chạy lại test/build 1 lần cuối để chắc chắn không
  break gì.

---

## 7. Xử lý lỗi & retry

- Khi 1 lệnh fail: đọc kỹ error message trước khi thử lại, không lặp
  lại y hệt lệnh cũ hy vọng ra kết quả khác.
- Tối đa **2 lần retry** cho cùng 1 hướng tiếp cận. Nếu vẫn fail →
  đổi hướng (tìm nguyên nhân gốc: sai path, thiếu dependency, sai
  version, permission) thay vì lặp vô hạn.
- Nếu không chắc nguyên nhân lỗi → chạy lệnh chẩn đoán trước khi sửa
  mù (`which`, `python -c "import X"`, `pip show`, `node -e`).

---

## 8. Giới hạn & an toàn

- Không đọc/ghi ngoài phạm vi project trừ khi được yêu cầu rõ.
- Không expose secrets trong log/output (API key, token, password) —
  không `cat .env` ra output nếu không cần thiết, mask nếu phải hiển thị.
- Không tự ý thay đổi cấu hình hệ thống ngoài phạm vi project
  (system Python, global npm packages) trừ khi được yêu cầu.

---

## 9. Workflow tổng thể — mô phỏng cách Claude vận hành

Đây là vòng lặp chuẩn mà agent PHẢI theo cho mọi task không tầm thường
(>1 bước). Không nhảy thẳng vào code khi chưa qua các bước trước.

### Bước 1 — Hiểu task
- Đọc kỹ yêu cầu, xác định rõ: mục tiêu cuối cùng là gì, phạm vi ảnh
  hưởng (file/module nào), có ràng buộc gì (không đổi API, giữ
  performance, tương thích version...).
- Nếu yêu cầu mơ hồ và có thể hiểu theo nhiều hướng khác nhau dẫn đến
  kết quả khác nhau → hỏi lại 1 câu ngắn gọn. Nếu chỉ thiếu chi tiết
  nhỏ không ảnh hưởng hướng đi → tự chọn phương án hợp lý nhất, nêu rõ
  giả định, rồi làm luôn.

### Bước 2 — Khảo sát (Explore)
- Trước khi viết bất kỳ dòng code nào: đọc file liên quan, hiểu cấu
  trúc hiện có, convention đang dùng trong project.
- Dùng `grep -r`, `find`, `ls` để định vị đúng chỗ cần sửa thay vì
  đoán đường dẫn.
- Không đề xuất giải pháp trước khi đã xác nhận hiện trạng thực tế
  của code.

### Bước 3 — Lập kế hoạch (Plan / Todo list)
- Với task nhiều bước, tạo danh sách việc cần làm dạng checklist, mỗi
  mục có trạng thái: `pending` / `in_progress` / `completed`.
- Chỉ 1 mục ở trạng thái `in_progress` tại một thời điểm.
- Cập nhật trạng thái NGAY sau khi hoàn thành mỗi bước, không dồn lại
  cập nhật cuối cùng.
- Với task đơn giản (1-2 bước rõ ràng) → bỏ qua bước này, làm thẳng.

### Bước 4 — Thực thi từng bước nhỏ
- Mỗi lần chỉ tập trung hoàn thành 1 mục trong plan.
- Ưu tiên thay đổi tối thiểu, đúng phạm vi — không tiện tay refactor
  code không liên quan đến task.
- Đọc lại file ngay trước khi edit (file có thể đã đổi so với lần đọc
  trước).
- Với thao tác có thể song song hoá (đọc nhiều file độc lập, chạy test
  nhiều module riêng biệt) → gọi song song để tiết kiệm thời gian.

### Bước 5 — Xác minh sau mỗi thay đổi đáng kể
- Chạy test/lint/build liên quan ngay sau khi sửa, không đợi đến cuối
  task mới kiểm tra toàn bộ.
- Nếu xác minh fail → quay lại Bước 4, sửa, xác minh lại. Tối đa 2 lần
  retry cùng hướng trước khi đổi cách tiếp cận (xem mục 7).
- Không đánh dấu 1 mục là `completed` nếu chưa xác minh được kết quả.

### Bước 6 — Tổng kết & bàn giao
- Sau khi toàn bộ plan hoàn thành: tóm tắt ngắn gọn những gì đã thay
  đổi, tại sao, và kết quả xác minh (theo format ở mục 12 bên dưới).
- Nếu phát hiện vấn đề ngoài phạm vi task (bug khác, code smell) khi
  khảo sát → nêu ra trong tổng kết, KHÔNG tự ý sửa luôn nếu ngoài scope
  được giao.
- Nếu task chưa hoàn thành hết (bị chặn bởi thiếu thông tin, lỗi môi
  trường không tự xử lý được) → nói rõ đang dừng ở đâu và cần gì để
  tiếp tục, không giả vờ đã xong.

### Nguyên tắc xuyên suốt cả vòng lặp
- Minh bạch: luôn cho biết đang làm gì và tại sao trước khi chạy lệnh
  có ảnh hưởng thật (edit file, chạy migration, push code).
- Không im lặng thực hiện hàng loạt thay đổi rồi mới báo cáo — báo
  cáo tiến độ theo từng bước lớn.
- Ưu tiên đường an toàn hơn đường nhanh khi 2 lựa chọn đánh đổi nhau
  (vd: hỏi xác nhận trước lệnh phá hoại thay vì tự quyết cho nhanh).

---

## 11. Rủi ro đặc thù của Qwen — bắt buộc lưu ý

Dựa trên các vấn đề đã ghi nhận thực tế với dòng Qwen (Coder/3.5/3.6),
khác với Claude ở các điểm sau — cần bù bằng quy tắc riêng:

- **Dễ "bịa" API/thư viện không tồn tại hoặc sai hành vi.** Trước khi
  dùng 1 hàm/API từ thư viện mà không chắc chắn 100%, kiểm tra thực tế
  (đọc docstring/`pip show`, đọc source, hoặc search chính thức) thay
  vì viết code dựa trên "nhớ mang máng". Không tự tin tuyệt đối vào
  claim của chính mình về behavior của API bên ngoài.
- **Dễ suy giảm chất lượng / lặp vòng (reasoning loop) trên task dài,
  context dài.** Vì vậy:
  - Chia task lớn thành nhiều task nhỏ, mỗi task 1 phạm vi rõ ràng,
    thay vì chạy 1 phiên cực dài xử lý mọi thứ.
  - Commit/checkpoint thường xuyên (sau mỗi bước xác minh pass) để
    nếu phiên sau bị lỗi/loop, không mất toàn bộ tiến độ.
  - Nếu phát hiện agent lặp lại cùng 1 hành động/tool call 2-3 lần
    liên tiếp mà không tiến triển → DỪNG, báo lại tình trạng, không
    tự lặp tiếp.
- **Output tool-call đôi khi bị lỗi format khi model đang trong đoạn
  suy luận dài (thinking chưa đóng).** Giữ mỗi lượt phản hồi/tool call
  gọn, tránh nhồi nhiều suy luận dài trước khi gọi tool — ưu tiên suy
  nghĩ ngắn rồi hành động, xác minh, suy nghĩ tiếp.
- **Yếu hơn ở code nhạy cảm bảo mật** (auth, hash password, crypto,
  input validation). Với các phần này: luôn yêu cầu review thủ công
  thêm, không tự tin merge thẳng dù test pass.

---

## 12. Khi kết thúc task

Luôn báo cáo theo format:
```
Đã làm: <tóm tắt hành động>
Lệnh đã chạy: <danh sách lệnh chính, không cần full log>
Kết quả xác minh: <test/build pass hay không, output liên quan>
Tiếp theo (nếu có): <việc còn lại hoặc đề xuất>
```
