import os
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === 配置 ===
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
STATS_FILE = "stats.json"

# === 初始化统计文件 ===
if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, 'w') as f:
        json.dump({"count": 0, "keywords": {}, "daily": {}}, f)

# === 更新计数 ===
def increment_counter(keyword="其他"):
    today = datetime.now().strftime("%Y-%m-%d")
    with open(STATS_FILE, 'r') as f:
        data = json.load(f)

    data["count"] += 1
    data["keywords"][keyword] = data["keywords"].get(keyword, 0) + 1
    data["daily"][today] = data["daily"].get(today, 0) + 1

    with open(STATS_FILE, 'w') as f:
        json.dump(data, f)
    return data

# === /send 命令 ===
async def send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("用法：/send 内容")
        return
    text = " ".join(context.args)
    keyword = text.split()[0]
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHANNEL_ID, text=text)
    data = increment_counter(keyword)
    await update.message.reply_text(
        f"✅ 已发送。\n总数：{data['count']} 条\n关键词“{keyword}”出现：{data['keywords'][keyword]} 次")

# === /count 命令 ===
async def count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(STATS_FILE, 'r') as f:
        data = json.load(f)
    await update.message.reply_text(f"📊 当前总发送条数：{data['count']}")

# === /top20 命令 ===
async def top20(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(STATS_FILE, 'r') as f:
        data = json.load(f)
    keywords = data.get("keywords", {})
    if not keywords:
        await update.message.reply_text("❗ 暂无关键词记录")
        return

    sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
    top_items = sorted_keywords[:20]

    result = "🏆 关键词排行榜 TOP20\n"
    for i, (word, count) in enumerate(top_items, 1):
        result += f"{i}. {word} - {count} 次\n"
    await update.message.reply_text(result)

# === /chart 命令 ===
async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(STATS_FILE, 'r') as f:
        data = json.load(f)
    dates = list(data["daily"].keys())
    values = list(data["daily"].values())

    if not dates:
        await update.message.reply_text("📉 暂无图表数据")
        return

    plt.figure(figsize=(10, 5))
    plt.bar(dates, values)
    plt.xticks(rotation=45)
    plt.title("每日消息统计")
    plt.xlabel("日期")
    plt.ylabel("消息数量")
    plt.tight_layout()
    plt.savefig("chart.png")
    plt.close()

    await update.message.reply_photo(photo=open("chart.png", "rb"))

# === /top7days 命令 ===
async def top7days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().date()
    with open(STATS_FILE, 'r') as f:
        data = json.load(f)

    counts = {}
    for date_str, count in data.get("daily", {}).items():
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            if 0 <= (today - date_obj).days < 7:
                counts[date_str] = count
        except:
            continue

    if not counts:
        await update.message.reply_text("📅 最近7天没有数据")
        return

    result = "📆 近7天消息统计排行榜：\n"
    for date in sorted(counts.keys(), reverse=True):
        result += f"{date} - {counts[date]} 条\n"
    await update.message.reply_text(result)

# === 启动主程序 ===
async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("send", send))
    app.add_handler(CommandHandler("count", count))
    app.add_handler(CommandHandler("top20", top20))
    app.add_handler(CommandHandler("chart", chart))
    app.add_handler(CommandHandler("top7days", top7days))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
