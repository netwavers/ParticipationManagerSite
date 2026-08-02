import re
import html
import json
import os
from datetime import datetime
from html.parser import HTMLParser

class TakeoutHTMLParser(HTMLParser):
    def __init__(self, on_session_extracted, error_log_path):
        super().__init__()
        self.on_session_extracted = on_session_extracted
        self.error_log_path = error_log_path
        self.tag_stack = []
        self.cell_text_accumulator = []

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            attrs_dict = dict(attrs)
            cls = attrs_dict.get("class", "")
            valid_classes = ["outer-cell", "content-cell", "mdl-grid", "header-cell"]
            if any(vc in cls for vc in valid_classes):
                self.tag_stack.append((tag, cls))

    def handle_endtag(self, tag):
        if tag == "div" and self.tag_stack:
            popped_tag, popped_cls = self.tag_stack[-1]
            valid_classes = ["outer-cell", "content-cell", "mdl-grid", "header-cell"]
            if any(vc in popped_cls for vc in valid_classes):
                self.tag_stack.pop()
                if popped_tag == "div" and "outer-cell" in popped_cls:
                    full_cell_text = "".join(self.cell_text_accumulator)
                    self.process_extracted_cell(full_cell_text)
                    self.cell_text_accumulator = []

    def handle_data(self, data):
        # 現在のスタック内に "content-cell" が存在する場合のみデータを蓄積
        is_inside_content = False
        for tag, cls in self.tag_stack:
            if tag == "div" and "content-cell" in cls:
                is_inside_content = True
                break
                
        if is_inside_content:
            self.cell_text_accumulator.append(data)

    def process_extracted_cell(self, cell_text):
        msg_prefix = "送信したメッセージ:"
        if msg_prefix not in cell_text:
            return
            
        # タイムスタンプの抽出 (YYYY/MM/DD HH:MM:SS JST)
        ts_match = re.search(r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} JST)', cell_text)
        if not ts_match:
            return
            
        timestamp_raw = ts_match.group(1)
        ts_pos = cell_text.find(timestamp_raw)
        
        prompt_start = cell_text.find(msg_prefix) + len(msg_prefix)
        user_prompt = cell_text[prompt_start:ts_pos].strip()
        ai_response = cell_text[ts_pos + len(timestamp_raw):].strip()
        
        # サニタイズ
        user_prompt = html.unescape(user_prompt).strip()
        ai_response = html.unescape(ai_response).strip()
        
        # タイムスタンプのフォーマット
        try:
            dt = datetime.strptime(timestamp_raw, "%Y/%m/%d %H:%M:%S JST")
            timestamp_formatted = dt.strftime("%Y年%m月%d日 %H:%M:%S")
        except Exception:
            timestamp_formatted = timestamp_raw
            
        self.on_session_extracted(timestamp_formatted, user_prompt, ai_response)


class TanukiBigDataParser:
    def __init__(self, file_path, output_jsonl, error_log_path="parser_errors.log"):
        self.file_path = file_path
        self.output_jsonl = output_jsonl
        self.error_log_path = error_log_path
        self.session_counter = 0
        self.out_f = None

    def on_session_extracted(self, timestamp, user_prompt, ai_response):
        self.session_counter += 1
        session_id = f"tanuki_session_{self.session_counter:08d}"
        
        data = {
            "session_id": session_id,
            "timestamp": timestamp,
            "turn_pair": {
                "user_prompt": user_prompt,
                "ai_response": ai_response
            }
        }
        
        # 逐次 Flush を保証して JSONL に書き込み
        self.out_f.write(json.dumps(data, ensure_ascii=False) + "\n")
        self.out_f.flush()

    def run(self):
        print(f"🐾 BigData Parser: Scanning {self.file_path} ...", flush=True)
        
        # エラーログの初期化
        with open(self.error_log_path, "w", encoding="utf-8") as err_f:
            err_f.write(f"--- T.A.N.U.K.I. Parser Error Log: {datetime.now()} ---\n")

        # HTMLParser インスタンスの作成
        parser = TakeoutHTMLParser(self.on_session_extracted, self.error_log_path)

        with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f, \
             open(self.output_jsonl, "w", encoding="utf-8") as out_f:
            
            self.out_f = out_f
            
            # 1.5GBの大容量を想定し、1MBずつのチャンク読み込みでメモリ使用量を完全に定数に抑え込みます
            chunk_size = 1024 * 1024 # 1MB
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                try:
                    parser.feed(chunk)
                except Exception as e:
                    # エラースキップ ＆ ロギングの徹底
                    error_msg = f"Parse Warning in chunk feed: {e}\n"
                    print(f"⚠️ {error_msg.strip()}", flush=True)
                    with open(self.error_log_path, "a", encoding="utf-8") as err_f:
                        err_f.write(error_msg)
            
            parser.close()

        print(f"✅ Parsing complete! Total sessions processed: {self.session_counter}", flush=True)
