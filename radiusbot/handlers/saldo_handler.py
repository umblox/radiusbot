# handlers/saldo_handler.py

import mysql.connector
from telegram import Update
from telegram.ext import ContextTypes
from config import logger, DB_CONFIG

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    logger.info("Menerima perintah /saldo dari pengguna %s", telegram_id)

    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor()

    cursor.execute("SELECT balance FROM users WHERE telegram_id = %s", (telegram_id,))
    result = cursor.fetchone()

    if result:
        saldo = result[0]
        await update.message.reply_text(f"Saldo Anda adalah {saldo:.2f} kredit.")
    else:
        await update.message.reply_text("Pengguna tidak ditemukan dalam sistem.")

    cursor.close()
    db.close()
