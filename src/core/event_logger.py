import os
import re

class EventLogger:
    """
    Thêm code ghi log vào APK để theo dõi các lời gọi billing/license.
    Log được ghi vào /sdcard/lp_pc_events.log trên thiết bị.
    """
    def __init__(self, decompiled_path, log_callback=print):
        self.decompiled_path = decompiled_path
        self.log = log_callback

    def inject_logging(self):
        self.log("[*] [EventLogger] Đang thêm code ghi log sự kiện...")
        count = 0

        # Thêm một class Logger vào smali
        logger_dir = os.path.join(self.decompiled_path, 'smali', 'com', 'lppc', 'logger')
        os.makedirs(logger_dir, exist_ok=True)

        logger_smali = '''.class public Lcom/lppc/logger/EventLogger;
.super Ljava/lang/Object;
.source "EventLogger.java"

.method public static log(Ljava/lang/String;Ljava/lang/String;)V
    .registers 6
    :try_start
    new-instance v0, Ljava/io/FileWriter;
    const-string v1, "/sdcard/lp_pc_events.log"
    const/4 v2, 0x1  # append mode
    invoke-direct {v0, v1, v2}, Ljava/io/FileWriter;-><init>(Ljava/lang/String;Z)V
    new-instance v1, Ljava/io/BufferedWriter;
    invoke-direct {v1, v0}, Ljava/io/BufferedWriter;-><init>(Ljava/io/Writer;)V
    new-instance v2, Ljava/lang/StringBuilder;
    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J
    move-result-wide v3
    invoke-virtual {v2, v3, v4}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;
    const-string v3, " | "
    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string p0, " | "
    invoke-virtual {v2, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string p0, "\\n"
    invoke-virtual {v2, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object p0
    invoke-virtual {v1, p0}, Ljava/io/BufferedWriter;->write(Ljava/lang/String;)V
    invoke-virtual {v1}, Ljava/io/BufferedWriter;->close()V
    invoke-virtual {v0}, Ljava/io/FileWriter;->close()V
    :try_end
    .catch Ljava/io/IOException; {:try_start .. :try_end} :end_try
    :end_try
    return-void
.end method
'''
        logger_path = os.path.join(logger_dir, 'EventLogger.smali')
        if not os.path.exists(logger_path):
            with open(logger_path, 'w', encoding='utf-8') as f:
                f.write(logger_smali)
            self.log("[+] [EventLogger] Added EventLogger class")
            count += 1

        # Thêm lời gọi log vào các method billing
        billing_methods = [
            'launchBillingFlow', 'queryPurchases', 'getBuyIntent',
            'startConnection', 'endConnection'
        ]
        for root, dirs, files in os.walk(self.decompiled_path):
            for file in files:
                if not file.endswith('.smali'): continue
                path = os.path.join(root, file)
                if len(path) > 250: continue
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception: continue

                modified = False
                for method in billing_methods:
                    if method not in content: continue

                    # Tìm vị trí đầu method để thêm lời gọi log
                    pattern = r'(\.method\s+(?:public|private|static)\s+(?:final\s+)?' + method + r'\(.*?\)\s*(?:V|L.*?;)\s*)'
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        # Chèn lời gọi log vào ngay sau header method
                        header_end = match.end()
                        log_call = f'\n    const-string v0, "Billing"\n    const-string v1, "{method} called"\n    invoke-static {{v0, v1}}, Lcom/lppc/logger/EventLogger;->log(Ljava/lang/String;Ljava/lang/String;)V\n'
                        content = content[:header_end] + log_call + content[header_end:]
                        modified = True

                if modified:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    count += 1
                    self.log(f"[+] [EventLogger] Added logging to {os.path.basename(path)}")

        self.log(f"[*] [EventLogger] Tổng số file đã thêm log: {count}")
        return count