import logging
import sys

import httpx

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, InlineQueryHandler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def load_config(path: str = "config.toml") -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


async def nl_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /nl <缩写> 指令，查询 NLang 词条并回复。"""
    config: dict = context.bot_data["config"]
    allowed_ids: list = config["groups"]["allowed_ids"]

    # 限制只在允许的群组中使用
    chat_id = update.effective_chat.id
    if chat_id not in allowed_ids:
        if update.effective_message:
            await update.effective_message.reply_text("⚠️ 没有权限")
        return

    if not context.args:
        await update.message.reply_text("❌ 用法：/nl <缩写>\n例如：/nl nlk")
        return

    abbrev = context.args[0].strip()
    logger.info("收到查询请求 chat_id=%s abbrev=%s", chat_id, abbrev)
    endpoint: str = config["server"]["endpoint"].rstrip("/")
    url = f"{endpoint}/api/entries"
    timeout: float = config["server"].get("timeout", 10)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params={"abbr": abbrev})
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        await update.message.reply_text("⚠️ 请求超时，请稍后再试。")
        return
    except httpx.HTTPStatusError as exc:
        await update.message.reply_text(f"⚠️ 服务器返回错误：{exc.response.status_code}")
        return
    except Exception as exc:
        logger.exception("查询时发生未知错误：%s", exc)
        await update.message.reply_text("⚠️ 查询时发生未知错误，请稍后再试。")
        return

    items: list = data if isinstance(data, list) else []
    if not items:
        await update.message.reply_text(f"🔍 未找到缩写「{abbrev}」的相关词条。")
        return

    lines = [f"🔤 缩写「{abbrev}」的含义如下：\n"]
    for idx, item in enumerate(items, start=1):
        value = item.get("value", "（无）")
        lines.append(f"  {idx}. {value}")

    await update.message.reply_text("\n".join(lines))


async def nl_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 inline query，通过 @botname <缩写> 直接查询 NLang 词条。"""
    abbrev = update.inline_query.query.strip()
    if not abbrev:
        await update.inline_query.answer([])
        return

    config: dict = context.bot_data["config"]
    endpoint: str = config["server"]["endpoint"].rstrip("/")
    url = f"{endpoint}/api/entries"
    timeout: float = config["server"].get("timeout", 10)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params={"abbr": abbrev})
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        logger.exception("inline query 查询时发生错误：%s", exc)
        await update.inline_query.answer([])
        return

    items: list = data if isinstance(data, list) else []
    if not items:
        result = InlineQueryResultArticle(
            id="not_found",
            title=f"未找到「{abbrev}」的相关词条",
            input_message_content=InputTextMessageContent(
                f"🔍 未找到缩写「{abbrev}」的相关词条。"
            ),
        )
        await update.inline_query.answer([result])
        return

    lines = [f"🔤 缩写「{abbrev}」的含义如下：\n"]
    for idx, item in enumerate(items, start=1):
        value = item.get("value", "（无）")
        lines.append(f"  {idx}. {value}")

    description = ", ".join(m for item in items[:3] if (m := item.get("value")))
    result = InlineQueryResultArticle(
        id=str(hash(abbrev)),
        title=f"缩写「{abbrev}」的含义",
        description=description,
        input_message_content=InputTextMessageContent("\n".join(lines)),
    )
    await update.inline_query.answer([result])


def main() -> None:
    try:
        config = load_config()
    except FileNotFoundError:
        logger.error("找不到配置文件 config.toml，请检查文件是否存在。")
        sys.exit(1)
    except Exception as exc:
        logger.error("读取配置文件时出错：%s", exc)
        sys.exit(1)

    token: str = config["bot"]["token"]

    app = ApplicationBuilder().token(token).build()
    app.bot_data["config"] = config

    app.add_handler(CommandHandler("nl", nl_command))
    app.add_handler(InlineQueryHandler(nl_inline_query))

    logger.info("NLang TGBot 已启动，等待指令中……")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
