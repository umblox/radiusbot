import mysql.connector
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from config import DB_CONFIG

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fungsi untuk membuat koneksi ke database
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Fungsi untuk menampilkan profile pelanggan tanpa informasi voucher
async def profile(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    try:
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
            profile_message += "Anda hanya boleh mengganti username jika Anda benar-benar telah mengganti username Telegram Anda, atau saldo Anda bisa hilang.\n\n"
            profile_message += "Masukkan username sesuai username baru Telegram Anda.\n"

            # Membuat tombol untuk ubah username dan password
            keyboard = [
                [InlineKeyboardButton("Ubah Username", callback_data="change_username")],
                [InlineKeyboardButton("Lihat Password", callback_data="show_password")],
                [InlineKeyboardButton("Ubah Password", callback_data="change_password")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(profile_message, reply_markup=reply_markup)
        else:
            await update.message.reply_text("Data Anda tidak ditemukan.")

        cursor.close()
        connection.close()
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")

# Fungsi untuk memulai perubahan username
async def set_username_prompt(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Masukkan username baru yang Anda inginkan:")
    context.user_data['waiting_for_username'] = True  # Flag menunggu input username baru

# Fungsi untuk menangani input username baru
#async def handle_new_username(update: Update, context: CallbackContext):
#    if context.user_data.get('waiting_for_username'):
#        new_username = update.message.text
#        user_id = update.message.from_user.id
#
        # Logging username baru
#        logger.info(f"New username: {new_username} for user {user_id}")

        # Simpan username baru ke dalam context
#        context.user_data['new_username'] = new_username
#
        # Minta konfirmasi dari pengguna
#        await update.message.reply_text(
#            f"Username baru yang akan Anda gunakan adalah :  @{new_username}.
#            f"Username harus sesuai dengan username telegram Anda. 
#            f"Apakah Anda ingin mengonfirmasi?",
#            reply_markup=InlineKeyboardMarkup([
#                [InlineKeyboardButton("Ya", callback_data="confirm_username_change")],
#                [InlineKeyboardButton("Batal", callback_data="cancel_username_change")]
#            ])
#        )
#
        # Jangan hapus status 'change_username' di sini agar tetap menunggu konfirmasi

# Fungsi untuk mengonfirmasi perubahan username
async def confirm_username_change(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    new_username = context.user_data.get('new_username')

    if new_username:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("UPDATE users SET username=%s WHERE telegram_id=%s", (new_username, user_id))
            connection.commit()

            await query.edit_message_text(f"Username Anda telah diubah menjadi @{new_username}.")
            
            # Hapus data username setelah konfirmasi berhasil
            context.user_data.pop('new_username', None)
            context.user_data.pop('waiting_for_username', None)  # Reset flag agar tidak terkunci

            cursor.close()
            connection.close()

        except Exception as e:
            logger.error(f"Error updating username: {e}")
            await query.edit_message_text("Terjadi kesalahan saat mengubah username. Silakan coba lagi.")
    else:
        await query.edit_message_text("Tidak ada username baru yang ditemukan.")

# Fungsi untuk membatalkan perubahan username
async def cancel_username_change(update: Update, context: CallbackContext):
    query = update.callback_query

    await query.edit_message_text("Perubahan username dibatalkan.")
    
    # Hapus flag perubahan username
    context.user_data.pop('waiting_for_username', None)
    context.user_data.pop('new_username', None)

# Fungsi untuk menampilkan password pengguna (misalnya jika disimpan dalam database)
async def show_password(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    try:
        # Ambil password dari database berdasarkan telegram_id
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT password FROM users WHERE telegram_id=%s", (user_id,))
        result = cursor.fetchone()

        if result:
            password = result[0]

            # Menampilkan password dengan tombol "Tutup"
            await query.edit_message_text(
                f"Password Anda adalah: {password}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Tutup", callback_data="close_message")]
                ])
            )
        else:
            await query.edit_message_text("Password tidak ditemukan.")

        cursor.close()
        connection.close()

    except Exception as e:
        logger.error(f"Error showing password: {e}")
        await query.edit_message_text("Terjadi kesalahan saat mengambil password.")

# Fungsi untuk menutup pesan (menghapus pesan yang ada)
async def close_message(update: Update, context: CallbackContext):
    query = update.callback_query

    # Menghapus pesan dengan password saat tombol "Tutup" diklik
    await query.delete_message()

# Fungsi untuk menerima input password baru dan meminta konfirmasi
#async def handle_new_password(update: Update, context: CallbackContext):
#    if context.user_data.get('waiting_for_password'):
#      new_password = update.message.text
#        user_id = update.message.from_user.id
#
        # Logging password baru
#        logger.info(f"New password: {new_password} for user {user_id}")

        # Simpan password baru ke dalam context
#        context.user_data['new_password'] = new_password

        # Minta konfirmasi
#        await update.message.reply_text(
#            f"Apakah Anda yakin ingin mengganti password dengan {new_password}?",
#            reply_markup=InlineKeyboardMarkup([
#                [InlineKeyboardButton("Ya", callback_data="confirm_password_change")],
#                [InlineKeyboardButton("Batal", callback_data="cancel_password_change")]
#            ])
#        )
#    else:
#        logger.info("change_password state not set")
        # Jangan hapus status 'change_password' di sini agar tetap menunggu konfirmasi

# Fungsi untuk memulai proses pengaturan password baru
async def set_password_prompt(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Masukkan password baru yang Anda inginkan:")
    context.user_data['waiting_for_password'] = True  # Flag menunggu input password baru

# Fungsi untuk mengonfirmasi perubahan password
async def confirm_password_change(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    new_password = context.user_data.get('new_password')

    if new_password:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("UPDATE users SET password=%s WHERE telegram_id=%s", (new_password, user_id))
            connection.commit()

            await query.edit_message_text(f"Password Anda berhasil diubah.")

            # Hapus data password setelah konfirmasi berhasil
            context.user_data.pop('new_password', None)
            context.user_data.pop('waiting_for_password', None)  # Reset flag agar tidak terkunci

            cursor.close()
            connection.close()

        except Exception as e:
            logger.error(f"Error updating password: {e}")
            await query.edit_message_text("Terjadi kesalahan saat mengubah password. Silakan coba lagi.")
    else:
        await query.edit_message_text("Tidak ada password baru yang ditemukan.")

# Fungsi untuk membatalkan perubahan password
async def cancel_password_change(update: Update, context: CallbackContext):
    query = update.callback_query

    await query.edit_message_text("Perubahan password dibatalkan.")
    
    # Hapus flag perubahan password
    context.user_data.pop('waiting_for_password', None)
    context.user_data.pop('new_password', None)

# Fungsi untuk menangani input dari user saat mengubah username atau password
async def handle_user_input(update: Update, context: CallbackContext):
    if context.user_data.get('waiting_for_username'):
        new_username = update.message.text
        context.user_data['new_username'] = new_username

        # Minta konfirmasi username
        await update.message.reply_text(
            f"Username baru Anda adalah: {new_username}. Apakah Anda ingin mengonfirmasi?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Ya", callback_data="confirm_username_change")],
                [InlineKeyboardButton("Batal", callback_data="cancel_username_change")]
            ])
        )

    elif context.user_data.get('waiting_for_password'):
        new_password = update.message.text
        context.user_data['new_password'] = new_password

        # Minta konfirmasi password
        await update.message.reply_text(
            f"Apakah Anda yakin ingin mengganti password menjadi {new_password}?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Ya", callback_data="confirm_password_change")],
                [InlineKeyboardButton("Batal", callback_data="cancel_password_change")]
            ])
        )

    else:
        # Jika tidak ada flag yang aktif
        await update.message.reply_text('Tidak ada perubahan yang diproses.')
