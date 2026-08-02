# 🐾 TanukiHistoryMigrator

ご主人様、過去のGeminiチャット履歴（Google Takeout形式）を読み込み、T.A.N.U.K.I.知識ベースへ高速かつメモリ効率良く移行・コンパイルするためのマイグレーションプロジェクトですわ！

## 🌟 特徴
- **定数メモリパース (O(1))**: 1MBずつのチャンクストリーミング読込により、1GBを超える大容量HTMLでもRAM使用量を32MB以下に抑えて安全に処理します。
- **堅牢な HTMLParser**: 汚染されたHTMLデータ（未閉じタグや交差タグ、不等号）でもエラーを起こさず決定論的に救済・パースします。
- **インデックス自動生成**: 年月ごとに整理されたフォルダ階層に `INDEX.md` および会話ログ（`minutes_*.md`）を自動ビルドします。

## 📁 ディレクトリ構成
```text
TanukiHistoryMigrator/
├── pyproject.toml              # プロジェクトパッケージメタデータ
├── requirements.txt            # 依存関係（テスト用 psutil など）
├── README.md                   # この説明書です！
├── tanuki_history_migrator/    # パッケージソースコード
│   ├── __init__.py
│   ├── parser.py               # HTMLストリーミングパーサクラス
│   ├── compiler.py             # ディレクトリ構造コンパイルクラス
│   └── cli.py                  # CLIエントリーポイント
└── tests/                      # ユニットテスト
    └── test_migrator.py
```

## 🛠 インストール方法

### 1. 開発モードでのインストール
PEP 668が有効なLinux環境では、`--break-system-packages` フラグを指定するか、仮想環境を有効化してインストールします。

```bash
# システム環境にそのままインストールする場合
pip install -e . --break-system-packages

# または開発用の依存関係（テスト用 psutil 等）も含める場合
pip install -e .[dev] --break-system-packages
```

※ 仮想環境（`venv`）を使用する場合は以下のように実行します：
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 🚀 使い方

### コマンドラインからの実行
パッケージをインストールすると、`tanuki-migrate` コマンドが使用可能になります。

```bash
tanuki-migrate --input "path/to/MyActivity.html" --jsonl "path/to/output.jsonl" --output-dir "path/to/root/archive"
```

#### 引数オプション：
- `--input` : パース対象の Google Takeout HTMLファイルのパス (デフォルト: `/home/tanuki/PyProjects/Documents/InBox/MyActivity.html`)
- `--jsonl` : 一時出力されるシリアライズ済みJSONLファイルのパス (デフォルト: `/home/tanuki/PyProjects/Documents/InBox/serialized_data.jsonl`)
- `--output-dir` : コンパイルされたマークダウン群を出力するルートディレクトリ (デフォルト: `/home/tanuki/PyProjects/Documents/Archive/History/Gemini`)
- `--error-log` : エラーログファイルの出力先 (デフォルト: `parser_errors.log`)

### 🧠 TANUKI 知識ベースへのインデックス反映
マイグレーション後、以下のコマンドでチャット履歴を含めた TANUKI 知識ベースの再構築を行えます：
```bash
cd /home/tanuki/PyProjects/Documents/Archive/Devlog

# 月一覧の確認
python3 rebuild_history_tanuki.py --list-months

# 特定月のみを分割高速ビルド（計算資源節約）
python3 rebuild_history_tanuki.py --month 2026_05
```

## 🧪 テストの実行

以下のコマンドでユニットテストを実行できます：
```bash
python -m unittest discover -s tests
```
テストを実行すると、メモリ消費が32MB以内に抑えられているかのベンチマークも自動で行われますわ！💮
