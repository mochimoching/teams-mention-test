# Teams メンション監視ツール

Windows 11 の Teams デスクトップアプリで自分宛に届く @メンション通知を捕捉し、標準出力にリアルタイムでログ出力するツールです。

## 仕組み

Teams がメンション通知を送信すると、Windows はその通知を内部の SQLite データベース（`wpndatabase.db`）に記録します。本ツールはこのデータベースを定期的に読み取り、Teams からのトースト通知だけをフィルタリング・XML解析して stdout に出力します。

```
[Teams App] → Windows 通知DB (wpndatabase.db) → [本ツール] → stdout
```

> **Note**: Teams Graph API やBot Framework は使用していません。Windows がローカルに保持する通知データベースのみで動作します。
> WinRT の `UserNotificationListener` API は UWP アプリ専用のため使用せず、SQLite DB 直接読み取り方式を採用しています。

## 動作要件

| 要件 | 詳細 |
|------|------|
| OS | Windows 11 |
| Python | 3.12 以上（3.14 で動作確認済み） |
| Teams | 新しい Teams デスクトップアプリ (Teams 2.0 / MSIX版) |
| 外部パッケージ | なし（Python 標準ライブラリのみ。テスト実行時のみ `pytest` が必要） |

## 事前設定

### 1. Windows の通知設定

本ツールが通知を検出するには、Teams がトースト通知を送信している必要があります。

1. **Teams の通知を有効にする**
   - `設定` → `システム` → `通知` を開く
   - 「通知」がオンになっていることを確認
   - アプリ一覧から **Microsoft Teams** を見つけ、通知がオンになっていることを確認

> 本ツールは Windows の通知データベースファイル（`%LocalAppData%\Microsoft\Windows\Notifications\wpndatabase.db`）を読み取ります。特別なアクセス許可設定は不要です。

### 2. Teams アプリの確認

- Teams デスクトップアプリがインストール済みで、サインイン済みであること
- Teams 内の通知設定（`設定` → `通知とアクティビティ`）でメンション通知が有効であること

> **制限事項**: Teams がフォアグラウンドで該当チャネルを表示中の場合、Windows のトースト通知が抑制されることがあります。その場合、本ツールでは検出できません。

## インストール

```powershell
# リポジトリをクローン
git clone <repository-url>
cd teams-mention-test

# 依存パッケージをインストール
python -m pip install -r requirements.txt
```

### 依存パッケージ

実行時の外部パッケージ依存は **ありません**。Python 標準ライブラリ（`sqlite3`, `xml.etree.ElementTree`, `time`, `argparse`）のみで動作します。

| パッケージ | 用途 |
|-----------|------|
| `pytest` | テスト実行（開発用） |

> **Note**: 初期の設計では WinRT の `UserNotificationListener` API を使用する予定でしたが、この API は UWP アプリ専用であり通常の Python スクリプトからは `E_NOTIMPL` エラーになるため、Windows 通知データベース直接読み取り方式に変更しました。

## 使い方

### 基本: 特定の名前のメンションを監視

```powershell
python -m src.main --name "山田太一"
```

自分の Teams 表示名を `--name` に指定すると、`@山田太一` を含む通知だけを出力します。部分一致にも対応しており、`@山田` のような省略形も検出します。

### 全 Teams 通知を監視

```powershell
python -m src.main
```

`--name` を省略すると、Teams からの全通知を出力します。

### ポーリング間隔を変更

```powershell
python -m src.main --name "山田太一" --interval 3
```

デフォルトは 5 秒間隔です。`--interval` で秒数を指定できます。

### 出力例

```
[2026-02-17 10:23:45] 一般 | プロジェクトA | 佐藤次郎: @山田太一 今日の会議の資料を確認してください
[2026-02-17 10:30:12] 高橋花子: @山田太一 確認お願いします
[2026-02-17 11:05:33] 開発チーム | 山田一郎: @all 全員ミーティングに参加してください
```

| フォーマット | 条件 |
|-------------|------|
| `[timestamp] チャネル \| 送信者: メッセージ` | チャネルメンション |
| `[timestamp] 送信者: メッセージ` | ダイレクトチャット |
| `[timestamp] メッセージ` | 送信者不明の通知 |

### 停止

`Ctrl+C` で安全に停止します。

## コマンドオプション一覧

| オプション | 型 | デフォルト | 説明 |
|-----------|-----|----------|------|
| `--name` | 文字列 | なし（全通知） | 監視対象の Teams 表示名 |
| `--interval` | 数値 | 5.0 | ポーリング間隔（秒） |

## メンション検出ルール

| パターン | 検出 | 例 |
|----------|------|-----|
| `@<完全な表示名>` | ○ | `@山田太一` |
| `@<表示名の先頭部分>` | ○ | `@山田` |
| `@all` | ○（常に検出） | `@all 確認してください` |
| `@everyone` | ○（常に検出） | `@everyone 会議です` |
| 英語名（大文字小文字不問） | ○ | `@john.smith` = `@John.Smith` |

## テスト

```powershell
# 全テスト実行
python -m pytest tests/ -v

# 個別モジュールのテスト
python -m pytest tests/test_teams_parser.py -v
python -m pytest tests/test_notification_listener.py -v
python -m pytest tests/test_main.py -v
```

## プロジェクト構成

```
teams-mention-test/
├── README.md                              # 本ファイル
├── requirements.txt                       # 依存パッケージ
├── pyproject.toml                         # プロジェクト設定
├── src/
│   ├── __init__.py
│   ├── config.py                          # 設定値
│   ├── teams_parser.py                    # 通知テキスト解析・メンション判定
│   ├── notification_listener.py           # Windows通知DB読み取り
│   └── main.py                            # エントリポイント・CLIコマンド
└── tests/
    ├── __init__.py
    ├── test_teams_parser.py               # パーサーテスト (14件)
    ├── test_notification_listener.py      # DB読み取りテスト (12件)
    └── test_main.py                       # メインモジュールテスト (10件)
```

## トラブルシューティング

### 通知が検出されない

1. **Teams の通知設定を確認**: Teams アプリ内の `設定` → `通知とアクティビティ` でメンション通知がオンか確認
2. **Windows の通知設定を確認**: `設定` → `システム` → `通知` で Teams の通知がオンか確認
3. **Teams のフォーカス状態を確認**: メンションされたチャネルを Teams で開いている場合、OS 通知が抑制されることがあります
4. **集中モード（応答不可）を確認**: Windows の集中モードがオンだと通知が抑制されます
5. **通知DBの存在を確認**: `%LocalAppData%\Microsoft\Windows\Notifications\wpndatabase.db` が存在するか確認

### `Skipped 0 existing notification(s).` と表示されるが通知が検出されない

Teams の通知がDB内で期限切れになっている可能性があります。Teams で新しいメンション通知を発生させてからしばらく待ってください。

### 技術的な補足: なぜ WinRT API を使わないのか

当初 `UserNotificationListener` API（WinRT）を使う設計でしたが、この API は UWP アプリ（パッケージ化されたアプリ）専用です。通常の Python スクリプトから呼び出すと `E_NOTIMPL (0x80004001)` エラーになります。そのため、Windows が内部に保持する通知データベース（SQLite）を直接読み取る方式を採用しています。
