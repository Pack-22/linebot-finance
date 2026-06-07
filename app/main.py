import os
import json
import hmac
import hashlib
import base64
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
from db import Database

app = FastAPI()
db = Database()

LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

LINE_API = "https://api.line.me/v2/bot/message/reply"
GROQ_API = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"  # เร็ว ฟรี เหมาะกับ chat

HELP_TEXT = """💰 วิธีใช้งาน:

📝 บันทึกรายการ:
• พิมพ์ธรรมชาติ เช่น "กาแฟ 65" หรือ "เงินเดือน 30000"

📊 ดูรายงาน:
• "สรุป" — สรุปเดือนนี้
• "สรุปเดือนที่แล้ว" — เดือนที่แล้ว
• "รายการ" — รายการทั้งหมดเดือนนี้

🤖 ถาม AI:
• "วิเคราะห์" — AI วิเคราะห์การเงิน
• "ฉันใช้เงินเกินไปไหม?"

🗑️ ลบรายการ:
• "ลบ [ชื่อรายการ]" เช่น "ลบกาแฟ"

❓ "ช่วยเหลือ" — แสดงเมนูนี้"""


def verify_signature(body: bytes, signature: str) -> bool:
    hash_val = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"), body, hashlib.sha256
    ).digest()
    expected = base64.b64encode(hash_val).decode("utf-8")
    return hmac.compare_digest(expected, signature)


async def reply(reply_token: str, messages: list[dict]):
    async with httpx.AsyncClient() as client:
        await client.post(
            LINE_API,
            headers={"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"},
            json={"replyToken": reply_token, "messages": messages},
        )


