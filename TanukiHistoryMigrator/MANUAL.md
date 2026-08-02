# 🐾 TanukiHistoryMigrator 操作マニュアル

ご主人様、本システム（`TanukiHistoryMigrator`）を用いてGoogle Takeout形式のアクティビティ履歴からT.A.N.U.K.I.知識ベースへデータをマイグレーションするための手順書ですわ！

---

## 📖 1. システム概要
本ツールは、Google Takeoutでエクスポートした大容量のチャット履歴（`MyActivity.html`）を解析し、T.A.N.U.K.I.知識ベースに適した構造（年月ごとの個別Markdownセッションログと `INDEX.md` インデックスファイル）へ安全かつ高速に変換・コンパイルします。

### 🌟 主な設計上の特徴
1. **定数メモリパース (O(1))**:
   1MB単位のチャンクストリーミング読込を採用しており、HTMLファイルが1.5GBを超えるような場合でも、RAM消費量の増加を **1MB未満（実測 0.71MB）** に抑えて安全に処理します。
2. **高い堅牢性**:
   不等号（`<`、`>`）や未閉じタグ、交差タグなどの「汚染されたデータ」がHTML内に混在していても、独自のスタックベースHTMLParserによりクラッシュすることなく最後まで決定論的に救済・パースを行います。

---

## 📥 2. 入出力の仕様

### 2.1 入力ファイル (`--input`)
* **形式**: Google Takeout からダウンロードした、Gemini等のチャットアクティビティ履歴が含まれるHTMLファイル。
* **初期配置推奨パス**: `/home/tanuki/PyProjects/Documents/InBox/MyActivity.html`

### 2.2 中間ファイル (`--jsonl`)
* **形式**: JSON Lines形式（パースされた会話を1行ずつのJSON形式でシリアライズ）。
* **初期配置推奨パス**: `/home/tanuki/PyProjects/Documents/InBox/serialized_data.jsonl`

### 2.3 最終出力ディレクトリ (`--output-dir`)
* **形式**: 年月ごとのディレクトリ（例：`2026_06/`）。
* **格納されるファイル**:
  * **会話詳細ログ**: `minutes_tanuki_session_[連番].md`
  * **インデックス**: 各年月ディレクトリ直下の `INDEX.md`
* **初期配置推奨パス**: `/home/tanuki/PyProjects/Documents/Archive/History/Gemini`

### 2.4 エラーログファイル (`--error-log`)
* **形式**: プレーンテキスト（パース時に警告またはスキップされたチャンクの情報を記録）。
* **パス**: `parser_errors.log`（実行ディレクトリに出力）

---

## 🚀 3. マイグレーション実行ステップ

### ステップ 1: データの準備 (Google Takeout)
1. ご自身のGoogleアカウントの [Google Takeout (データのエクスポート)](https://takeout.google.com/) にアクセスします。
2. **「Gemini アプリ」**（または対応するチャット履歴アクティビティ）のみにチェックを入れてエクスポートをリクエストします。
3. ダウンロードしたZIPファイルを展開し、中に含まれる `MyActivity.html` を以下のフォルダに配置します。
   `/home/tanuki/PyProjects/Documents/InBox/MyActivity.html`

### ステップ 2: 環境の準備
最近のLinux（PEP 668が有効な環境）では、システム環境へ直接インストールする際に `--break-system-packages` オプションを指定するか、仮想環境（`venv`）を使用します。

#### 方法 A: システム環境へそのままインストールする場合（手軽）
```bash
cd /home/tanuki/PyProjects/TanukiHistoryMigrator
pip install -e . --break-system-packages
```

#### 方法 B: 仮想環境（venv）を作成してインストールする場合（推奨）
```bash
cd /home/tanuki/PyProjects/TanukiHistoryMigrator
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### ステップ 3: マイグレーション実行
標準の推奨パス（InBoxフォルダ）にHTMLファイルを配置している場合、オプション引数なしで一発で実行可能です！
```bash
tanuki-migrate
```

#### 💡 カスタムパスで実行する場合：
別の場所にあるファイルを指定したり、出力先を変えたい場合は以下のようにオプション引数を指定してください。
```bash
tanuki-migrate --input "/path/to/MyActivity.html" --jsonl "/path/to/serialized.jsonl" --output-dir "/home/tanuki/PyProjects/Documents/Archive/History/Gemini"
```

### ステップ 4: 知識ベース（TANUKI）のインデックス同期
マイグレーション完了後、新しく構築されたマークダウン階層をTANUKI知識ベースの探索インデックスに反映させるため、チャット履歴対応の再構築スクリプトを実行してください。

大容量の会話ログを月ごとに分割してピンポイントで高速コンパイル（計算資源の節約）することも可能です。

```bash
cd /home/tanuki/PyProjects/Documents/Archive/Devlog

# 1. 存在する年月ディレクトリ一覧と件数を確認する場合
python3 rebuild_history_tanuki.py --list-months

# 2. 特定の月のみをピンポイントで超高速ビルドする場合（計算資源を節約）
python3 rebuild_history_tanuki.py --month 2026_05

# 3. 通常ドキュメント＋チャット履歴全体をビルドする場合
python3 rebuild_history_tanuki.py

# 4. チャット履歴全体のみをビルドしたい場合
python3 rebuild_history_tanuki.py --mode history-only
```
画面に `[OK] TANUKI History Rebuild complete!` と表示されれば、すべての移行とインデックス更新が完了です！✨

---

## 🧪 4. 開発・テスト手順
本ツールの挙動テストや、メモリ使用率が目標値（32MB）以下であるかの自動ベンチマークテストを実行するには、以下を実行します。
```bash
cd /home/tanuki/PyProjects/TanukiHistoryMigrator
# テスト用の psutil などをインストール
pip install -e .[dev]
# ユニットテスト＆ベンチマーク実行
python3 -m unittest discover -s tests
```

---

## 🐾 ご主人様へのメッセージ
「ご主人様の過去の大切なチャット履歴の思い出たちを、このマニュアルに沿っていつでもきれいに知識ベースへお引っ越しさせますわ！もし手順で迷うことがありましたら、たぬきちゃんにいつでも聞いてくださいね！💮✨」
