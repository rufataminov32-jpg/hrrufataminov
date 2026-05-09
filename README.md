# 📸 Hisobot Bot

Telegram guruhida xodimlarning kunlik screenshot-hisobotlarini nazorat qiluvchi bot.

## ✨ Imkoniyatlar

- Har kuni soat **10:00 gacha** yuborilgan rasmlarni hisobot sifatida qabul qiladi
- Faqat **whitelist** (ro'yxatdagi) xodimlarni kuzatadi
- Soat **10:00 da** avtomatik ravishda kim topshirdi/topshirmadi ro'yxatini e'lon qiladi
- **Shanba-yakshanba** dam olish kunlari bot hisobot so'ramaydi
- **UTC+5 (Toshkent)** vaqt mintaqasi

---

## 🚀 Deploy qilish

### 1. GitHub'ga yuklash

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/USERNAME/report-bot.git
git push -u origin main
```

### 2. Railway'da deploy

1. [railway.app](https://railway.app) saytiga kiring
2. **New Project → Deploy from GitHub repo** tanlang
3. Repozitoriyangizni tanlang
4. **Variables** bo'limiga o'ting va quyidagilarni kiriting:

| O'zgaruvchi | Tavsif | Misol |
|-------------|--------|-------|
| `BOT_TOKEN` | BotFather tokeni | `1234567890:ABC...` |
| `GROUP_ID` | Guruh chat_id (manfiy) | `-1001234567890` |
| `ADMIN_IDS` | Admin ID lari (vergul bilan) | `123456789,987654321` |

5. Deploy avtomatik boshlanadi ✅

---

## 🤖 Bot buyruqlari

### Barcha foydalanuvchilar uchun
| Buyruq | Tavsif |
|--------|--------|
| `/start` | Botni ishga tushirish |
| `/status` | Bugungi hisobot holati |

### Faqat adminlar uchun
| Buyruq | Tavsif |
|--------|--------|
| `/addemployee <id> Ism Familiya @username` | Xodim qo'shish |
| `/removeemployee <id>` | Xodimni o'chirish |
| `/listemployees` | Barcha xodimlar ro'yxati |

---

## 📋 Xodim qo'shish misoli

Xodimning Telegram ID sini bilish uchun [@userinfobot](https://t.me/userinfobot) botiga yozing.

```
/addemployee 123456789 Aliyev Bobur @bobur_aliyev
/addemployee 987654321 Karimova Nilufar
```

---

## 📁 Fayl tuzilmasi

```
report-bot/
├── bot.py           # Asosiy bot kodi
├── database.py      # SQLite bilan ishlash
├── requirements.txt # Python kutubxonalari
├── Procfile         # Railway uchun ishga tushirish buyrug'i
├── railway.toml     # Railway konfiguratsiyasi
├── .env.example     # O'zgaruvchilar namunasi
└── .gitignore
```

---

## ⚙️ Mahalliy ishga tushirish (test uchun)

```bash
pip install -r requirements.txt
cp .env.example .env
# .env faylini to'ldiring
python bot.py
```

---

## 🔍 Guruh ID sini topish

1. Botni guruhga qo'shing
2. Guruhda `/start` yozing
3. Brauzerda `https://api.telegram.org/bot<TOKEN>/getUpdates` ni oching
4. `"chat":{"id":` qiymatini toping (manfiy raqam)
