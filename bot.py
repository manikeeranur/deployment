#!/usr/bin/env python3
"""
SMC Deployment Bot
Runs ON the EC2 server and executes deploy scripts locally.
"""

import os
import subprocess
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

load_dotenv()

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BOT_TOKEN       = os.getenv("BOT_TOKEN", "")
ALLOWED_IDS_RAW = os.getenv("ALLOWED_CHAT_IDS", "")
ALLOWED_IDS     = set(int(x.strip()) for x in ALLOWED_IDS_RAW.split(",") if x.strip())
SCRIPTS_DIR     = os.path.join(os.path.dirname(__file__), "scripts")
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def run_script(script_name: str, timeout: int = 300) -> tuple[str, bool]:
    """Execute a shell script and return (output, success)."""
    path = os.path.join(SCRIPTS_DIR, script_name)
    try:
        result = subprocess.run(
            ["bash", path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (result.stdout + result.stderr).strip()
        return output, result.returncode == 0
    except subprocess.TimeoutExpired:
        return f"ERROR: Script timed out after {timeout}s", False
    except Exception as exc:
        return f"ERROR: {exc}", False


def fmt(output: str, max_len: int = 3800) -> str:
    """Trim output for Telegram's 4096-char message limit."""
    if len(output) > max_len:
        return output[:max_len] + "\n...(truncated)"
    return output


def authorized(update: Update) -> bool:
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_IDS:
        logger.warning("Unauthorized access attempt from chat_id=%s", chat_id)
        return False
    return True


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 Deploy Frontend", callback_data="deploy_frontend"),
            InlineKeyboardButton("⚙️ Deploy Backend",  callback_data="deploy_backend"),
        ],
        [
            InlineKeyboardButton("🔄 Deploy All",   callback_data="deploy_all"),
            InlineKeyboardButton("📊 Server Status", callback_data="status"),
        ],
        [
            InlineKeyboardButton("📋 Frontend Logs", callback_data="logs_frontend"),
            InlineKeyboardButton("📋 Backend Logs",  callback_data="logs_backend"),
        ],
        [
            InlineKeyboardButton("🔁 Restart All PM2", callback_data="confirm_restart"),
        ],
    ])


# ─── COMMAND HANDLERS ─────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update):
        await update.message.reply_text("⛔ Unauthorized.")
        return
    await update.message.reply_text(
        "🤖 *SMC Deployment Bot*\n\n"
        "EC2: `13.61.175.6`\n"
        "Frontend: Next.js (port 3000)\n"
        "Backend:  Express.js (port 4000)\n\n"
        "Choose an action:",
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )


async def cmd_deploy_frontend(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update): return
    msg = await update.message.reply_text("⏳ Deploying Frontend…")
    output, ok = run_script("deploy_frontend.sh")
    icon = "✅" if ok else "❌"
    await msg.edit_text(
        f"{icon} *Frontend Deploy* `{datetime.now().strftime('%H:%M:%S')}`\n\n"
        f"<pre>{fmt(output)}</pre>",
        parse_mode="HTML",
    )


async def cmd_deploy_backend(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update): return
    msg = await update.message.reply_text("⏳ Deploying Backend…")
    output, ok = run_script("deploy_backend.sh")
    icon = "✅" if ok else "❌"
    await msg.edit_text(
        f"{icon} <b>Backend Deploy</b> <code>{datetime.now().strftime('%H:%M:%S')}</code>\n\n"
        f"<pre>{fmt(output)}</pre>",
        parse_mode="HTML",
    )


async def cmd_deploy_all(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update): return
    msg = await update.message.reply_text("⏳ Deploying Backend + Frontend…")
    output, ok = run_script("deploy_all.sh", timeout=600)
    icon = "✅" if ok else "❌"
    await msg.edit_text(
        f"{icon} <b>Full Deploy</b> <code>{datetime.now().strftime('%H:%M:%S')}</code>\n\n"
        f"<pre>{fmt(output)}</pre>",
        parse_mode="HTML",
    )


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update): return
    msg = await update.message.reply_text("📊 Fetching server status…")
    output, ok = run_script("status.sh")
    icon = "✅" if ok else "❌"
    await msg.edit_text(
        f"{icon} <b>Server Status</b>\n\n<pre>{fmt(output)}</pre>",
        parse_mode="HTML",
    )


async def cmd_logs_frontend(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update): return
    msg = await update.message.reply_text("📋 Fetching Frontend logs…")
    output, ok = run_script_inline("pm2 logs SMC-Frontend --lines 50 --nostream")
    await msg.edit_text(
        f"📋 <b>Frontend Logs</b>\n\n<pre>{fmt(output)}</pre>",
        parse_mode="HTML",
    )


async def cmd_logs_backend(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update): return
    msg = await update.message.reply_text("📋 Fetching Backend logs…")
    output, ok = run_script_inline("pm2 logs SMC-Backend --lines 50 --nostream")
    await msg.edit_text(
        f"📋 <b>Backend Logs</b>\n\n<pre>{fmt(output)}</pre>",
        parse_mode="HTML",
    )


async def cmd_restart(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update): return
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Yes, restart all", callback_data="do_restart"),
        InlineKeyboardButton("❌ Cancel",            callback_data="cancel"),
    ]])
    await update.message.reply_text(
        "⚠️ Restart ALL PM2 processes?",
        reply_markup=keyboard,
    )


# ─── INLINE HELPER ────────────────────────────────────────────────────────────

