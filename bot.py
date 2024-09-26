import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.start_handler import start
from handlers.saldo_handler import saldo
from handlers.beli_handler import beli, beli_callback, beli_confirm_callback, beli_cancel_callback
from handlers.topup_handler import topup, handle_topup_callback, handle_admin_topup_confirmation
from handlers.profile_handler import profile, set_username_prompt, set_password_prompt, confirm_username_change, cancel_username_change, show_password, close_message, confirm_password_change, cancel_password_change, handle_user_input
from handlers.status_handler import status
from config import BOT_TOKEN

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Tambahkan CommandHandler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("saldo", saldo))
    application.add_handler(CommandHandler("beli", beli))
    application.add_handler(CommandHandler("topup", topup))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("profile", profile))

    # Tambahkan CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(beli_confirm_callback, pattern='^confirm_beli_'))
    application.add_handler(CallbackQueryHandler(beli_callback, pattern='^beli_'))
    application.add_handler(CallbackQueryHandler(beli_cancel_callback, pattern='^cancel_beli'))
    application.add_handler(CallbackQueryHandler(handle_topup_callback, pattern='^topup'))
    application.add_handler(CallbackQueryHandler(handle_admin_topup_confirmation, pattern='^confirm_topup|reject_topup'))

    # Tambahkan handler untuk perubahan username
    application.add_handler(CallbackQueryHandler(set_username_prompt, pattern='^change_username$'))
    application.add_handler(CallbackQueryHandler(confirm_username_change, pattern='^confirm_username_change$'))
    application.add_handler(CallbackQueryHandler(cancel_username_change, pattern='^cancel_username_change$'))

    # Tambahkan CallbackQueryHandler dan MessageHandler untuk password
    application.add_handler(CallbackQueryHandler(show_password, pattern='^show_password$'))
    application.add_handler(CallbackQueryHandler(close_message, pattern='^close_message$'))

    # Tambahkan handler untuk perubahan password
    application.add_handler(CallbackQueryHandler(set_password_prompt, pattern='^change_password$'))
    application.add_handler(CallbackQueryHandler(confirm_password_change, pattern='^confirm_password_change$'))
    application.add_handler(CallbackQueryHandler(cancel_password_change, pattern='^cancel_password_change$'))

    # Tampilkan tombol konfirmasi penggantian username dan password
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))

    # Mulai polling
    application.run_polling()

if __name__ == '__main__':
    main()
