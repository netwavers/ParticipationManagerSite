#!/usr/bin/env python3
"""
🐾 rebuild_history_tanuki.py
チャット履歴 (Documents/Archive/History/Gemini) を含む TANUKI 知識ベースの再構築スクリプト
（月別分割コンパイル対応）
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path

def get_available_months(history_root: Path) -> list[tuple[str, int]]:
    """Gemini履歴配下の月別ディレクトリ一覧とその中のMarkdownファイル数を取得"""
    if not history_root.is_dir():
        return []
    
    results = []
    for item in sorted(history_root.iterdir()):
        if item.is_dir() and item.name != "InBox":
            md_files = list(item.glob("*.md"))
            results.append((item.name, len(md_files)))
    return results

def rebuild_history():
    script_dir = Path(__file__).resolve().parent
    history_root = script_dir.parent / "History/Gemini"
    
    parser = argparse.ArgumentParser(
        description="🐾 TANUKI Knowledge Base Rebuild Script (Chat History Support with Monthly Splitting)"
    )
    parser.add_argument(
        "--mode",
        choices=["all", "history-only"],
        default="all",
        help="Build mode: 'all' (documents + chat history) or 'history-only' (chat history only)"
    )
    parser.add_argument(
        "--month",
        type=str,
        help="Target month directory to build (e.g. '2026_05'). Skips full rebuild."
    )
    parser.add_argument(
        "--list-months",
        action="store_true",
        help="List available month directories in chat history and exit."
    )
    args = parser.parse_args()

    # 月一覧の表示処理
    if args.list_months:
        months = get_available_months(history_root)
        print("🐾 利用可能なチャット履歴の年月ディレクトリ一覧:")
        if not months:
            print("  (履歴ディレクトリが見つかりません)")
        else:
            for month_name, file_count in months:
                print(f"  - {month_name} ({file_count} files)")
        sys.exit(0)

    sys.path.insert(0, str(script_dir))
    from rag_policy_loader import apply_compile_env, load_policy

    policy = load_policy()
    base_dirs = policy.get("compile_dirs", [])
    history_rel_base = "../Documents/Archive/History/Gemini"

    if args.month:
        # 特定月のみのピンポイントビルド
        target_dir = f"{history_rel_base}/{args.month}"
        target_dirs = [target_dir]
        build_desc = f"Month '{args.month}'"
    elif args.mode == "history-only":
        target_dirs = [history_rel_base]
        build_desc = "History Only (All Months)"
    else: # "all"
        target_dirs = list(base_dirs)
        if history_rel_base not in target_dirs:
            target_dirs.append(history_rel_base)
        build_desc = "All Documents + All Chat History"

    print(f"🐾 Rebuilding TANUKI Knowledge Base ({build_desc})...")
    print(f"  Target Directories: {target_dirs}")

    tanuki_dir = (script_dir / "../../../TANUKI").resolve()
    env = apply_compile_env(os.environ.copy())
    env["TANUKI_TARGET_DIRS"] = ",".join(target_dirs)
    env["OLLAMA_KEEP_ALIVE"] = "5m"

    try:
        process = subprocess.Popen(
            ["cargo", "run", "--bin", "tanuki-compiler", "--", "compile"],
            cwd=tanuki_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        for line in process.stdout:
            try:
                sys.stdout.write(line)
                sys.stdout.flush()
            except UnicodeEncodeError:
                sys.stdout.write(line.encode("ascii", "replace").decode("ascii"))
                sys.stdout.flush()

        process.wait()

        if process.returncode == 0:
            print(f"\n[OK] TANUKI History Rebuild complete! ({build_desc})")
        else:
            print(f"\n[FAIL] TANUKI History Rebuild failed with return code {process.returncode}")
            sys.exit(process.returncode)

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    rebuild_history()
