#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TELEGRAM GIFT BOT - REAL STARS BALANSI BILAN
Telegram stars evaziga gift sotib olish va yuborish
HTTP API qo'shilgan versiya: username va gift_id orqali POST so'rov bilan gift yuborish

MUHIM — BITTA AKKAUNT REJIMI:
  Bu skript FAQAT BITTA Telegram akkaunt (TG_SESSION) bilan ishlaydi.
  Gift shu akkauntning REAL Stars balansidan sotib olinadi va yuboriladi.
  Agar bir nechta akkaunt kerak bo'lsa — har biri uchun bu skriptni
  ALOHIDA (turli PORT / GIFTBOT_API_URL bilan) deploy qiling, bitta
  jarayon ichida bir nechta akkauntni boshqarish qasddan QILINMAGAN —
  bu xavfsizroq va balansni chalkashtirib yubormaydi.

Muallif: @not_type Manba: @Professional_PHP
Version: 7.2 (Real Gift Sending — single account)
"""

import asyncio
import os
import sys
import json
import time
import logging
import random
from datetime import datetime
from typing import Dict, Optional, Tuple

# Kerakli kutubxonalarni o'rnatish. Manba: @Professional_PHP
try:
    from telethon import TelegramClient, events, functions, types
    from telethon.sessions import StringSession
    from telethon.tl.types import InputPeerUser, InputPeerSelf, StarsAmount, InputInvoiceStarGift
    from telethon.tl.functions.payments import GetPaymentFormRequest, SendStarsFormRequest
    from telethon.errors import FloodWaitError
    from colorama import init, Fore, Style
    from aiohttp import web
except ImportError as e:
    print(f"❌ Kutubxona xatosi: {e}")
    print("\n📦 O'rnatish uchun:")
    print("pip install telethon colorama aiohttp")
    sys.exit(1)

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gift_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Colorama ni ishga tushirish
init(autoreset=True)

# TELEGRAM GIFT MA'LUMOTLARI (haqiqiy Telegram gift IDlari, foydalanuvchi bergan ro'yxat asosida)
TELEGRAM_GIFTS = {
    '5170145012310081615': {'name': 'Yurakcha',       'price': 15,  'emoji': '❤️', 'kind': 'unlimited'},
    '5170233102089322756': {'name': 'Ayiqcha',        'price': 15,  'emoji': '🧸', 'kind': 'unlimited'},
    '5170250947678437525': {'name': "Sovg'a",         'price': 25,  'emoji': '🎁', 'kind': 'unlimited'},
    '5168103777563050263': {'name': 'Atirgul',        'price': 25,  'emoji': '🌹', 'kind': 'unlimited'},
    '5170144170496491616': {'name': 'Tort',           'price': 50,  'emoji': '🎂', 'kind': 'unlimited'},
    '5170314324215857265': {'name': 'Gulchambar',     'price': 50,  'emoji': '💐', 'kind': 'unlimited'},
    '5170564780938756245': {'name': 'Raketa',         'price': 50,  'emoji': '🚀', 'kind': 'unlimited'},
    '6028601630662853006': {'name': 'Shampan',        'price': 50,  'emoji': '🍾', 'kind': 'unlimited'},
    '5168043875654172773': {'name': 'Yulduz',         'price': 100, 'emoji': '⭐', 'kind': 'unlimited'},
    '5170690322832818290': {'name': 'Uzuk',           'price': 100, 'emoji': '💍', 'kind': 'unlimited'},
    '5170521118301225164': {'name': 'Yulduz Premium', 'price': 100, 'emoji': '⭐', 'kind': 'unlimited'},

    '5956217000635139069': {'name': 'Noyob gift #1', 'price': None, 'emoji': '⭐', 'kind': 'unique'},
    '5922558454332916696': {'name': 'Noyob gift #2', 'price': None, 'emoji': '⭐', 'kind': 'unique'},
    '5800655655995968830': {'name': 'Noyob gift #3', 'price': None, 'emoji': '⭐', 'kind': 'unique'},
    '5801108895304779062': {'name': 'Noyob gift #4', 'price': None, 'emoji': '⭐', 'kind': 'unique'},
    '5866352046986232958': {'name': 'Noyob gift #5', 'price': None, 'emoji': '⭐', 'kind': 'unique'},
    '5893356958802511476': {'name': 'Noyob gift #6', 'price': None, 'emoji': '⭐', 'kind': 'unique'},
    '5935895822435615975': {'name': 'Noyob gift #7', 'price': None, 'emoji': '🎁', 'kind': 'unique'},
    '5969796561943660080': {'name': 'Noyob gift #8', 'price': None, 'emoji': '🎁', 'kind': 'unique'},
}

class TelegramGiftBot:
    """Telegram Gift Bot - Real Stars bilan ishlaydi (BITTA akkaunt)"""

    def __init__(self):
        self.api_id = None
        self.api_hash = None
        self.client = None
        self.session_file = 'telegram_gift_bot_session'
        self.admins = []
        self.start_time = time.time()
        self.real_stars_balance = 0
        self.me = None
        self.api_secret = ''
        self.session_string = ''
        self.headless = False
        self.web_runner = None  # aiohttp AppRunner ni saqlash uchun (to'xtatish uchun kerak)

        self.print_banner()
        self.load_config()

    def print_banner(self):
        """Chiroyli banner chiqarish"""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════╗
{Fore.CYAN}║   TELEGRAM GIFT BOT - REAL STARS v7.2 (API)    ║
{Fore.CYAN}║   BITTA AKKAUNT REJIMI — REAL GIFT YUBORISH    ║
{Fore.CYAN}╠══════════════════════════════════════════════════╣
{Fore.YELLOW}║  HTTP API: username + gift_id -> POST /buy      ║
{Fore.CYAN}╚══════════════════════════════════════════════════╝
{Fore.GREEN}
⚡ Telegram Gift Bot ishga tushmoqda...
⚡ REAL STARS BALANSI bilan ishlaydi!
        """
        print(banner)
        logger.info("Bot ishga tushmoqda...")

    def load_config(self):
        """Konfiguratsiyani yuklash.

        1. config.json mavjud bo'lsa — undan o'qiydi (api_id, api_hash, session_string)
        2. Yo'q bo'lsa — foydalanuvchidan so'raydi va config.json ga saqlaydi
        """
        self.api_secret = os.environ.get('API_SECRET', '').strip()
        config_file = 'config.json'

        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.api_id         = config.get('api_id')
                self.api_hash       = config.get('api_hash')
                self.session_string = config.get('session_string', '')
                self.admins         = config.get('admins', [])
                self.headless       = bool(self.session_string)
                logger.info("Konfiguratsiya config.json dan yuklandi")
                return

            # config.json yo'q — birinchi marta ishga tushmoqda
            print(f"{Fore.YELLOW}📝 Birinchi marta sozlash:")
            print(f"{Fore.YELLOW}👉 https://my.telegram.org dan API ID va Hash oling")
            self.api_id   = int(input(f"{Fore.YELLOW}API ID: ").strip())
            self.api_hash = input(f"{Fore.YELLOW}API Hash: ").strip()

            self.session_string = ''
            self.headless = False

            config = {
                'api_id': self.api_id,
                'api_hash': self.api_hash,
                'session_string': '',
                'admins': self.admins
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)

            print(f"{Fore.GREEN}✅ API ma'lumotlari saqlandi!")
            logger.info("Yangi konfiguratsiya saqlandi")

        except Exception as e:
            logger.error(f"Konfiguratsiya yuklashda xatolik: {e}")
            print(f"{Fore.RED}❌ Xatolik: {e}")
            sys.exit(1)

    def save_session_to_config(self, session_string: str):
        """Session stringni config.json ga saqlaydi"""
        config_file = 'config.json'
        try:
            config = {}
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            config['session_string'] = session_string
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            logger.info("Session config.json ga saqlandi")
        except Exception as e:
            logger.error(f"Session saqlashda xatolik: {e}")

    async def get_real_stars_balance(self) -> int:
        """Telegram API orqali REAL STARS balansini olish"""
        try:
            result = await self.client(functions.payments.GetStarsStatusRequest(
                peer=await self.client.get_input_entity('me')
            ))

            if result and hasattr(result, 'balance'):
                if hasattr(result.balance, 'amount'):
                    self.real_stars_balance = result.balance.amount
                else:
                    self.real_stars_balance = int(result.balance)

                logger.info(f"Real stars balansi olindi: {self.real_stars_balance}⭐")
                return self.real_stars_balance
            else:
                logger.warning("Balans ma'lumoti olinmadi")
                return 0

        except FloodWaitError as e:
            wait_time = e.seconds
            logger.warning(f"Flood wait: {wait_time} soniya")
            print(f"{Fore.YELLOW}⚠️ Ko'p so'rov yuborildi. {wait_time} soniya kuting...")
            await asyncio.sleep(wait_time)
            return await self.get_real_stars_balance()

        except Exception as e:
            logger.error(f"Balans olishda xatolik: {e}")
            print(f"{Fore.RED}❌ Balans olishda xatolik: {e}")
            return 0

    async def get_stars_balance_direct(self) -> int:
        """Stars balansini olishning alternativ usuli"""
        try:
            result = await self.client(functions.payments.GetStarsBalanceRequest())
            if result:
                if hasattr(result, 'balance'):
                    if hasattr(result.balance, 'amount'):
                        return result.balance.amount
                    else:
                        return int(result.balance)
            return 0
        except Exception as e:
            logger.error(f"Direct balans olishda xatolik: {e}")
            return 0

    @staticmethod
    def _translate_gift_error(raw: str) -> str:
        """Telegram RPC xato matnini odam o'qiy oladigan o'zbek tilidagi
        xabarga aylantiradi. Tanilmagan xatolar uchun xom matnni qaytaradi."""
        raw_up = raw.upper()
        mapping = {
            'BALANCE_TOO_LOW':          "Stars balansi yetarli emas",
            'STARGIFT_USAGE_LIMITED':   "Bu giftning soni tugagan (limited edition)",
            'STARGIFT_INVALID':         "Bu gift mavjud emas yoki o'chirilgan",
            'STARGIFT_USABLE_INVALID':  "Bu gift hozir sotib olinmaydi",
            'PEER_ID_INVALID':          "Foydalanuvchi topilmadi yoki sizga yopiq",
            'USER_IS_BLOCKED':          "Foydalanuvchi sizni bloklagan",
            'USER_ID_INVALID':          "Foydalanuvchi ID noto'g'ri",
            'FORM_EXPIRED':             "To'lov shakli muddati tugadi, qayta urinib ko'ring",
            'PREMIUM_ACCOUNT_REQUIRED': "Qabul qiluvchi giftlarni cheklagan",
            'INPUT_USER_DEACTIVATED':   "Foydalanuvchi akkaunti o'chirilgan",
            'FLOOD_WAIT':               "Juda ko'p so'rov, biroz kuting",
        }
        for key, val in mapping.items():
            if key in raw_up:
                return val
        return f"Xatolik: {raw}"

    async def send_real_gift(self, gift_id: str, user_id: int, anonymous: bool = False) -> Tuple[bool, str]:
        """REAL GIFT yuborish — Telegram Stars to'lov tizimi orqali.

        Telegramning rasmiy "gift sotib olish" protokoli quyidagicha ishlaydi
        (xuddi Premium'ni Stars evaziga sotib olishdagi kabi):

          1) InputInvoiceStarGift quramiz — kimga, qaysi gift, anonim yoki yo'q
          2) payments.GetPaymentForm — to'lov shaklini (form_id) olamiz
          3) payments.SendStarsForm  — shu form_id bilan, AKKAUNTNING
             REAL Stars balansidan yechib, giftni haqiqatan yuboradi

        Bu BITTA akkauntning (joriy self.client sessiyasi) o'z balansidan
        ishlaydi — boshqa hech qanday akkaunt aralashmaydi.
        """
        try:
            if gift_id not in TELEGRAM_GIFTS:
                return False, "Gift topilmadi"

            gift = TELEGRAM_GIFTS[gift_id]

            if gift.get('kind') == 'unique' or gift.get('price') is None:
                return False, "Bu noyob (unique) gift — sotib olib bo'lmaydi, faqat transfer qilinadi"

            balance = await self.get_real_stars_balance()
            if balance == 0:
                balance = await self.get_stars_balance_direct()

            if balance < gift['price']:
                return False, f"Balans yetarli emas! Kerak: {gift['price']}⭐, Sizda: {balance}⭐"

            # Qabul qiluvchining InputUser obyektini olamiz (entity allaqachon
            # buy_and_send_gift() ichida resolve qilingan bo'lishi kerak)
            peer = await self.client.get_input_entity(user_id)

            invoice = InputInvoiceStarGift(
                user_id=peer,
                gift_id=int(gift_id),
                hide_name=anonymous,
            )

            form = await self.client(GetPaymentFormRequest(invoice=invoice))
            form_id = getattr(form, 'form_id', None)
            if not form_id:
                return False, "To'lov shakli olinmadi, qayta urinib ko'ring"

            await self.client(SendStarsFormRequest(
                form_id=form_id,
                invoice=invoice,
            ))

            logger.info(f"Gift muvaffaqiyatli yuborildi: {gift['name']} -> {user_id}")
            return True, f"✅ Gift muvaffaqiyatli yuborildi! Balansdan {gift['price']}⭐ yechildi"

        except FloodWaitError as e:
            wait_time = e.seconds
            logger.warning(f"Flood wait: {wait_time} soniya")
            return False, f"Ko'p so'rov yuborildi. {wait_time} soniya kuting"

        except Exception as e:
            err_name = type(e).__name__
            msg = str(e)
            logger.error(f"Gift yuborishda xatolik: {err_name}: {msg}")
            friendly = self._translate_gift_error(f"{err_name} {msg}")
            return False, friendly

    async def get_available_gifts(self) -> Dict:
        """Mavjud giftlarni olish"""
        return TELEGRAM_GIFTS

    # ------------------------------------------------------------------
    # ASOSIY QAYTA ISHLATILADIGAN MANTIQ: username + gift_id -> natija
    # Bu metod ham .buy komandasi, ham HTTP API tomonidan ishlatiladi.
    # ------------------------------------------------------------------
    async def buy_and_send_gift(self, gift_id: str, username: str, anonymous: bool = False) -> dict:
        """
        gift_id va username asosida gift sotib olib yuboradi.
        Telegram xabar eventiga bog'liq emas — shuning uchun HTTP API dan
        ham, .buy komandasidan ham bir xil ishlatish mumkin.

        Qaytaradi: {success: bool, message: str, gift, user_id, new_balance}
        """
        username = username.lstrip('@').strip()

        if gift_id not in TELEGRAM_GIFTS:
            return {"success": False, "message": "Bunday gift topilmadi", "gift_id": gift_id}

        gift = TELEGRAM_GIFTS[gift_id]

        if gift.get('kind') == 'unique' or gift.get('price') is None:
            return {
                "success": False,
                "message": "Bu noyob (unique) gift — sotib olib bo'lmaydi, faqat transfer qilinadi",
                "gift_id": gift_id,
            }

        try:
            user = await self.client.get_entity(username)
        except Exception as e:
            logger.error(f"Foydalanuvchi topilmadi: {username} - {e}")
            return {"success": False, "message": f"Foydalanuvchi topilmadi: @{username}"}

        balance = await self.get_real_stars_balance()
        if balance == 0:
            balance = await self.get_stars_balance_direct()

        if gift['price'] is not None and balance < gift['price']:
            return {
                "success": False,
                "message": f"Balans yetarli emas! Kerak: {gift['price']}⭐, Sizda: {balance}⭐",
                "balance": balance,
                "required": gift['price'],
            }

        success, message = await self.send_real_gift(gift_id, user.id, anonymous=anonymous)

        new_balance = balance
        if success:
            new_balance = await self.get_real_stars_balance()
            if new_balance == 0:
                new_balance = await self.get_stars_balance_direct()

            try:
                await self.client.send_message(
                    user.id,
                    f"🎁 **Sizga REAL GIFT yuborildi!**\n\n"
                    f"{gift['emoji']} **Gift:** {gift['name']}\n\n"
                    f"💝 Bu haqiqiy Telegram gift! Profilingizda ko'rinadi!"
                )
            except Exception as e:
                logger.warning(f"Qabul qiluvchiga xabar yuborilmadi: {e}")

        return {
            "success": success,
            "message": message,
            "gift_id": gift_id,
            "gift_name": gift['name'],
            "username": username,
            "user_id": user.id,
            "balance_before": balance,
            "balance_after": new_balance,
        }

    # ------------------------------------------------------------------
    # HTTP API (aiohttp)
    # POST /buy   { "gift_id": "...", "username": "...", "anonymous": false }
    # Header:     X-API-Secret: <API_SECRET ENV qiymati>
    # ------------------------------------------------------------------
    def _check_auth(self, request: web.Request) -> bool:
        """API_SECRET ENV o'zgaruvchisi bo'lsa, so'rovni tekshiradi."""
        if not self.api_secret:
            # API_SECRET o'rnatilmagan bo'lsa, ochiq qoladi.
            # Productionda API_SECRET ni doim o'rnatish tavsiya etiladi.
            return True
        provided = request.headers.get('X-API-Secret', '')
        return provided == self.api_secret

    async def api_buy_handler(self, request: web.Request) -> web.Response:
        """POST /buy - gift_id va username orqali real gift yuboradi"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "Unauthorized"}, status=401)

        try:
            data = await request.json()
        except Exception:
            return web.json_response({"success": False, "message": "Body JSON bo'lishi kerak"}, status=400)

        gift_id = str(data.get('gift_id', '')).strip()
        username = str(data.get('username', '')).strip()
        anonymous = bool(data.get('anonymous', False))

        if not gift_id or not username:
            return web.json_response(
                {"success": False, "message": "gift_id va username majburiy"},
                status=400,
            )

        try:
            result = await self.buy_and_send_gift(gift_id, username, anonymous=anonymous)
        except Exception as e:
            logger.error(f"API /buy xatolik: {e}")
            return web.json_response({"success": False, "message": f"Xatolik: {e}"}, status=500)

        status = 200 if result.get("success") else 400
        return web.json_response(result, status=status)

    async def api_gifts_handler(self, request: web.Request) -> web.Response:
        """GET /gifts - mavjud giftlar ro'yxatini JSON qilib qaytaradi"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "Unauthorized"}, status=401)
        return web.json_response({"success": True, "gifts": TELEGRAM_GIFTS})

    async def api_balance_handler(self, request: web.Request) -> web.Response:
        """GET /balance - real stars balansini JSON qilib qaytaradi"""
        if not self._check_auth(request):
            return web.json_response({"success": False, "message": "Unauthorized"}, status=401)
        balance = await self.get_real_stars_balance()
        if balance == 0:
            balance = await self.get_stars_balance_direct()
        return web.json_response({"success": True, "balance": balance})

    async def api_health_handler(self, request: web.Request) -> web.Response:
        """GET /health - server ishlayotganini tekshirish uchun (auth talab qilmaydi)"""
        return web.json_response({"status": "ok", "uptime_seconds": int(time.time() - self.start_time)})

    async def start_api_server(self):
        """aiohttp HTTP serverini ishga tushiradi (Telegram clientga parallel)"""
        port = int(os.environ.get('PORT', os.environ.get('API_PORT', 8080)))

        app = web.Application()
        app.router.add_post('/buy', self.api_buy_handler)
        app.router.add_get('/gifts', self.api_gifts_handler)
        app.router.add_get('/balance', self.api_balance_handler)
        app.router.add_get('/health', self.api_health_handler)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        self.web_runner = runner

        logger.info(f"HTTP API ishga tushdi: 0.0.0.0:{port}")
        print(f"{Fore.GREEN}🌐 HTTP API ishga tushdi: http://0.0.0.0:{port}")
        print(f"{Fore.CYAN}   POST /buy      body: {{\"gift_id\": \"...\", \"username\": \"...\"}}")
        print(f"{Fore.CYAN}   GET  /gifts")
        print(f"{Fore.CYAN}   GET  /balance")
        print(f"{Fore.CYAN}   GET  /health")
        if self.api_secret:
            print(f"{Fore.CYAN}   Header kerak: X-API-Secret: ****** (ENV: API_SECRET)")
        else:
            print(f"{Fore.YELLOW}   ⚠️ API_SECRET o'rnatilmagan — API ochiq! Productionda o'rnatish tavsiya etiladi.")

    async def start(self):
        """Botni ishga tushirish (BITTA akkaunt bilan)"""
        try:
            if self.session_string:
                # config.json da session bor — to'g'ridan ulanamiz
                print(f"{Fore.GREEN}🔄 Saqlangan session orqali ulanmoqda...")
                logger.info("StringSession orqali ulanish...")
                self.client = TelegramClient(StringSession(self.session_string), self.api_id, self.api_hash)
                await self.client.start()
            else:
                # Birinchi marta — telefon raqam so'rab login qilamiz
                phone = input(f"{Fore.YELLOW}📱 Telefon raqam (+998901234567): ").strip()
                print(f"{Fore.GREEN}🔄 Telegram ga ulanmoqda...")
                logger.info("Telegramga ulanish...")
                self.client = TelegramClient(StringSession(), self.api_id, self.api_hash)
                await self.client.start(phone=phone)
                # Session ni config.json ga saqlaymiz (keyingi safar so'ramaslik uchun)
                saved_session = self.client.session.save()
                self.save_session_to_config(saved_session)
                self.session_string = saved_session
                print(f"{Fore.GREEN}✅ Session saqlandi! Keyingi safar avtomatik ulanadi.")

            self.me = await self.client.get_me()
            self.admins.append(self.me.id)

            self.real_stars_balance = await self.get_real_stars_balance()
            if self.real_stars_balance == 0:
                self.real_stars_balance = await self.get_stars_balance_direct()

            print(f"{Fore.GREEN}✅ Xush kelibsiz, {self.me.first_name}!")
            print(f"{Fore.GREEN}✅ Sizning ID: {self.me.id}")
            print(f"{Fore.GREEN}💰 REAL STARS BALANSI: {self.real_stars_balance}⭐")
            logger.info(f"Bot ishga tushdi: {self.me.first_name} (ID: {self.me.id})")

            @self.client.on(events.NewMessage)
            async def handler(event):
                await self.handle_message(event)

            # HTTP API serverini parallel ishga tushiramiz
            await self.start_api_server()

            print(f"{Fore.GREEN}\n✅ Bot muvaffaqiyatli ishga tushdi!")
            print(f"{Fore.CYAN}📝 KOMANDALAR:")
            print(f"{Fore.CYAN}  .start - Botni tekshirish")
            print(f"{Fore.CYAN}  .gifts - Giftlar ro'yxati")
            print(f"{Fore.CYAN}  .balance - Stars balansini tekshirish")
            print(f"{Fore.CYAN}  .buy [ID] @user - Gift sotib olish va yuborish")
            print(f"{Fore.CYAN}  .stats - Statistika")
            print(f"{Fore.CYAN}  .help - Yordam")
            print(f"{Fore.CYAN}  .restart - Botni qayta ishga tushirish")
            print(f"{Fore.CYAN}  .stop - Botni to'xtatish")
            print(f"{Fore.CYAN}\n💰 REAL STARS BALANSI: {self.real_stars_balance}⭐")
            print(f"{Fore.CYAN}📌 Kutilyapti...\n")

            await self.client.run_until_disconnected()

        except Exception as e:
            logger.error(f"Bot ishga tushishda xatolik: {e}")
            print(f"{Fore.RED}❌ Xatolik: {e}")
            sys.exit(1)

    async def handle_message(self, event):
        """Xabarlarni qabul qilish"""
        try:
            message = event.message.text
            if not message or not message.startswith('.'):
                return

            parts = message.split()
            cmd = parts[0].lower()

            logger.info(f"Komanda: {cmd} from {event.sender_id}")

            if cmd == '.start' or cmd == '.go':
                await self.cmd_start(event)
            elif cmd == '.gifts' or cmd == '.giftlist':
                await self.cmd_gifts(event)
            elif cmd == '.balance' or cmd == '.balans' or cmd == '.stars':
                await self.cmd_balance(event)
            elif cmd == '.buy' or cmd == '.gift' or cmd == '.send':
                await self.cmd_buy_gift(event, parts)
            elif cmd == '.stats':
                await self.cmd_stats(event)
            elif cmd == '.help':
                await self.cmd_help(event)
            elif cmd == '.restart':
                await self.cmd_restart(event)
            elif cmd == '.stop':
                await self.cmd_stop(event)
            else:
                await event.reply(f"❌ Noma'lum komanda: {cmd}\n\n.help yozing komandalar ro'yxati uchun")

        except Exception as e:
            logger.error(f"Xabarni qayta ishlashda xatolik: {e}")
            await event.reply(f"❌ Xatolik: {str(e)}")

    async def cmd_start(self, event):
        balance = await self.get_real_stars_balance()
        if balance == 0:
            balance = await self.get_stars_balance_direct()

        text = f"""
🤖 **TELEGRAM GIFT BOT - REAL STARS**

✅ **Holat:** Aktiv
💰 **REAL Stars balansi:** {balance} ⭐
🎁 **Giftlar:** {len(TELEGRAM_GIFTS)} ta
👤 **Foydalanuvchi:** {self.me.first_name}
🆔 **ID:** `{self.me.id}`

📌 **KOMANDALAR:**
`.gifts` - Giftlar ro'yxati
`.balance` - Stars balansini tekshirish
`.buy [ID] @user` - Gift sotib olish va yuborish
`.stats` - Statistika
`.help` - Yordam
        """
        await event.reply(text)

    async def cmd_gifts(self, event):
        balance = await self.get_real_stars_balance()
        if balance == 0:
            balance = await self.get_stars_balance_direct()

        gifts = await self.get_available_gifts()

        text = "🎁 **TELEGRAM REAL GIFTLAR**\n\n"
        for gift_id, gift in gifts.items():
            price = gift['price'] if gift['price'] is not None else 0
            can_buy = "✅" if (gift['price'] is not None and balance >= price) else "❌"
            text += f"{can_buy} {gift['emoji']} **{gift['name']}**\n"
            text += f"   📦 ID: `{gift_id}`\n"
            text += f"   💰 Narx: {gift['price'] if gift['price'] is not None else 'noyob (faqat transfer)'}⭐\n\n"

        text += f"\n💰 **Sizning REAL Stars balansingiz:** {balance}⭐\n"
        await event.reply(text)

    async def cmd_balance(self, event):
        balance = await self.get_real_stars_balance()
        if balance == 0:
            balance = await self.get_stars_balance_direct()

        max_display = 1000
        progress = min(int((balance / max_display) * 20), 20)
        bar = "█" * progress + "░" * (20 - progress)

        text = f"""
💰 **TELEGRAM REAL STARS BALANSI**

┌────────────────────
│ 💳 **Jami:** {balance} ⭐
│ 📅 **Sana:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
└────────────────────

{bar} {balance}/{max_display}⭐
        """
        await event.reply(text)

    async def cmd_buy_gift(self, event, parts):
        """`.buy [gift_id] @username` komandasi - umumiy buy_and_send_gift dan foydalanadi"""
        if len(parts) < 3:
            await event.reply(
                "❌ **Noto'g'ri format!**\n\n"
                "📝 **To'g'ri format:**\n"
                "`.buy 5801108895304779062 @username`\n\n"
                "📋 Giftlar ro'yxati: `.gifts`"
            )
            return

        gift_id = parts[1]
        username = parts[2]

        msg = await event.reply("🔄 **REAL GIFT sotib olinmoqda...**\n⏳ Iltimos kuting...")

        result = await self.buy_and_send_gift(gift_id, username)

        if result.get("success"):
            await msg.edit(
                f"✅ **REAL GIFT muvaffaqiyatli yuborildi!**\n\n"
                f"🎁 **{result.get('gift_name')}**\n"
                f"👤 Qabul qiluvchi: @{result.get('username')}\n"
                f"💳 Yangi balans: {result.get('balance_after')}⭐"
            )
        else:
            await msg.edit(f"❌ **Xatolik:** {result.get('message')}")

    async def cmd_stats(self, event):
        balance = await self.get_real_stars_balance()
        if balance == 0:
            balance = await self.get_stars_balance_direct()

        uptime = int(time.time() - self.start_time)
        hours = uptime // 3600
        minutes = (uptime % 3600) // 60

        text = f"""
📊 **STATISTIKA**

👤 **Foydalanuvchi:** {self.me.first_name}
🆔 **ID:** `{self.me.id}`
⏱ **Ishlagan vaqt:** {hours}h {minutes}m
💰 **REAL Stars balansi:** {balance}⭐
🎁 **Giftlar soni:** {len(TELEGRAM_GIFTS)}
        """
        await event.reply(text)

    async def cmd_help(self, event):
        text = f"""
📚 **YORDAM - REAL TELEGRAM GIFTS**

**ASOSIY KOMANDALAR:**
`.start` - Botni tekshirish
`.gifts` - Giftlar ro'yxati
`.balance` - REAL Stars balansini tekshirish
`.buy [ID] @user` - Gift sotib olish (stars evaziga)
`.stats` - Statistika
`.restart` - Botni qayta ishga tushirish
`.stop` - Botni to'xtatish
`.help` - Bu yordam

**HTTP API:**
`POST /buy` body: {{"gift_id": "...", "username": "..."}}
`GET /gifts`, `GET /balance`, `GET /health`
        """
        await event.reply(text)

    async def cmd_restart(self, event):
        await event.reply("♻️ **Bot qayta ishga tushirilmoqda...**")
        logger.info("Bot qayta ishga tushirilmoqda...")
        await asyncio.sleep(2)
        os.execl(sys.executable, sys.executable, *sys.argv)

    async def cmd_stop(self, event):
        await event.reply("🛑 **Bot to'xtatilmoqda...**")
        logger.info("Bot to'xtatilmoqda...")
        await asyncio.sleep(1)
        sys.exit(0)

async def main():
    """Asosiy funksiya"""
    bot = TelegramGiftBot()

    try:
        await bot.start()
    except KeyboardInterrupt:
        print(f"{Fore.RED}\n\n❌ Bot to'xtatildi!")
        logger.info("Bot to'xtatildi")
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {e}")
        print(f"{Fore.RED}❌ Xatolik: {e}")
        print(f"{Fore.YELLOW}🔄 5 soniyadan keyin qayta ishga tushiriladi...")
        await asyncio.sleep(5)
        os.execl(sys.executable, sys.executable, *sys.argv)

if __name__ == '__main__':
    asyncio.run(main())