async def call_groq(system: str, user: str, max_tokens: int = 500) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(
            GROQ_API,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        data = res.json()
        return data["choices"][0]["message"]["content"].strip()


async def parse_entry(text: str) -> dict | None:
    system = """วิเคราะห์ข้อความรายรับ-รายจ่าย ตอบเป็น JSON เท่านั้น ไม่มี markdown ไม่มี backtick
format: {"name":"ชื่อรายการ","amount":จำนวน,"type":"income หรือ expense","cat":"หมวดหมู่"}
หมวดรายจ่าย: อาหาร, เดินทาง, ช้อปปิ้ง, บิล/สาธารณูปโภค, สุขภาพ, ความงาม, บันเทิง, การศึกษา, อื่นๆ
หมวดรายรับ: เงินเดือน, ฟรีแลนซ์, โบนัส, ลงทุน, อื่นๆ
ถ้าไม่ใช่รายรับ-รายจ่าย ตอบ: null"""
    try:
        raw = await call_groq(system, f'วิเคราะห์: "{text}"', max_tokens=200)
        raw = raw.strip()
        if raw.lower() == "null":
            return None
        # กรณี Groq ใส่ ```json ... ``` มา
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        return None


def fmt_amount(n: float) -> str:
    return f"฿{int(n):,}"


def build_summary(user_id: str, year: int, month: int) -> str:
    entries = db.get_entries(user_id, year, month)
    if not entries:
        return "📭 ยังไม่มีรายการในช่วงนี้"

    income = sum(e["amount"] for e in entries if e["type"] == "income")
    expense = sum(e["amount"] for e in entries if e["type"] == "expense")
    balance = income - expense

    cats: dict[str, float] = {}
    for e in entries:
        if e["type"] == "expense":
            cats[e["cat"]] = cats.get(e["cat"], 0) + e["amount"]

    months_th = ["","ม.ค.","ก.พ.","มี.ค.","เม.ย.","พ.ค.","มิ.ย.",
                 "ก.ค.","ส.ค.","ก.ย.","ต.ค.","พ.ย.","ธ.ค."]

    lines = [
        f"📊 สรุป {months_th[month]} {year + 543}",
        "",
        f"💚 รายรับ:  {fmt_amount(income)}",
        f"❤️ รายจ่าย: {fmt_amount(expense)}",
        f"{'💛' if balance >= 0 else '🔴'} คงเหลือ:  {fmt_amount(balance)}",
    ]

    if cats:
        lines.append("\n📂 รายจ่ายตามหมวด:")
        for cat, amt in sorted(cats.items(), key=lambda x: -x[1]):
            pct = amt / expense * 100 if expense else 0
            lines.append(f"  • {cat}: {fmt_amount(amt)} ({pct:.0f}%)")

    return "\n".join(lines)


def build_list(user_id: str, year: int, month: int) -> str:
    entries = db.get_entries(user_id, year, month)
    if not entries:
        return "📭 ยังไม่มีรายการในเดือนนี้"

    months_th = ["","ม.ค.","ก.พ.","มี.ค.","เม.ย.","พ.ค.","มิ.ย.",
                 "ก.ค.","ส.ค.","ก.ย.","ต.ค.","พ.ย.","ธ.ค."]
    lines = [f"📋 รายการ {months_th[month]} {year + 543}\n"]
    for e in entries[-20:]:
        icon = "💚" if e["type"] == "income" else "❤️"
        sign = "+" if e["type"] == "income" else "-"
        lines.append(f"{icon} {e['name']} ({e['cat']})\n   {sign}{fmt_amount(e['amount'])} · {e['date']}")

    if len(entries) > 20:
        lines.append(f"\n... และอีก {len(entries)-20} รายการ")
    return "\n".join(lines)


@app.get("/")
async def health():
    return {"status": "ok", "service": "LINE Finance Bot (Groq)"}


@app.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    if not verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = json.loads(body)
    for event in data.get("events", []):
        if event["type"] != "message" or event["message"]["type"] != "text":
            continue

        reply_token = event["replyToken"]
        user_id = event["source"]["userId"]
        text = event["message"]["text"].strip()
        now = datetime.now()

        cmd = text.lower().replace(" ", "")

        if cmd in ["ช่วยเหลือ", "help", "เมนู", "menu", "?", "วิธีใช้"]:
            await reply(reply_token, [{"type": "text", "text": HELP_TEXT}])
            continue

        if cmd in ["สรุป", "summary", "report"]:
            msg = build_summary(user_id, now.year, now.month)
            await reply(reply_token, [{"type": "text", "text": msg}])
            continue

        if "สรุปเดือนที่แล้ว" in text or "เดือนที่แล้ว" in text:
            m = now.month - 1 or 12
            y = now.year if now.month > 1 else now.year - 1
            msg = build_summary(user_id, y, m)
            await reply(reply_token, [{"type": "text", "text": msg}])
            continue

        if cmd in ["รายการ", "list", "ดูรายการ"]:
            msg = build_list(user_id, now.year, now.month)
            await reply(reply_token, [{"type": "text", "text": msg}])
            continue

        if cmd in ["วิเคราะห์", "analyze", "ai"]:
            entries = db.get_entries(user_id, now.year, now.month)
            if not entries:
                await reply(reply_token, [{"type": "text", "text": "📭 ยังไม่มีข้อมูล กรุณาบันทึกรายการก่อนนะ"}])
                continue
            income = sum(e["amount"] for e in entries if e["type"] == "income")
            expense = sum(e["amount"] for e in entries if e["type"] == "expense")
            cats = {}
            for e in entries:
                if e["type"] == "expense":
                    cats[e["cat"]] = cats.get(e["cat"], 0) + e["amount"]
            cat_str = ", ".join(f"{k}: {int(v)} บาท" for k, v in cats.items())
            ai_msg = await call_groq(
                "คุณเป็นที่ปรึกษาการเงินส่วนตัว ภาษาไทย เป็นกันเอง กระชับ ตอบ 4-5 ประโยค",
                f"รายรับ: {income} บาท, รายจ่าย: {expense} บาท, คงเหลือ: {income-expense} บาท\nหมวดรายจ่าย: {cat_str}\nวิเคราะห์และให้คำแนะนำ",
                max_tokens=400,
            )
            await reply(reply_token, [{"type": "text", "text": f"🤖 AI วิเคราะห์:\n\n{ai_msg}"}])
            continue

        if text.startswith("ลบ"):
            name = text[2:].strip()
            deleted = db.delete_entry_by_name(user_id, name, now.year, now.month)
            if deleted:
                await reply(reply_token, [{"type": "text", "text": f"🗑️ ลบ '{name}' เรียบร้อยแล้ว"}])
            else:
                await reply(reply_token, [{"type": "text", "text": f"❌ ไม่พบรายการ '{name}' ในเดือนนี้"}])
            continue

        # --- AI Parse รายการ ---
        entry = await parse_entry(text)
        if entry:
            date_str = now.strftime("%Y-%m-%d")
            db.add_entry(
                user_id=user_id,
                name=entry["name"],
                amount=entry["amount"],
                type_=entry["type"],
                cat=entry["cat"],
                date=date_str,
            )
            icon = "💚" if entry["type"] == "income" else "❤️"
            type_th = "รายรับ" if entry["type"] == "income" else "รายจ่าย"
            msg = (
                f"{icon} บันทึกแล้ว!\n\n"
                f"📝 {entry['name']}\n"
                f"💰 {fmt_amount(entry['amount'])}\n"
                f"📂 {type_th} · {entry['cat']}\n"
                f"📅 {date_str}\n\n"
                f'พิมพ์ "สรุป" เพื่อดูภาพรวม'
            )
            await reply(reply_token, [{"type": "text", "text": msg}])
        else:
            # ถาม AI ทั่วไป
            entries = db.get_entries(user_id, now.year, now.month)
            income = sum(e["amount"] for e in entries if e["type"] == "income")
            expense = sum(e["amount"] for e in entries if e["type"] == "expense")
            ai_msg = await call_groq(
                "คุณเป็นที่ปรึกษาการเงินส่วนตัว ภาษาไทย เป็นกันเอง ตอบกระชับใน LINE",
                f"ข้อมูลการเงินเดือนนี้: รายรับ {income} บาท, รายจ่าย {expense} บาท\nคำถาม: {text}",
                max_tokens=300,
            )
            await reply(reply_token, [{"type": "text", "text": f"🤖 {ai_msg}"}])

    return JSONResponse({"status": "ok"})
