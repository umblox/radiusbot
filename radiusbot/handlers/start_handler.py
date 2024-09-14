import mysql.connector
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler

# ID Admin
ADMIN_ID = 2123457759  # Ganti dengan ID Admin Anda

# Fungsi untuk koneksi ke database
def get_db_connection():
    return mysql.connector.connect(
        user='radius',
        password='radius',
        host='127.0.0.1',
        database='radius'
    )

# Fungsi untuk menangani command /start
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    
    # Cek apakah username ada
    if not username:
        await update.message.reply_text(
            "Anda harus memasang username di Telegram terlebih dahulu untuk menggunakan bot ini. "
            "Silakan pasang username di pengaturan Telegram, kemudian coba lagi dengan perintah /start."
        )
        return

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Cek jika pengguna sudah ada
    cursor.execute("SELECT id FROM users WHERE telegram_id=%s", (user_id,))
    existing_user = cursor.fetchone()

    if not existing_user:
        # Jika pengguna baru, masukkan ke dalam database
        cursor.execute("INSERT INTO users (telegram_id, username, balance) VALUES (%s, %s, %s)",
                       (user_id, username, 0))
        connection.commit()

        # Kirim notifikasi ke admin
        admin_message = f"Pengguna baru mendaftar:\n\nID Pengguna: {user_id}\nUsername: @{username}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

    # Sambutan untuk pengguna baru dan daftar perintah
    welcome_message = (
        f"Selamat datang di bot billing arneta.id!\n\n"
        f"Berikut rincian akun Anda:\n"
        f"ID Pengguna: {user_id}\n"
        f"Username: @{username}\n\n"
        f"Daftar perintah yang tersedia:\n"
        f"/profile - Untuk melihat profile anda\n"
        f"/topup - Untuk isi ulang saldo\n"
        f"/beli - Untuk membeli voucher\n"
        f"/saldo - Untuk mengecek saldo Anda"
    )
    await update.message.reply_text(welcome_message)

    cursor.close()
    connection.close()

# Tambahkan handler untuk /start
def main():
    from telegram.ext import Application

    application = Application.builder().token("7530717438:AAFDpkb15BzqvjJx8-jNDT-Kg6JS0uhgbuo").build()

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
