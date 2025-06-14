# Gemma Function Calling デモ

**言語**: [English](README.md) | **日本語**

FastMCP (Model Control Protocol) を使用した Gemma モデルでの関数呼び出しのデモンストレーションです。このプロジェクトは、ツール呼び出しが失敗した場合やエラーが発生した場合に自動的にリトライロジックを実行するAIエージェントを実装しています。

## クイックスタート

Gemma 3 の関数呼び出しの簡単な紹介については、MCP の複雑さを含まないスタンドアロンデモが含まれている `examples/` ディレクトリを参照してください。

## 前提条件

- Python 3.8+
- [Ollama](https://ollama.ai/) がインストール済みで動作していること
- Gemma 3 モデルがプル済み: `ollama pull gemma3:12b`

## インストール

1. リポジトリをクローン:
```bash
git clone <repository-url>
cd gemma_fn_calling_demo
```

2. 依存関係をインストール:
```bash
pip install -r requirements.txt
```

3. Ollama が Gemma 3 で動作していることを確認:
```bash
ollama run gemma3:12b
```

## 使用方法

### シンプルな例（学習に推奨）

コアコンセプトを示すスタンドアロンの例から始めてください:

```bash
# 基本的な関数呼び出しデモ（MCP なし）
python examples/basic_example.py

# インタラクティブな関数呼び出しデモ
python examples/simple_function_calling.py
```

### 完全な MCP 統合

完全な MCP ベースのシステムの場合:

1. **MCP サーバーを起動**（1つのターミナルで）:
```bash
python app/main.py
```

2. **チャットサーバーを起動**（別のターミナルで）:
```bash
python app/chat_server.py
# サーバーは http://localhost:8001 で動作
```

3. **API をテスト**:
```bash
curl -X POST http://localhost:8001/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "今何時ですか？"}'
```

## 使用例

### 時刻の問い合わせ
```
ユーザー: 今何時ですか？
Gemma: {"tool_call": {"name": "get_time", "arguments": {}}}
関数結果: Current time: 14:30:25
最終回答: 現在の時刻は 14:30:25 です。
```

### 数学計算
```
ユーザー: 15 と 27 を足すといくつ？
Gemma: {"tool_call": {"name": "add_numbers", "arguments": {"a": 15, "b": 27}}}
関数結果: 15 + 27 = 42
最終回答: 15 足す 27 は 42 です。
```

### ツール発見
システムは MCP プロトコルを通じて利用可能なツールを自動的に発見し、モデルのシステムプロンプトに含めます。

## アーキテクチャ

- **MCP サーバー**: `app/main.py` が FastMCP デコレーターを使用してツールを定義
- **MCP クライアント**: `app/mcp_client.py` が Ollama と MCP サーバー間の通信を処理
- **チャットサーバー**: `app/chat_server.py` が MCP クライアントと Ollama を統合する HTTP API を提供
- **ツールシステム**: ツールは `app/tools.py` で定義され、`@mcp.tool()` デコレーターで登録

### 主要機能

- **自動リトライ**: 設定可能な `MAX_LOOPS` セーフティバルブを備えた組み込みリトライメカニズム
- **ツール発見**: MCP サーバーが `list_tools()` API を通じて利用可能なツールを公開
- **JSON ツール呼び出し**: 構造化 JSON 形式を使用: `{"tool_call": {"name": "...", "arguments": {...}}}`
- **エラーハンドリング**: 詳細なログ記録を備えた堅牢なエラーハンドリング

## テスト

すべてのテストを実行:
```bash
python tests/run_all_tests.py
```

または個別のテストカテゴリを実行:
```bash
# Ollama 接続をテスト
python tests/test_ollama.py

# タイムゾーン機能をテスト  
python tests/test_timezone.py

# MCP 接続をテスト
python tests/test_mcp.py

# ツール呼び出しをテスト
python tests/test_tool_call.py

# HTTP API をテスト（サーバーが動作している必要があります）
python tests/test_retry.py
```

pytest を使用:
```bash
python -m pytest tests/ -v
```

## 設定

- モデル設定は `app/config.py`（現在は "gemma3:12b" に設定）
- リトライ制限は `MAX_LOOPS` 定数で制御
- MCP クライアントが自動的にツールを発見し、システムプロンプトを生成

## トラブルシューティング

### モデルが応答しない
- Ollama が動作していることを確認: `ollama list`
- モデルの可用性を確認: `ollama run gemma3:12b`

### JSON パースエラー
- モデルが時々不正な形式の JSON を生成することがあります
- 例にはエラーハンドリングを含む堅牢なパースが含まれています
- 本番環境では リトライロジックを検討してください

### 接続の問題
- MCP サーバーが予期されたポートで動作していることを確認
- 異なるマシンで実行している場合はファイアウォール設定を確認
- すべての依存関係が正しくインストールされていることを確認

## 学習パス

1. **例から始める**: コアコンセプトを理解するために `examples/basic_example.py` を実行
2. **インタラクティブデモを試す**: 実践的な経験のために `examples/simple_function_calling.py` を実行
3. **MCP 統合を探索**: 本番パターンのために `app/` ディレクトリを学習
4. **テストを実行**: 検証パターンを理解するためにテストスイートを使用
5. **ドキュメントを読む**: より深い洞察のために `article_plots/` を確認

## OpenAI との主要な違い

- Gemma 3 は構造化関数呼び出しの代わりに JSON-in-text 形式を使用
- ツール認識のための明示的なプロンプトエンジニアリングが必要
- コンテキスト管理に会話履歴を使用
- カスタム JSON パースロジックが必要

## 貢献

1. リポジトリをフォーク
2. 機能ブランチを作成
3. 新機能のテストを追加
4. すべてのテストが通ることを確認
5. プルリクエストを提出

## ライセンス

[こちらにライセンス情報を追加してください]