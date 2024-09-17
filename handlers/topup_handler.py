import mysql.connector
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from config import logger, DB_CONFIG, ADMIN_ID

# Fungsi untuk permintaan top-up
async def topup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    telegram_username = update.message.from_user.username

    if not telegram_username:
        await update.message.reply_text("Anda harus memiliki username Telegram untuk melakukan top-up.")
        return

    logger.info("Menerima permintaan /topup dari pengguna %s (%s)", telegram_id, telegram_username)
    
    amounts = [5000, 10000, 20000, 50000, 100000]
    keyboard = [[InlineKeyboardButton(f"Top-up {amount} kredit", callback_data=f"topup,{amount}")] for amount in amounts]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Pilih jumlah top-up:", reply_markup=reply_markup)

# Fungsi untuk menangani callback dari pilihan top-up
async def handle_topup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    telegram_id = query.from_user.id
    telegram_username = query.from_user.username

    if not telegram_username:
        await query.edit_message_text("Anda harus memiliki username Telegram untuk melakukan top-up.")
        return

    # Memproses pilihan top-up yang sudah ditentukan
    _, amount = data.split(",")
    amount = int(amount)
    logger.info("Pengguna %s (%s) memilih top-up sebesar %s kredit", telegram_id, telegram_username, amount)

    # Cek apakah permintaan top-up sudah ada
    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor()

    # Tambahkan pengecekan berdasarkan username, amount, dan timestamp
    cursor.execute("""
        SELECT COUNT(*) 
        FROM topup_requests 
        WHERE user_id = %s 
        AND amount = %s 
        AND status = 'pending'
        AND created_at >= NOW() - INTERVAL 1 DAY
    """, (telegram_id, amount))
    result = cursor.fetchone()
    if result[0] > 0:
        await query.edit_message_text("Anda sudah memiliki permintaan top-up yang menunggu konfirmasi untuk jumlah ini.")
        cursor.close()
        db.close()
        return

    # Simpan permintaan top-up dengan status 'pending'
    cursor.execute("INSERT INTO topup_requests (user_id, username, amount, status) VALUES (%s, %s, %s, 'pending')",
                   (telegram_id, telegram_username, amount))
    db.commit()

    # Notifikasi ke admin untuk konfirmasi
    admin_message = (
        f"Permintaan top-up baru:\n\n"
        f"Telegram ID: {telegram_id}\n"  # ID pelanggan
        f"Username: @{telegram_username}\n"  # Username pelanggan
        f"Jumlah: {amount} kredit\n\n"
        f"Pastikan sudah menerima pembayaran!!\n\n"
    )
    keyboard = [
        [InlineKeyboardButton("Konfirmasi", callback_data=f"confirm_topup,{telegram_id},{amount}")],
        [InlineKeyboardButton("Tolak", callback_data=f"reject_topup,{telegram_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, reply_markup=reply_markup)
    await query.edit_message_text(f"Permintaan top-up sebesar {amount} kredit sedang menunggu konfirmasi admin.\nPastikan sudah membayar sejumlah {amount} secara cash maupun transfer.\nHubungi @arnetadotid untuk konfirmasi pembayaran atau mengirim bukti transfer")
    
    cursor.close()
    db.close()

# Fungsi untuk menangani konfirmasi top-up oleh admin
async def handle_admin_topup_confirmation(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    logger.info(f"Callback data received: {data}")

    try:
        # Memisahkan data callback
        parts = data.split(",")

        action = parts[0]
        telegram_id = int(parts[1])

        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()

        if action == "confirm_topup":
            amount = int(parts[2])
            logger.info(f"Admin action: {action}, Telegram ID: {telegram_id}, Amount: {amount}")

            # Tindakan jika admin mengonfirmasi top-up
            cursor.execute("""
                SELECT tr.username, u.balance
                FROM topup_requests tr
                JOIN users u ON tr.user_id = u.telegram_id
                WHERE tr.user_id = %s AND tr.amount = %s AND tr.status = 'pending'
            """, (telegram_id, amount))
            result = cursor.fetchone()
            if result:
                username, current_balance = result
                new_balance = current_balance + amount
                
                cursor.execute("""
                    UPDATE users
                    SET balance = %s
                    WHERE telegram_id = %s
                """, (new_balance, telegram_id))
                cursor.execute("""
                    UPDATE topup_requests
                    SET status = 'confirmed'
                    WHERE user_id = %s AND amount = %s AND status = 'pending'
                """, (telegram_id, amount))
                db.commit()

                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=f"Top-up sebesar {amount} kredit telah dikonfirmasi.\nSaldo Anda sekarang adalah {new_balance} kredit."
                )
                await query.edit_message_text(f"Top-up untuk pengguna {telegram_id} (@{username}) sebesar {amount} telah anda konfirmasi.\nSaldo baru: {new_balance} kredit.")
            else:
                await query.edit_message_text("Data top-up tidak ditemukan atau sudah diproses.")

        elif action == "reject_topup":
            logger.info(f"Admin action: {action}, Telegram ID: {telegram_id}")

            # Tindakan jika admin menolak top-up
            cursor.execute("""
                SELECT tr.username, tr.amount
                FROM topup_requests tr
                WHERE tr.user_id = %s AND tr.status = 'pending'
            """, (telegram_id,))
            result = cursor.fetchone()
            if result:
                username, amount = result
                cursor.execute("""
                    UPDATE topup_requests
                    SET status = 'rejected'
                    WHERE user_id = %s AND status = 'pending'
                """, (telegram_id,))
                db.commit()

                cursor.execute("""
                    SELECT balance
                    FROM users
                    WHERE telegram_id = %s
                """, (telegram_id,))
                balance_result = cursor.fetchone()
                current_balance = balance_result[0] if balance_result else 0

                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=f"Top-up Anda sebesar {amount} kredit telah ditolak oleh admin.\nKonfirmasikan pembayaran pada @arnetadotid sebelum melakukan top-up\nSaldo Anda masih tetap : {current_balance} kredit."
                )
                await query.edit_message_text(f"Top-up untuk pengguna {telegram_id} (@{username}) sebesar {amount} telah anda tolak.\nSaldo saat ini tetap : {current_balance} kredit.")
            else:
                await query.edit_message_text("Data top-up tidak ditemukan atau sudah diproses.")

        else:
            logger.warning(f"Unknown action: {action}")

        await query.answer()
        cursor.close()
        db.close()

    except ValueError as e:
        logger.error(f"Error processing callback data: {e}")
        await query.answer("Terjadi kesalahan dalam memproses data konfirmasi.")
