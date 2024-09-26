import random
import string
import mysql.connector
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import CallbackContext
from decimal import Decimal
from datetime import datetime
from config import DB_CONFIG, BOT_TOKEN, ADMIN_ID, VOUCHER_PREFIX  # Import dari config

# Fungsi untuk membuat kode voucher dengan prefix yang sesuai
def generate_voucher_code(planName):
    prefix = VOUCHER_PREFIX.get(planName, '')  # Mengambil prefix dari config.py
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
    return prefix + random_part

# Fungsi untuk koneksi ke database
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)  # Menggunakan konfigurasi dari config.py

# Fungsi untuk menangani pembelian voucher (async)
async def beli(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Menampilkan hanya paket dengan harga lebih dari 0
    cursor.execute("SELECT id, planName, planCost FROM billing_plans WHERE planCost > 0")
    plans = cursor.fetchall()

    if not plans:
        await update.message.reply_text('Tidak ada paket yang tersedia untuk dibeli.')
        cursor.close()
        connection.close()
        return

    keyboard = []
    for plan in plans:
        keyboard.append([InlineKeyboardButton(f"{plan['planName']} - {plan['planCost']}", callback_data=f"confirm_beli_{plan['id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text('Pilih paket yang ingin Anda beli:', reply_markup=reply_markup)

    cursor.close()
    connection.close()

# Fungsi callback untuk konfirmasi sebelum pembelian
async def beli_confirm_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    plan_id = query.data.split('_')[2]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT planName, planCost FROM billing_plans WHERE id=%s", (plan_id,))
    plan = cursor.fetchone()

    if not plan:
        await query.edit_message_text(text="Paket tidak ditemukan.")
        return

    # Menampilkan pesan konfirmasi
    confirmation_message = (
        f"Anda telah memilih paket: {plan['planName']} dengan harga {plan['planCost']}\n\n"
        f"Apakah Anda ingin melanjutkan pembelian?"
    )

    keyboard = [
        [InlineKeyboardButton("Ya", callback_data=f"beli_{plan_id}"),
         InlineKeyboardButton("Batal", callback_data="cancel_beli")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=confirmation_message, reply_markup=reply_markup)

    cursor.close()
    connection.close()

# Fungsi callback saat user membatalkan pembelian
async def beli_cancel_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.edit_message_text("Pembelian dibatalkan. Silakan pilih paket lain.")

# Fungsi callback saat user memilih paket dan mengonfirmasi pembelian (async)
async def beli_callback(update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    telegram_username = query.from_user.username  # Mendapatkan username Telegram pengguna
    plan_id = query.data.split('_')[1]
    chat_id = query.message.chat_id

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT planName, planCost FROM billing_plans WHERE id=%s", (plan_id,))
    plan = cursor.fetchone()

    if not plan:
        await query.edit_message_text(text="Paket tidak ditemukan.")
        return

    cursor.execute("SELECT balance FROM users WHERE telegram_id=%s", (user_id,))
    user = cursor.fetchone()

    if not user or Decimal(user['balance']) < Decimal(plan['planCost']):
        await query.edit_message_text(
            text=f"Saldo Anda tidak mencukupi.\nSaldo saat ini: {user['balance']:.2f}"
        )
        return

    new_balance = Decimal(user['balance']) - Decimal(plan['planCost'])
    cursor.execute("UPDATE users SET balance=%s WHERE telegram_id=%s", (new_balance, user_id))

    voucher_code = generate_voucher_code(plan['planName'])

    cursor.execute("INSERT INTO radcheck (username, attribute, op, value) VALUES (%s, %s, %s, %s)",
                   (voucher_code, 'Auth-Type', ':=', 'Accept'))

    cursor.execute("INSERT INTO radusergroup (username, groupname, priority) VALUES (%s, %s, %s)",
                   (voucher_code, plan['planName'], 1))

    creation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Ubah nilai creationby untuk userinfo
    creationby_value = f"{telegram_username}@Radiusbot"
    cursor.execute(
        "INSERT INTO userinfo (username, creationdate, creationby) "
        "VALUES (%s, %s, %s)",
        (voucher_code, creation_date, creationby_value)
    )

    purchase_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Ubah nilai creationby untuk userbillinfo
    cursor.execute(
        "INSERT INTO userbillinfo (username, planName, paymentmethod, cash, creationdate, creationby) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (voucher_code, plan['planName'], 'cash', str(plan['planCost']), purchase_date, creationby_value)
    )

    connection.commit()

    login_url = f"http://10.10.10.1:3990/login?username={voucher_code}&password=Accept"
    
    keyboard = [
        [InlineKeyboardButton("Login", url=login_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"Voucher anda telah dibuat dengan kode: {voucher_code}\n"
             f"Sisa saldo Anda sekarang: {new_balance:.2f}",
        reply_markup=reply_markup
    )

    # Notifikasi admin tentang pembelian voucher
    admin_message = (
        f"Pengguna dengan username Telegram @{telegram_username} telah berhasil membeli voucher {plan['planName']} melalui radiusbot.\n"
        f"Kode voucher: {voucher_code}\n"
        f"Sisa saldo pengguna: {new_balance:.2f}"
    )

    bot = Bot(token=BOT_TOKEN)  # Menggunakan token dari config.py
    await bot.send_message(chat_id=ADMIN_ID, text=admin_message)  # Menggunakan admin ID dari config.py

    cursor.close()
    connection.close()
