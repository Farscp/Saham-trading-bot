import time
import requests
import yfinance as yf
import pandas as pd

# ==========================================
# 1. إعدادات بوت التليجرام الخاص بك
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
# 2. قائمة المراقبة العالمية والمحلية الشاملة
# ==========================================
WATCHLIST = [
    # 🇸🇦 السوق السعودي (TADAWUL)
    {"symbol": "1120.SR", "name": "مصرف الراجحي", "category": "🇸🇦 القطاع البنكي السعودي"},
    {"symbol": "2222.SR", "name": "أرامكو السعودية", "category": "🇸🇦 قطاع الطاقة السعودي"},
    {"symbol": "1180.SR", "name": "البنك الأهلي السعودي", "category": "🇸🇦 القطاع البنكي السعودي"},
    {"symbol": "7010.SR", "name": "إس تي سي STC", "category": "🇸🇦 الاتصالات السعودية"},
    {"symbol": "4330.SR", "name": "صندوق دراية ريت", "category": "🇸🇦 صناديق العقار والمبالغ"},
    
    # 🇺🇸 عمالقة التكنولوجيا والنمو
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "category": "🇺🇸 الذكاء الاصطناعي والرقائق"},
    {"symbol": "AAPL", "name": "Apple Inc.", "category": "🇺🇸 التقنية الاستهلاكية"},
    {"symbol": "MSFT", "name": "Microsoft", "category": "🇺🇸 السحابيات والذكاء الاصطناعي"},
    {"symbol": "GOOGL", "name": "Alphabet (Google)", "category": "🇺🇸 محركات البحث والإعلان"},
    {"symbol": "AMZN", "name": "Amazon", "category": "🇺🇸 التجارة الإلكترونية والسحابية"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "category": "🇺🇸 السيارات الكهربائية"},

    # 🌐 الاقتصاد العالمي والأسواق الناشئة
    {"symbol": "VT", "name": "Vanguard Total World Stock", "category": "🌐 أسهم العالم أجمع (تنوع عالمي)"},
    {"symbol": "VWO", "name": "Vanguard FTSE Emerging Markets", "category": "🌏 الأسواق الناشئة (الصين، الهند، إلخ)"},
    {"symbol": "VOO", "name": "Vanguard S&P 500 ETF", "category": "🇺🇸 أكبر 500 شركة أمريكية"},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust", "category": "💻 مؤشر قطاع التقنية الأمريكي"},

    # 🥇 الذهب والنفط (الملاذات الآمنة والسلع)
    {"symbol": "GLD", "name": "SPDR Gold Shares", "category": "🥇 صندوق الذهب العالمي"},
    {"symbol": "USO", "name": "United States Oil Fund", "category": "🛢️ صندوق النفط الخام"}
]

# ذاكرة مؤقتة لمنع تكرار التنبيهات خلال 24 ساعة
last_alert_times = {}
COOLDOWN_PERIOD = 86400  # 24 ساعة

# ==========================================
# 3. جلب الأخبار العاجلة
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
# 4. دالة الفحص والتحليل الفني
# ==========================================
def analyze_market():
    print("جاري فحص الأسواق العالمية والمحلية...")
    current_time = time.time()

    for item in WATCHLIST:
        symbol = item["symbol"]
        name = item["name"]
        category = item["category"]

        try:
            # جلب البيانات لآخر 60 يوم
            df = yf.download(symbol, period="60d", interval="1d", progress=False)
            if df.empty or len(df) < 20:
                continue

            close_prices = df['Close']
            if isinstance(close_prices, pd.DataFrame):
                close_prices = close_prices.iloc[:, 0]

            # حساب مؤشر القوة النسبية RSI
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # المتوسط المتحرك SMA 20
            sma_20 = close_prices.rolling(window=20).mean()

            last_close = float(close_prices.iloc[-1])
            prev_close = float(close_prices.iloc[-2])
            last_rsi = float(rsi.iloc[-1])
            last_sma = float(sma_20.iloc[-1])
            
            change_percent = ((last_close - prev_close) / prev_close) * 100

            # شرط التنبيه: تشبع بيعي (RSI < 35) فرصة ارتداد
            if last_rsi < 35:
                # تصفية التكرار خلال 24 ساعة
                if symbol in last_alert_times:
                    if current_time - last_alert_times[symbol] < COOLDOWN_PERIOD:
                        continue

                last_alert_times[symbol] = current_time
                news_text = get_latest_news_summary(symbol)

                # تحديد العملة حسب السوق
                currency = "SAR" if ".SR" in symbol else "USD"

                message = (
                    f"🚨 *تنبيه فرصة استثمارية عالمية/محليّة*\n\n"
                    f"📌 *الأصل / السهم:* {name} (`{symbol}`)\n"
                    f"📁 *التصنيف:* {category}\n\n"
                    f"📊 *الحالة الفنية:* 🎯 فرصة دخول محتملة (منطقة تشبع بيعي)\n"
                    f"💵 *السعر الحالي:* {last_close:.2f} {currency}\n"
                    f"📈 *التغير اليومي:* {change_percent:.2f}%\n"
                    f"📉 *مؤشر RSI:* {last_rsi:.1f}\n"
                    f"⚖️ *المتوسط المتحرك (SMA 20):* {last_sma:.2f}\n\n"
                    f"{news_text}\n\n"
                    f"🟢 *سعر الدخول المقترح:* {last_close:.2f} {currency}\n"
                    f"🛑 *وقف الخسارة الآمن:* {last_close * 0.97:.2f} {currency}\n"
                    f"🎯 *الهدف الأول:* {last_close * 1.04:.2f} {currency}\n"
                    f"🎯 *الهدف الثاني:* {last_close * 1.08:.2f} {currency}"
                )

                send_telegram_message(message)
                time.sleep(1)

        except Exception as e:
            print(f"خطأ أثناء تحليل {symbol}: {e}")

# ==========================================
# 5. التشغيل المستمر
# ==========================================
if __name__ == "__main__":
    print("تم إقلاع الرادار العالمي والمحلي بنجاح...")
    while True:
        analyze_market()
        time.sleep(3600)  # فحص كلي كل ساعة
