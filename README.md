# LINE Finance Bot — คู่มือ Deploy

## สิ่งที่ต้องเตรียม (ฟรีทั้งหมด)

| บริการ | ใช้ทำอะไร | ราคา |
|--------|-----------|------|
| LINE Developers | LINE Bot + Webhook | ฟรี |
| Railway.app | Host Python server | ฟรี $5/เดือน (เกินพอ) |
| Groq API | LLaMA 3.1 AI วิเคราะห์ | **ฟรี** (14,400 req/วัน) |
| GitHub | เก็บ source code | ฟรี |

---

## ขั้นตอนที่ 0: ขอ Groq API Key

1. ไปที่ https://console.groq.com/
2. Sign up (ฟรี) → ไปที่ **API Keys** → **Create API Key**
3. จด key ไว้ (ขึ้นต้นด้วย `gsk_...`)

---

## ขั้นตอนที่ 1: สร้าง LINE Bot

1. ไปที่ https://developers.line.biz/console/
2. กด **Create a new provider** → ตั้งชื่อ (เช่น "Finance Bot")
3. กด **Create a new channel** → เลือก **Messaging API**
4. กรอกข้อมูล:
   - Channel name: "Finance Bot"
   - Channel description: "บันทึกรายรับ-รายจ่าย"
   - Category: Finance
5. กด **Create**
6. ไปที่แท็บ **Basic settings** → จด **Channel secret**
7. ไปที่แท็บ **Messaging API** → **Issue** Channel access token → จด token

---

## ขั้นตอนที่ 2: Upload code ขึ้น GitHub

```bash
git init
git add .
git commit -m "init LINE finance bot with Groq"
git remote add origin https://github.com/YOUR_USERNAME/linebot-finance.git
git push -u origin main
```

---

## ขั้นตอนที่ 3: Deploy บน Railway

1. ไปที่ https://railway.app/ → Sign in with GitHub
2. กด **New Project** → **Deploy from GitHub repo**
3. เลือก repo `linebot-finance`
4. รอ build ประมาณ 2-3 นาที
5. ไปที่ **Settings** → **Networking** → กด **Generate Domain**
   - ได้ URL เช่น `https://linebot-finance-production.up.railway.app`

### ตั้งค่า Environment Variables

ใน Railway → แท็บ **Variables** → เพิ่ม:

```
LINE_CHANNEL_SECRET       = [Channel secret จากขั้นตอนที่ 1]
LINE_CHANNEL_ACCESS_TOKEN = [Channel access token จากขั้นตอนที่ 1]
GROQ_API_KEY              = [API key จาก console.groq.com]
DB_PATH                   = /data/finance.db
PORT                      = 8000
```

### เพิ่ม Volume สำหรับ Database

Railway → แท็บ **Volumes** → **Add Volume** → Mount path: `/data`

---

## ขั้นตอนที่ 4: ตั้งค่า Webhook บน LINE

1. กลับไป LINE Developers Console → แท็บ **Messaging API**
2. **Webhook URL** → ใส่: `https://YOUR-DOMAIN.up.railway.app/webhook`
3. กด **Verify** → ต้องขึ้น "Success"
4. เปิด **Use webhook** → ON
5. ปิด **Auto-reply messages** → OFF

---

## ขั้นตอนที่ 5: เพิ่ม Bot เป็นเพื่อน

1. ใน LINE Developers → แท็บ **Messaging API** → สแกน QR Code
2. ทดสอบพิมพ์ "ช่วยเหลือ" → บอทตอบกลับ ✅

---

## วิธีใช้งาน

```
กาแฟ 65           → บันทึกรายจ่าย อาหาร 65 บาท
ข้าวเที่ยง 120    → บันทึกรายจ่าย อาหาร 120 บาท
เงินเดือน 30000   → บันทึกรายรับ เงินเดือน 30,000 บาท
แท็กซี่ 200       → บันทึกรายจ่าย เดินทาง 200 บาท

สรุป              → สรุปรายรับ-รายจ่ายเดือนนี้
รายการ            → รายการทั้งหมดเดือนนี้
วิเคราะห์         → AI วิเคราะห์พฤติกรรมการเงิน

ลบกาแฟ           → ลบรายการที่มีชื่อ "กาแฟ"
ช่วยเหลือ        → แสดงเมนู
```

---

## ค่าใช้จ่ายโดยประมาณ

| รายการ | ค่าใช้จ่าย |
|--------|-----------|
| LINE Messaging API | ฟรี (reply ไม่จำกัด) |
| Railway | ฟรี $5 credit/เดือน |
| **Groq API (LLaMA 3.1)** | **ฟรี 14,400 req/วัน** |
| **รวม** | **ฟรี 100%** |

---

## โครงสร้างไฟล์

```
linebot-finance/
├── app/
│   ├── main.py          # FastAPI webhook + Groq AI
│   └── db.py            # SQLite database
├── requirements.txt
├── Dockerfile
├── railway.toml
└── README.md
```
