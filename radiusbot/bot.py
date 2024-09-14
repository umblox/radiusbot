from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.start_handler import start
from handlers.saldo_handler import saldo
from handlers.beli_handler import beli, beli_callback, beli_confirm_callback, beli_cancel_callback
from handlers.topup_handler import topup, handle_topup_callback, handle_admin_topup_confirmation
from handlers.profile_handler import profile, change_username_prompt, handle_new_username, confirm_username_change, cancel_username_change  # Import handler for /profile command
from handlers.status_handler import status  # Import handler for /status command
from config import BOT_TOKEN

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Menambahkan handler untuk perintah
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("saldo", saldo))
    application.add_handler(CommandHandler("beli", beli))
    application.add_handler(CommandHandler("topup", topup))
    application.add_handler(CommandHandler("profile", profile))  # Added handler for /profile command
    application.add_handler(CommandHandler("status", status))  # Added handler for /status command

    # Menambahkan handler untuk CallbackQuery
    application.add_handler(CallbackQueryHandler(beli_confirm_callback, pattern='^confirm_beli_'))
    application.add_handler(CallbackQueryHandler(beli_callback, pattern='^beli_'))
    application.add_handler(CallbackQueryHandler(beli_cancel_callback, pattern='^cancel_beli'))
    application.add_handler(CallbackQueryHandler(handle_topup_callback, pattern='^topup'))

    # Menambahkan handler untuk konfirmasi topup (termasuk penolakan)
    application.add_handler(CallbackQueryHandler(handle_admin_topup_confirmation, pattern='^confirm_topup|reject_topup'))  # DITAMBAHKAN UNTUK MENANGANI PENOLAKAN

    # Menambahkan handler untuk CallbackQuery (ubah username)
    application.add_handler(CallbackQueryHandler(change_username_prompt, pattern='^change_username$'))
    application.add_handler(CallbackQueryHandler(confirm_username_change, pattern='^confirm_username_change$'))
    application.add_handler(CallbackQueryHandler(cancel_username_change, pattern='^cancel_username_change$'))

    # Pastikan handler yang tepat digunakan sebagai callback
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^[0-9]+$'), handle_admin_topup_confirmation))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^[a-zA-Z0-9_]+$'), handle_new_username))

    # Mulai polling
    application.run_polling()

if __name__ == '__main__':
    main()
