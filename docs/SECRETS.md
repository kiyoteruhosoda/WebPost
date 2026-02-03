# シークレット管理

## .envファイルの使用

認証情報などのシークレットは`.env`ファイルで管理します。

### セットアップ

1. `.env.example`をコピー：
```bash
cp .env.example .env
```

2. `.env`ファイルを編集して実際の認証情報を設定：
```
# 任意の環境変数を定義可能
FUNNAVI_FULLTIME_ID=your_actual_id
FUNNAVI_PASSWORD=your_actual_password
API_KEY=your_api_key
DATABASE_URL=postgresql://user:pass@localhost/db
```

**重要**: `.env`ファイルに定義した**すべての変数**がシナリオで利用可能になります。

### シナリオでの使用

シナリオファイルで `${secrets.変数名}` を使ってシークレットを参照：

```json
{
  "id": "login_post",
  "type": "http",
  "request": {
    "method": "POST",
    "url": "/login",
    "form_list": [
      ["fulltimeID", "${secrets.FUNNAVI_FULLTIME_ID}"],
      ["password", "${secrets.FUNNAVI_PASSWORD}"],
      ["apiKey", "${secrets.API_KEY}"]
    ]
  }
}
```

**ポイント**:
- `.env`の変数名をそのまま使用（例: `FUNNAVI_FULLTIME_ID`）
- 変数名は大文字・小文字を区別します
- 存在しない変数を参照するとエラーになります

### 自動マスキング

シークレット値は自動的にログでマスクされます：
```
["fulltimeID", "test_user"], ["password", "********"], ["apiKey", "********"]
```

パスワード、APIキーなどの機密情報を含むキー名は自動的に検出されてマスクされます。

### 実装

- [infrastructure/secrets/env_secret_provider.py](../infrastructure/secrets/env_secret_provider.py)
  - `.env`ファイルを自動的にロード（`python-dotenv`使用）
  - `.env`ファイル内の**すべての変数**を読み込み
  - 環境変数もマージ（`.env`の値が優先）
  - `get()` メソッドですべての変数を辞書として返す

### 汎用性

この実装は完全に汎用的で、任意のプロジェクトで使用できます：

```
# .env ファイル例
DATABASE_URL=postgresql://localhost/mydb
STRIPE_SECRET_KEY=sk_test_xxxxx
SENDGRID_API_KEY=SG.xxxxx
CUSTOM_API_TOKEN=xxxxx
```

シナリオで使用：
```jsonFUNNAVI_FULLTIME_ID": "your_id",
      "FUNNAVI_PASSWORD": "your_password",
      "API_KEY": "your_api_key"
    }
  }'
```

この場合、`.env`ファイルの設定は不要です。任意のキー名を使用できま

### セキュリティ

- `.env`ファイルは `.gitignore` に含まれており、Gitリポジトリにコミットされません
- 本番環境では環境変数として直接設定することも可能
- ログ出力時にパスワードなどの機密情報は自動的にマスクされます

### API経由での実行

REST API経由でシナリオを実行する場合、リクエストボディで直接シークレットを渡すこともできます：

```bash
curl -X POST http://localhost:8000/scenarios/fun_navi_reserve/runs \
  -H "Content-Type: application/json" \
  -d '{
    "vars": {"dates": ["", "2026/02/02"]},
    "secrets": {
      "fulltimeID": "your_id",
      "password": "your_password"
    }
  }'
```

この場合、`.env`ファイルの設定は不要です。
