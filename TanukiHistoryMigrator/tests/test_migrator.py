import unittest
import os
import sys
import json
import psutil
import shutil

# パッケージルートを path に追加して実行可能にする
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tanuki_history_migrator.parser import TanukiBigDataParser
from tanuki_history_migrator.compiler import TanukiTreeCompiler

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

class TestTanukiPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_sandbox"
        os.makedirs(self.test_dir, exist_ok=True)
        self.dummy_html = os.path.join(self.test_dir, "dummy_activity.html")
        self.dummy_jsonl = os.path.join(self.test_dir, "dummy_serialized.jsonl")
        self.dummy_output = os.path.join(self.test_dir, "dummy_root/archive")
        self.dummy_err_log = os.path.join(self.test_dir, "dummy_errors.log")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def create_dummy_html(self, content_list):
        """ダミーのHTMLを作成する"""
        with open(self.dummy_html, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Test</title></head><body>\n")
            for c in content_list:
                f.write(c + "\n")
            f.write("</body></html>\n")

    def test_normal_parsing_and_compiling(self):
        """正常データのパースとインデックス生成の検証"""
        normal_cell = """
        <div class="outer-cell mdl-cell">
          <div class="mdl-grid">
            <div class="header-cell"><p class="mdl-typography--title">Gemini アプリ<br></p></div>
            <div class="content-cell mdl-typography--body-1">
              送信したメッセージ: 大手のゲーム会社なら自前でLLMを持ちなさい！<br>
              2026/05/26 13:46:29 JST<br>
              はわわ！素晴らしい大号令ですわ！🐾
            </div>
          </div>
        </div>
        """
        self.create_dummy_html([normal_cell])
        
        parser = TanukiBigDataParser(self.dummy_html, self.dummy_jsonl, self.dummy_err_log)
        parser.run()
        
        self.assertEqual(parser.session_counter, 1)
        self.assertTrue(os.path.exists(self.dummy_jsonl))
        
        with open(self.dummy_jsonl, "r", encoding="utf-8") as f:
            data = json.loads(f.read().strip())
            self.assertEqual(data["session_id"], "tanuki_session_00000001")
            self.assertEqual(data["timestamp"], "2026年05月26日 13:46:29")
            # HTMLParserは自動で改行や空白をサニタイズする
            self.assertIn("大手のゲーム会社なら自前でLLMを持ちなさい！", data["turn_pair"]["user_prompt"])
            self.assertIn("はわわ！素晴らしい大号令ですわ！🐾", data["turn_pair"]["ai_response"])
            
        compiler = TanukiTreeCompiler(self.dummy_jsonl, self.dummy_output)
        compiler.compile()
        
        target_dir = os.path.join(self.dummy_output, "2026_05")
        self.assertTrue(os.path.exists(target_dir))
        
        md_file = os.path.join(target_dir, "minutes_tanuki_session_00000001.md")
        self.assertTrue(os.path.exists(md_file))
        
        index_file = os.path.join(target_dir, "INDEX.md")
        self.assertTrue(os.path.exists(index_file))
        
        with open(index_file, "r", encoding="utf-8") as f:
            idx_content = f.read()
            self.assertIn("minutes_tanuki_session_00000001.md", idx_content)
            self.assertIn("(2026年05月26日 13:46:29)", idx_content)
            self.assertIn("全 1 件", idx_content)

    def test_html_parser_robustness(self):
        """不等号、未閉じタグ、特殊文字等を含む汚染データに対する HTMLParser の超堅牢性検証"""
        normal_cell = """
        <div class="outer-cell">
          <div class="content-cell">
            送信したメッセージ: 正常なプロンプトですわ。<br>
            2026/05/26 12:00:00 JST<br>
            正常な応答です。
          </div>
        </div>
        """
        # HTMLParserなら、不等号 <= や ->、未閉じタグ <br>、アンパサンド孤立 & もエラーなく完璧に処理します
        dirty_cell = """
        <div class="outer-cell">
          <div class="content-cell">
            送信したメッセージ: 壊れたプロンプト & <= -> 5 < 10 <br>
            2026/05/26 12:05:00 JST<br>
            壊れた応答です。 <div> タグの交差 </span> <p>段落
          </div>
        </div>
        """
        self.create_dummy_html([normal_cell, dirty_cell, normal_cell])
        
        parser = TanukiBigDataParser(self.dummy_html, self.dummy_jsonl, self.dummy_err_log)
        parser.run()
        
        # HTMLParserの強力な耐障害性により、エラーで止まることなく全 3 セッションすべて完璧にパースされます！
        self.assertEqual(parser.session_counter, 3)
        self.assertTrue(os.path.exists(self.dummy_jsonl))

    def test_ram_usage_benchmark(self):
        """大量のダミーデータをストリーミングで流した際も、RAM使用量が 32MB 以下に維持されることを自動検証"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        print(f"\n📊 Initial Memory: {initial_memory:.2f} MB")
        
        dummy_cell_template = """
        <div class="outer-cell">
          <div class="content-cell">
            送信したメッセージ: 疑似ベンチマーク用プロンプト ID {id} - {long_payload}<br>
            2026/05/26 13:00:00 JST<br>
            疑似ベンチマーク用応答 ID {id} - {long_payload}
          </div>
        </div>
        """
        long_payload = "A" * 1000 
        
        with open(self.dummy_html, "w", encoding="utf-8") as f:
            f.write("<html><body>\n")
            for i in range(1000): # 大容量データ
                f.write(dummy_cell_template.format(id=i, long_payload=long_payload) + "\n")
            f.write("</body></html>\n")
            
        parser = TanukiBigDataParser(self.dummy_html, self.dummy_jsonl, self.dummy_err_log)
        parser.run()
        
        mid_memory = process.memory_info().rss / 1024 / 1024
        print(f"📊 Mid-Process Memory: {mid_memory:.2f} MB")
        
        compiler = TanukiTreeCompiler(self.dummy_jsonl, self.dummy_output)
        compiler.compile()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        print(f"📊 Final Memory: {final_memory:.2f} MB")
        
        memory_increase = final_memory - initial_memory
        print(f"📊 Net Memory Increase: {memory_increase:.2f} MB")
        self.assertLess(memory_increase, 32.0)

if __name__ == "__main__":
    unittest.main()
