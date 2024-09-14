# config.py

import logging

# Konfigurasi logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfigurasi database
DB_CONFIG = {
    'user': 'radius',
    'password': 'radius',
    'host': '127.0.0.1',
    'database': 'radius'
}

# Token Bot
BOT_TOKEN = '7530717438:AAFDpkb15BzqvjJx8-jNDT-Kg6JS0uhgbuo'

# Admin ID
ADMIN_ID = 2123457759

# Prefix voucher berdasarkan nama plan
VOUCHER_PREFIX = {
    '1Hari': '3k',
    '5k': '5k',
    '7Hari': '15k',
    '30Hari': '60k'
}

