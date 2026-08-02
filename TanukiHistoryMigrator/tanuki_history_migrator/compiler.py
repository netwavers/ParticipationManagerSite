import os
import re
import json

class TanukiTreeCompiler:
    def __init__(self, jsonl_path, output_root="root/archive"):
        self.jsonl_path = jsonl_path
        self.output_root = output_root
        self.directories_meta = {} # YYYY_MM -> list of session_meta dicts

    def compile(self):
        print(f"🐾 Tree Compiler: Compiling from {self.jsonl_path} ...", flush=True)
        
        buffer_size = 1024 * 1024 # 1MB
        
        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                
                session_id = data["session_id"]
                timestamp = data["timestamp"]
                turn_pair = data["turn_pair"]
                
                # 年月の抽出 (YYYY年MM月DD日 -> YYYY, MM)
                match = re.match(r'(\d{4})年(\d{2})月', timestamp)
                if match:
                    yyyy, mm = match.group(1), match.group(2)
                else:
                    yyyy, mm = "2026", "05"
                    
                dir_name = f"{yyyy}_{mm}"
                dir_path = os.path.join(self.output_root, dir_name)
                os.makedirs(dir_path, exist_ok=True)
                
                # 個別ファイル名
                session_num = re.search(r'\d+', session_id)
                num_str = session_num.group(0) if session_num else session_id
                file_name = f"minutes_tanuki_session_{num_str}.md"
                file_path = os.path.join(dir_path, file_name)
                
                # 会話内容の書き出し
                content = f"""# PATH: /root/archive/{dir_name}/{file_name}

## 1. タイムスタンプ
- 記録日: {timestamp}

## 2. 对話コンテキスト

### 👤 ユーザープロンプト (USER_TURN)
{turn_pair["user_prompt"]}

### 🤖 AI応答 (AI_TURN)
{turn_pair["ai_response"]}
"""
                
                with open(file_path, "w", encoding="utf-8", buffering=buffer_size) as out_f:
                    out_f.write(content)
                    out_f.flush()
                
                preview = turn_pair["user_prompt"][:60].replace("\n", " ")
                if len(turn_pair["user_prompt"]) > 60:
                    preview += "..."
                    
                meta = {
                    "file_name": file_name,
                    "timestamp": timestamp,
                    "preview": preview
                }
                
                if dir_name not in self.directories_meta:
                    self.directories_meta[dir_name] = []
                self.directories_meta[dir_name].append(meta)

        # INDEX.md の自動生成
        for dir_name, sessions in self.directories_meta.items():
            dir_path = os.path.join(self.output_root, dir_name)
            index_path = os.path.join(dir_path, "INDEX.md")
            
            yyyy, mm = dir_name.split("_")
            
            index_content = f"""# PATH: /root/archive/{dir_name}

## 1. 階層サマリ
本階層は、ご主人様の過去のGeminiチャット履歴のうち、`[{yyyy}年{mm}月]` に分類された文脈ノード群（全 {len(sessions)} 件）を厳格に保持するインデックスレイヤーですわ。

## 2. 下層への分岐
"""
            for s in sessions:
                index_content += f"* [FILE] `{s['file_name']}` : ({s['timestamp']}) {s['preview']}\n"
                
            index_content += """
## 3. 探索上の注意点
* 本ノードに求める具体的な実装コードや抽象概念が見つからない場合は、自律的に上位階層（../）へバックトラック、または意味的に隣接するクラスタを走査すること。
"""
            with open(index_path, "w", encoding="utf-8", buffering=buffer_size) as idx_f:
                idx_f.write(index_content)
                idx_f.flush()
                
        print("✅ Compilation complete! All INDEX.md files dynamic generated.", flush=True)
