# NLang_TGBot

这是一个 Telegram 机器人，通过 `/nl <缩写>` 查询 NLang 词条并返回含义。

## 依赖

- Python 3.10+（建议 3.11）
- Telegram Bot Token

## 配置

修改 `config.toml`：

```toml
[bot]
token = "你的机器人 Token"

[server]
endpoint = "https://<你部署的NLang Web Endpoint>"
timeout = 10

[groups]
allowed_ids = [-1001234567890]
```

## 本地运行

```bash
pip3 install -r requirements.txt
python3 nlang_bot.py
```

## Docker 运行

构建镜像：

```bash
docker build -t nlang-tgbot .
```

运行容器（挂载配置文件）：

```bash
docker run -d nlang-tgbot
```

## 说明

- 仅允许在 `allowed_ids` 中的群组使用；否则会返回“没有权限”。
- 日志只记录收到查询请求的事件，不输出每条 HTTP 访问日志。
