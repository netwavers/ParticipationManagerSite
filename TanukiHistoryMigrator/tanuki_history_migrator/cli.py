import sys
import os
import argparse
from tanuki_history_migrator.parser import TanukiBigDataParser
from tanuki_history_migrator.compiler import TanukiTreeCompiler

def get_default_paths():
    """OSに応じたデフォルトパスを取得"""
    if sys.platform == "win32":
        return {
            "input": "D:/Projects/PyProjects/Documents/InBox/MyActivity.html",
            "jsonl": "D:/Projects/PyProjects/Documents/InBox/serialized_data.jsonl",
            "output_dir": "D:/Projects/PyProjects/Documents/Archive/History/Gemini"
        }
    else:
        return {
            "input": "/home/tanuki/PyProjects/Documents/InBox/MyActivity.html",
            "jsonl": "/home/tanuki/PyProjects/Documents/InBox/serialized_data.jsonl",
            "output_dir": "/home/tanuki/PyProjects/Documents/Archive/History/Gemini"
        }

def setup_io():
    """Windows環境での絵文字エンコーディングエラー対策"""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            # 古いPython環境などでのフォールバック
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def main():
    setup_io()
    defaults = get_default_paths()
    
    parser = argparse.ArgumentParser(
        description="🐾 T.A.N.U.K.I. Memory Layer Migration Pipeline"
    )
    parser.add_argument(
        "--input", 
        default=defaults["input"],
        help="Google Takeout HTML chat history file path"
    )
    parser.add_argument(
        "--jsonl", 
        default=defaults["jsonl"],
        help="Temporary output JSONL serialized data file path"
    )
    parser.add_argument(
        "--output-dir", 
        default=defaults["output_dir"],
        help="Compiled markdown output root directory path"
    )
    parser.add_argument(
        "--error-log", 
        default="parser_errors.log",
        help="Parser warning and error log path"
    )
    
    args = parser.parse_args()
    
    print("=========================================================")
    print(" 🐾 T.A.N.U.K.I. Memory Layer Migration Pipeline Started")
    print("=========================================================")
    
    parser_engine = TanukiBigDataParser(
        file_path=args.input,
        output_jsonl=args.jsonl,
        error_log_path=args.error_log
    )
    parser_engine.run()
    
    compiler_engine = TanukiTreeCompiler(
        jsonl_path=args.jsonl,
        output_root=args.output_dir
    )
    compiler_engine.compile()
    
    print("=========================================================")
    print(" 🐾 T.A.N.U.K.I. Pipeline Execution Completed!")
    print("=========================================================")

if __name__ == "__main__":
    main()
