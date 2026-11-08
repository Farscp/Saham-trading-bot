import time
import requests
import yfinance as yf
import pandas as pd

# ==========================================
# 1. إعدادات بوت التليجرام (مجهزة خصيصاً لك)
# ==========================================
TELEGRAM_TOKEN = "7547055038:AAFiM05sW1J649aY0gY2S5N83k2hR_9lJ8M"
TELEGRAM_CHAT_ID = "7155078564"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"خطأ في إرسال الرسالة: {e}")

# ==========================================
# 2. قائمة المراقبة الموسعة (أسهم وصناديق متنوعة)
# ==========================================
WATCHLIST = [
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "category": "أشباه الموصلات والذكاء الاصطناعي"},
    {"symbol": "AAPL", "name": "Apple Inc.", "category": "التكنولوجيا الاستهلاكية"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "category": "السيارات الكهربائية"},
    {"symbol": "VOO", "name": "Vanguard S&P 500 ETF", "category": "صناديق المؤشرات الكبرى"},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust", "category": "صناديق قطاع التقنية"}
]

# ذاكرة مؤقتة لتخزين وقت آخر تنبيه لكل سهم (منع التكرار)
last_alert_times = {}
COOLDOWN_PERIOD = 86400  # 24 ساعة بالثواني

# ==========================================
# 3. جلب الأخبار وتحليل المشاعر المبسط
# ==========================================
def get_latest_news_summary(symbol):
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        if news and len(news) > 0:
            latest = news[0]
            title = latest.get('title', 'لا توجد عناوين حديثة')
            publisher = latest.get('publisher', 'مصدر مالي')
            return f"📰 *آخر خبر ({publisher}):* {title}"
    except Exception:
        pass
    return "📰 *الأخبار:* لا توجد أخبار جوهرية جديدة مرصودة."

# ==========================================
# 4. دالة التحليل الفني والفحص
# ==========================================
def analyze_market():
    print("جاري فحص الأسواق والأصول...")
    current_time = time.time()

    for item in WATCHLIST:
        symbol = item["symbol"]
        name = item["name"]
        category = item["category"]

        try:
            # جلب البيانات التاريخية آخر 60 يوم
            df = yf.download(symbol, period="60d", interval="1d", progress=False)
            if df.empty or len(df) < 20:
                continue

            # معالجة بيانات الإغلاق لضمان توافقها كمتسلسلة رقمية بحتة
            close_prices = df['Close']
            if isinstance(close_prices, pd.DataFrame):
                close_prices = close_prices.iloc[:, 0]

            # حساب مؤشر القوة النسبية RSI (14)
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # المتوسط المتحرك البسيط SMA 20
            sma_20 = close_prices.rolling(window=20).mean()

            last_close = float(close_prices.iloc[-1])
            prev_close = float(close_prices.iloc[-2])
            last_rsi = float(rsi.iloc[-1])
            last_sma = float(sma_20.iloc[-1])
            
            change_percent = ((last_close - prev_close) / prev_close) * 100

            # شرط التنبيه: تشبع بيعي (RSI < 35) فرصة ارتداد
            if last_rsi < 35:
                # التحقق من نظام Cooldown (منع تكرار التنبيه خلال 24 ساعة)
                if symbol in last_alert_times:
                    if current_time - last_alert_times[symbol] < COOLDOWN_PERIOD:
                        continue  # تخطي التنبيه لعدم إزعاجك بتكرار نفس السهم

                # تحديث وقت آخر تنبيه
                last_alert_times[symbol] = current_time

                # جلب الخبر المرتبط
                news_text = get_latest_news_summary(symbol)

                # صياغة الرسالة الاحترافية
                message = (
                    f"🚨 *تنبيه تحليل فني وأخباري متقدم*\n\n"
                    f"📌 *الأصل / الصندوق:* {name} (`{symbol}`)\n"
                    f"📁 *التصنيف:* {category}\n\n"
                    f"📊 *الحالة الفنية:* 🎯 فرصة استثمارية محتملة (منطقة تشبع بيعي)\n"
                    f"💵 *السعر الحالي:* {last_close:.2f} USD\n"
                    f"📈 *التغير اليومي:* {change_percent:.2f}%\n"
                    f"📉 *مؤشر القوة النسبية (RSI):* {last_rsi:.1f}\n"
                    f"⚖️ *المتوسط المتحرك (SMA 20):* {last_sma:.2f}\n\n"
                    f"{news_text}\n\n"
                    f"🟢 *سعر الدخول المقترح:* {last_close:.2f}\n"
                    f"🛑 *وقف الخسارة الآمن:* {last_close * 0.97:.2f}\n"
                    f"🎯 *الهدف الأول:* {last_close * 1.04:.2f}\n"
                    f"🎯 *الهدف الثاني:* {last_close * 1.08:.2f}"
                )

                send_telegram_message(message)
                time.sleep(1)

        except Exception as e:
            print(f"خطأ أثناء تحليل السهم {symbol}: {e}")

# ==========================================
# 5. حلقة التدوير المستمرة (Loop)
# ==========================================
if __name__ == "__main__":
    print("تم إقلاع البوت بنجاح وبدأ مراقبة الأسواق...")
    while True:
        analyze_market()
        # فحص السوق كل ساعة لتفادي تكرار الرسائل وتوفير استهلاك السيرفر
        time.sleep(3600)
