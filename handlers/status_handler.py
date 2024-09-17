import mysql.connector
from telegram import Update
from telegram.ext import CallbackContext
from config import DB_CONFIG

# Fungsi untuk membuat koneksi ke database
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Handler untuk perintah /status
async def status(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT username FROM users WHERE telegram_id=%s", (user_id,))
    user = cursor.fetchone()

    if user:
        cursor.execute("SELECT planName, creationdate FROM userbillinfo WHERE username=%s", (user['username'],))
        vouchers = cursor.fetchall()

        if vouchers:
            status_message = "Status voucher Anda:\n\n"
            for voucher in vouchers:
                status_message += f"Plan: {voucher['planName']}\nTanggal Pembelian: {voucher['creationdate']}\n\n"
            await update.message.reply_text(status_message)
        else:
            await update.message.reply_text("Anda tidak memiliki voucher aktif.")
    else:
        await update.message.reply_text("Username Anda tidak ditemukan.")
    
    cursor.close()
    connection.close()
