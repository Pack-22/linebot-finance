# LINE Finance Bot — คู่มือ Deploy

## สิ่งที่ต้องเตรียม (ฟรีทั้งหมด)

| บริการ | ใช้ทำอะไร | ราคา |
|--------|-----------|------|
| LINE Developers | LINE Bot + Webhook | ฟรี |
| Railway.app | Host Python server | ฟรี $5/เดือน (เกินพอ) |
| Anthropic API | Claude AI วิเคราะห์ | Pay per use (~฿0.01/ข้อความ) |
| GitHub | เก็บ source code | ฟรี |

---

## ขั้นตอนที่ 1: สร้าง LINE Bot

1. ไปที่ https://developers.line.biz/console/
2. กด **Create a new provider** → ตั้งชื่อ (เช่น "Finance Bot")
3. กด **Create a new channel** → เลือก **Messaging API**
4. กรอกข้อมูล:
   - Channel name: "Finance Bot" (หรือชื่ออะไรก็ได้)
   - Channel description: "บันทึกรายรับ-รายจ่าย"
   - Category: Finance
5. กด **Create**
6. ไปที่แท็บ **Basic settings** → จด **Channel secret**
7. ไปที่แท็บ **Messaging API** → ด้านล่างสุด → **Issue** Channel access token → จด token

---

## ขั้นตอนที่ 2: Upload code ขึ้น GitHub

```bash
# สร้าง repo ใหม่บน github.com ก่อน แล้วรัน:
git init
git add .
git commit -m "init LINE finance bot"
git remote add origin https://github.com/YOUR_USERNAME/linebot-finance.git
git push -u origin main
```

---

## ขั้นตอนที่ 3: Deploy บน Railway

1. ไปที่ https://railway.app/ → Sign in with GitHub
2. กด **New Project** → **Deploy from GitHub repo**
3. เลือก repo `linebot-finance`
4. Railway จะ build อัตโนมัติ รอประมาณ 2-3 นาที
5. ไปที่ **Settings** → **Networking** → กด **Generate Domain**
   - จะได้ URL เช่น `https://linebot-finance-production.up.railway.app`

### ตั้งค่า Environment Variables

ใน Railway → แท็บ **Variables** → เพิ่มตัวแปรเหล่านี้:

```
LINE_CHANNEL_SECRET     = [Channel secret จากขั้นตอนที่ 1]
LINE_CHANNEL_ACCESS_TOKEN = [Channel access token จากขั้นตอนที่ 1]
ANTHROPIC_API_KEY       = [API key จาก console.anthropic.com]
DB_PATH                 = /data/finance.db
PORT                    = 8000
```

### เพิ่ม Volume สำหรับ Database

ใน Railway → แท็บ **Volumes** → **Add Volume**
- Mount path: `/data`

---

## ขั้นตอนที่ 4: ตั้งค่า Webhook บน LINE

1. กลับไป LINE Developers Console
2. แท็บ **Messaging API**
3. **Webhook URL** → ใส่: `https://YOUR-DOMAIN.up.railway.app/webhook`
4. กด **Verify** → ต้องขึ้น "Success"
5. เปิด **Use webhook** → ON
6. ปิด **Auto-reply messages** → OFF
7. ปิด **Greeting messages** → OFF (optional)

---

## ขั้นตอนที่ 5: เพิ่ม Bot เป็นเพื่อน

1. ใน LINE Developers → แท็บ **Messaging API**
2. ด้านบนจะมี QR Code → สแกนเพิ่มเพื่อน
3. ทดสอบพิมพ์ "ช่วยเหลือ" → บอทตอบกลับ ✅

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

- LINE Messaging API: **ฟรี** (200 push msg/วัน, reply ไม่จำกัด)
- Railway: **ฟรี** $5 credit/เดือน (เกินพอสำหรับใช้คนเดียว)
- Claude API (Haiku): **~฿0.005-0.02 ต่อข้อความ** (ใช้ 100 ข้อความ/วัน ≈ ฿50/เดือน)

---

## โครงสร้างไฟล์

```
linebot-finance/
├── app/
│   ├── main.py          # FastAPI webhook handler
│   └── db.py            # SQLite database
├── requirements.txt
├── Dockerfile
├── railway.toml
└── README.md
```
