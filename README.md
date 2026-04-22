# GroceryListAI

A Telegram bot that reads a photo of a handwritten grocery list and returns the items organized by store aisle/category using Claude AI.

## How it works

1. Authorize yourself with a passphrase
2. Send the bot a photo of your grocery list
3. Claude reads the image, categorizes each item, and replies with a formatted list organized by your store's layout

Crossed-out items are detected and grouped separately.

## Requirements

- [Claude Code CLI](https://claude.ai/code) installed and authenticated on the server
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Python 3.10+

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/2is1-1isNone/GroceryListAI.git
cd GroceryListAI
```

### 2. Configure environment

```bash
cp config.env.example config.env
```

Edit `config.env` and fill in:

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Telegram bot token from BotFather |
| `PASSPHRASE` | Secret phrase users must send to authorize themselves |
| `TEMPLATE_PATH` | Absolute path to your `ShoppingTemplate.md` on the server |
| `AUTHORIZED_USERS_PATH` | Absolute path to `authorized_users.json` on the server |

### 3. Create your shopping template

```bash
cp ShoppingTemplate.md.example ShoppingTemplate.md
```

Edit `ShoppingTemplate.md` to match your store's layout. Section headers use `=Section Name=` syntax. The bot will categorize items into these sections in the order listed. Add an `=Uncategorized=` section for unknown items and a `=Crossed Out=` section for struck-through items.

### 4. Install to a Linux server

```bash
./install.sh <server-ip>
```

This will:
- Copy project files to the server via SCP
- Set up a Python virtualenv and install dependencies
- Install and start a systemd service (`groceryai`)

The install script takes the remote username as a second argument (defaults to `your_username` if omitted).

### 5. Manual install (optional)

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python bot.py
```

## Files

| File | Description |
|---|---|
| `bot.py` | Main bot logic |
| `config.env.example` | Environment variable template |
| `ShoppingTemplate.md.example` | Store layout template example |
| `groceryai.service` | systemd service unit file |
| `install.sh` | One-command deploy script |
| `requirements.txt` | Python dependencies |

## Notes

- `authorized_users.json` is created automatically on first authorization and should not be committed
- `ShoppingTemplate.md` and `config.env` contain personal data and should not be committed
