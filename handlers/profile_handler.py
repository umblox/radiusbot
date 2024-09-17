import mysql.connector
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from config import DB_CONFIG

# Fungsi untuk membuat koneksi ke database
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Fungsi untuk menampilkan profile pelanggan tanpa informasi voucher
async def profile(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Mengambil data user dari tabel `users`
    cursor.execute("SELECT * FROM users WHERE telegram_id=%s", (user_id,))
    user = cursor.fetchone()

    if user:
        # Menyusun pesan profil pelanggan
        profile_message = f"Profil Anda:\n\n"
        profile_message += f"Telegram ID: {user['telegram_id']}\n"
        profile_message += f"Username: @{user['username']}\n"
        profile_message += f"Saldo: {user['balance']} kredit\n"
        profile_message += "Anda hanya boleh mengganti username jika anda benar benar telah mengganti username telegram anda, atau saldo anda bisa hilang.\n\n"
        profile_message += "Masukkan username sesuai username baru telegram anda.\n"

        # Membuat tombol untuk ubah username
        keyboard = [[InlineKeyboardButton("Ubah Username", callback_data="change_username")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(profile_message, reply_markup=reply_markup)
    else:
        await update.message.reply_text("Data Anda tidak ditemukan.")

    cursor.close()
    connection.close()

# Fungsi untuk mengubah username
async def change_username_prompt(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Masukkan username baru yang Anda inginkan:")
    context.user_data['waiting_for_username'] = True  # Flag menunggu input username baru

# Fungsi untuk menerima input username baru dan mengonfirmasi
async def handle_new_username(update: Update, context: CallbackContext):
    if context.user_data.get('waiting_for_username'):
        new_username = update.message.text
        user_id = update.message.from_user.id

        # Simpan username baru ke dalam context untuk konfirmasi
        context.user_data['new_username'] = new_username

        # Minta konfirmasi dari pengguna
        await update.message.reply_text(f"Apakah Anda yakin ingin mengganti username menjadi @{new_username}?",
                                        reply_markup=InlineKeyboardMarkup([
                                            [InlineKeyboardButton("Ya", callback_data="confirm_username_change"),
                                             InlineKeyboardButton("Batal", callback_data="cancel_username_change")]
                                        ]))

        # Hapus flag menunggu input
        context.user_data['waiting_for_username'] = False

# Fungsi untuk konfirmasi pergantian username
async def confirm_username_change(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    # Ambil username baru dari context
    new_username = context.user_data.get('new_username')

    # Simpan username baru ke database
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("UPDATE users SET username=%s WHERE telegram_id=%s", (new_username, user_id))
    connection.commit()

    await query.edit_message_text(f"Username Anda berhasil diubah menjadi @{new_username}.")

    cursor.close()
    connection.close()

# Fungsi untuk membatalkan pergantian username
async def cancel_username_change(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.edit_message_text("Pergantian username dibatalkan.")
