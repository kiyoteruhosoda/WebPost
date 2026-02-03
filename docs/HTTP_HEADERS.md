# HTTPヘッダー自動設定

## User-Agent

シナリオの`meta.user_agent`で定義したUser-Agentが、すべてのHTTPリクエストに自動的に設定されます。

### 設定方法

シナリオファイルの`meta`セクションに`user_agent`を追加：

```json
{
  "meta": {
    "id": 1,
    "name": "my-scenario",
    "version": 1,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
  },
  "steps": [...]
}
```

### デフォルト値

`user_agent`を指定しない場合、デフォルトで `"ScenarioRunner/1.0"` が使用されます。

### 実装

- [domain/scenario.py](../domain/scenario.py) - `ScenarioMeta.user_agent`
- [application/handlers/http_handler.py](../application/handlers/http_handler.py) - リクエスト時に`ctx.scenario.meta.user_agent`から取得

## Referer

前のHTTPリクエストのURLが、次のリクエストの`Referer`ヘッダーに自動的に設定されます。

### 動作

1. **最初のリクエスト**: Refererなし
2. **2番目以降のリクエスト**: 前のリクエストのURLがRefererに設定される

例：
```
1. GET /login           → Referer: なし
2. POST /login          → Referer: https://example.com/login
3. POST /submit         → Referer: https://example.com/login
```

### 仕組み

- `RunContext.last.url` に前のリクエストのURLが保存される
- `HttpStepHandler` が次のリクエスト時に `Referer` ヘッダーに設定

### 上書き

ステップで明示的に`Referer`ヘッダーを指定した場合、そちらが優先されます：

```json
{
  "id": "custom_request",
  "type": "http",
  "request": {
    "method": "POST",
    "url": "/api/endpoint",
    "headers": {
      "Referer": "https://custom-referer.com"
    }
  }
}
```

## Cookie

`requests.Session`を使用しているため、Cookieは自動的に管理されます：

- レスポンスの`Set-Cookie`ヘッダーからCookieを自動保存
- 次のリクエストで同じドメインへのリクエストに自動的に`Cookie`ヘッダーを追加

## ログ出力

HTTPリクエストのヘッダーはログに出力されます：

```json
{
  "headers": {
    "User-Agent": "Mozilla/5.0 ...",
    "Referer": "https://fun-navi.net/FRPC010G_LoginAction.do",
    "Accept": "text/html",
    "Cookie": "JSESSIONID=xxxxx"
  }
}
```

パスワードなどの機密情報は自動的にマスクされます。

## まとめ

| ヘッダー | 設定方法 | 優先順位 |
|---------|---------|---------|
| User-Agent | meta.user_agent | 1. ステップのheaders<br>2. meta.user_agent<br>3. デフォルト値 |
| Referer | 自動（前のURL） | 1. ステップのheaders<br>2. 前のリクエストURL<br>3. なし |
| Cookie | 自動（Session） | requests.Session が自動管理 |

この仕組みにより、ブラウザと同じような自然なHTTPリクエストを送信できます。