def run_script_inline(cmd: str, timeout: int = 60) -> tuple[str, bool]:
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return (result.stdout + result.stderr).strip(), result.returncode == 0
    except Exception as exc:
        return f"ERROR: {exc}", False


# ─── BUTTON HANDLER ───────────────────────────────────────────────────────────

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.message.chat.id not in ALLOWED_IDS:
        await query.edit_message_text("⛔ Unauthorized.")
        return

    action = query.data

    # ── Deploy Frontend ──
    if action == "deploy_frontend":
        await query.edit_message_text("⏳ Deploying Frontend…")
        output, ok = run_script("deploy_frontend.sh")
        icon = "✅" if ok else "❌"
        await query.edit_message_text(
            f"{icon} <b>Frontend Deploy</b> <code>{datetime.now().strftime('%H:%M:%S')}</code>\n\n"
            f"<pre>{fmt(output)}</pre>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back", callback_data="back_menu")
            ]]),
        )

    # ── Deploy Backend ──
    elif action == "deploy_backend":
        await query.edit_message_text("⏳ Deploying Backend…")
        output, ok = run_script("deploy_backend.sh")
        icon = "✅" if ok else "❌"
        await query.edit_message_text(
            f"{icon} <b>Backend Deploy</b> <code>{datetime.now().strftime('%H:%M:%S')}</code>\n\n"
            f"<pre>{fmt(output)}</pre>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back", callback_data="back_menu")
            ]]),
        )

    # ── Deploy All ──
    elif action == "deploy_all":
        await query.edit_message_text("⏳ Deploying Backend + Frontend (may take ~3 min)…")
        output, ok = run_script("deploy_all.sh", timeout=600)
        icon = "✅" if ok else "❌"
        await query.edit_message_text(
            f"{icon} <b>Full Deploy</b> <code>{datetime.now().strftime('%H:%M:%S')}</code>\n\n"
            f"<pre>{fmt(output)}</pre>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back", callback_data="back_menu")
            ]]),
        )

    # ── Status ──
    elif action == "status":
        await query.edit_message_text("📊 Fetching status…")
        output, ok = run_script("status.sh")
        icon = "✅" if ok else "❌"
        await query.edit_message_text(
            f"{icon} <b>Server Status</b>\n\n<pre>{fmt(output)}</pre>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Refresh", callback_data="status"),
                InlineKeyboardButton("« Back",     callback_data="back_menu"),
            ]]),
        )

    # ── Frontend Logs ──
    elif action == "logs_frontend":
        await query.edit_message_text("📋 Fetching Frontend logs…")
        output, _ = run_script_inline("pm2 logs SMC-Frontend --lines 50 --nostream")
        await query.edit_message_text(
            f"📋 <b>Frontend Logs</b>\n\n<pre>{fmt(output)}</pre>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Refresh", callback_data="logs_frontend"),
                InlineKeyboardButton("« Back",     callback_data="back_menu"),
            ]]),
        )

    # ── Backend Logs ──
    elif action == "logs_backend":
        await query.edit_message_text("📋 Fetching Backend logs…")
        output, _ = run_script_inline("pm2 logs SMC-Backend --lines 50 --nostream")
        await query.edit_message_text(
            f"📋 <b>Backend Logs</b>\n\n<pre>{fmt(output)}</pre>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Refresh", callback_data="logs_backend"),
                InlineKeyboardButton("« Back",     callback_data="back_menu"),
            ]]),
        )

    # ── Restart confirmation ──
    elif action == "confirm_restart":
        await query.edit_message_text(
            "⚠️ Restart ALL PM2 processes?\nThis will briefly interrupt both apps.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Yes, restart", callback_data="do_restart"),
                InlineKeyboardButton("❌ Cancel",       callback_data="back_menu"),
            ]]),
        )

    elif action == "do_restart":
        await query.edit_message_text("🔁 Restarting all PM2 processes…")
        output, ok = run_script_inline("pm2 restart all && pm2 list")
        icon = "✅" if ok else "❌"
        await query.edit_message_text(
            f"{icon} <b>PM2 Restart</b>\n\n<pre>{fmt(output)}</pre>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back", callback_data="back_menu")
            ]]),
        )

    # ── Back to menu ──
    elif action == "back_menu" or action == "cancel":
        await query.edit_message_text(
            "🤖 *SMC Deployment Bot*\n\n"
            "EC2: `13.61.175.6`\n"
            "Frontend: Next.js (port 3000)\n"
            "Backend:  Express.js (port 4000)\n\n"
            "Choose an action:",
            parse_mode="Markdown",
            reply_markup=main_keyboard(),
        )


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set in .env")
    if not ALLOWED_IDS:
        raise ValueError("ALLOWED_CHAT_IDS is not set in .env")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",            cmd_start))
    app.add_handler(CommandHandler("deploy_frontend",  cmd_deploy_frontend))
    app.add_handler(CommandHandler("deploy_backend",   cmd_deploy_backend))
    app.add_handler(CommandHandler("deploy_all",       cmd_deploy_all))
    app.add_handler(CommandHandler("status",           cmd_status))
    app.add_handler(CommandHandler("logs_frontend",    cmd_logs_frontend))
    app.add_handler(CommandHandler("logs_backend",     cmd_logs_backend))
    app.add_handler(CommandHandler("restart",          cmd_restart))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("SMC Deploy Bot started. Authorized IDs: %s", ALLOWED_IDS)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
