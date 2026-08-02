# 🐾 開発日誌_20260802_TanukiHistoryMigratorのLinux環境マイグレーション対応

## 📅 メタ
- 記録日: 2026-08-02
- スコープ: PyProjects
- セッション種別: 実装

## 🌟 概要
TanukiHistoryMigratorのCLIデフォルトパスおよび各種ドキュメントをLinux環境（/home/tanuki/PyProjects/...）対応へマイグレーション

## 🛠 変更
- tanuki_history_migrator/cli.py にOS判別ロジック get_default_paths() を追加し、Linux環境用のデフォルトパスを設定\n- README.md および MANUAL.md 内の Windows ドライブレター表記・PowerShell コマンド例を Linux パスおよび bash コマンド例へ変更・統一

## ✅ 検証
- python3 -m tanuki_history_migrator.cli --help および unittest で正常動作を確認\n- 定数メモリパース等の主要機能の全テスト合格を確認

## 🚀 次回
- Linux環境での実データ（Google Takeout MyActivity.html）投入による実地移行テスト

---
<!-- Tanuki-Hash: 08f574c8831a002497aa23ea1cc7dccae45c837c3fbc9e00cdf3ac014827f28e -->
