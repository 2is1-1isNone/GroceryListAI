import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
PASSPHRASE = os.environ["PASSPHRASE"]
TEMPLATE_PATH = os.environ.get("TEMPLATE_PATH", "/home/red5/groceryai/ShoppingTemplate.md")
AUTHORIZED_USERS_PATH = os.environ.get("AUTHORIZED_USERS_PATH", "/home/red5/groceryai/authorized_users.json")

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def load_authorized_users() -> set[int]:
    path = Path(AUTHORIZED_USERS_PATH)
    if not path.exists():
        return set()
    with open(path) as f:
        return set(json.load(f).get("user_ids", []))


def save_authorized_user(user_id: int):
    users = load_authorized_users()
    users.add(user_id)
    with open(AUTHORIZED_USERS_PATH, "w") as f:
        json.dump({"user_ids": list(users)}, f)


def load_template() -> str:
    with open(TEMPLATE_PATH) as f:
        return f.read()


def process_image_with_claude(image_path: str, template: str) -> str:
    prompt = f"""Look at this grocery list image: {image_path}

Read all the items written on the list. If any items have a line drawn through them (crossed out), note them.

Organize the items using this category template. Output sections in exactly the order they appear:

{template}

Output rules:
- Print each section header exactly as it appears in the template (e.g. =Fruits=)
- List each item on its own line under its section, no bullets or dashes
- Any crossed-out items belong in the =Crossed Out= section
- If you cannot determine the category for an item, place it in =Uncategorized=
- Only include sections that have at least one item
- Output the list only — no explanations, no preamble"""

    claude_bin = os.environ.get("CLAUDE_BIN", "claude")
    result = subprocess.run(
        [claude_bin, "-p", prompt, "--dangerously-skip-permissions"],
        capture_output=True, text=True, timeout=120,
    )
    result.check_returncode()
    return result.stdout.strip()


def format_for_telegram(raw: str) -> str:
    lines = raw.strip().splitlines()
    output: list[str] = []
    in_crossed_out = False

    for line in lines:
        text = line.strip()
        if not text:
            continue

        if text.startswith("="):
            section_name = text.strip("= ").strip()
            in_crossed_out = "crossed out" in section_name.lower()
            output.append(f"\n<b>{text}</b>")
        else:
            item = text.lstrip("•-* ").strip()
            if not item:
                continue
            if in_crossed_out:
                output.append(f"<s>{item}</s>")
            else:
                output.append(f"• {item}")

    return "\n".join(output).strip()


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in load_authorized_users():
        await update.message.reply_text("You're already authorized. Send me a photo of your grocery list!")
    else:
        await update.message.reply_text("Welcome! Send the passphrase to use this bot.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in load_authorized_users():
        await update.message.reply_text("Send me a photo of your grocery list.")
        return

    if (update.message.text or "").strip() == PASSPHRASE:
        save_authorized_user(user_id)
        await update.message.reply_text("Authorized! Send me a photo of your grocery list.")
    else:
        await update.message.reply_text("Incorrect passphrase. Please try again.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in load_authorized_users():
        await update.message.reply_text("Please send the passphrase first. Use /start to begin.")
        return

    await update.message.reply_text("Processing your list — this may take a minute or two...")

    photo_file = await (await context.bot.get_file(update.message.photo[-1].file_id)).download_as_bytearray()

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(photo_file)
        tmp_path = tmp.name

    try:
        categorized = process_image_with_claude(tmp_path, load_template())
        logger.info("Claude output for user %s:\n%s", user_id, categorized)
        formatted = format_for_telegram(categorized)
        await update.message.reply_text(formatted, parse_mode="HTML")
    except subprocess.TimeoutExpired:
        await update.message.reply_text("Request timed out. Please try again in a moment.")
    except Exception:
        logger.exception("Error processing photo for user %s", user_id)
        await update.message.reply_text("Something went wrong processing your list. Please try again.")
    finally:
        os.unlink(tmp_path)


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    logger.info("Bot started, polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
