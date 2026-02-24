# services/surge_service.py

from datetime import datetime, time
import httpx
from core.config import settings

# ======================================================
# 🔧 CONFIG
# ======================================================

CITY = "Hyderabad"  # service city (can be dynamic later)

RAIN_SURGE_AMOUNT = 20

PEAK_SLOTS = [
    {
        "start": time(7, 0),
        "end": time(11, 0),
        "amount": 15,
        "reason": "MORNING_PEAK",
    },
    {
        "start": time(18, 0),
        "end": time(22, 30),
        "amount": 20,
        "reason": "EVENING_PEAK",
    },
    {
        "start": time(22, 30),
        "end": time(1, 0),
        "amount": 35,
        "reason": "LATE_NIGHT_EMERGENCY",
    }
]

REDIS_AMOUNT_KEY = "delivery:surge:amount"
REDIS_REASON_KEY = "delivery:surge:reason"
REDIS_ACTIVE_KEY = "delivery:surge:active"
REDIS_MANUAL_KEY = "delivery:surge:manual"


# ======================================================
# 🌧️ WEATHER CHECK (RAIN)
# ======================================================
async def _is_raining() -> bool:
    # ❌ No API key → skip rain surge safely
    if not settings.WEATHER_API_KEY:
        return False

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?q={settings.SURGE_CITY}&appid={settings.WEATHER_API_KEY}"
    )

    async with httpx.AsyncClient(timeout=5) as client:
        res = await client.get(url)

    if res.status_code != 200:
        return False

    data = res.json()

    return any(
        "rain" in w.get("main", "").lower()
        for w in data.get("weather", [])
    )

# ======================================================
# ⏰ PEAK HOUR CHECK
# ======================================================

def _get_peak_surge(now: datetime):
    current_time = now.time()
    for slot in PEAK_SLOTS:
        if slot["start"] <= current_time <= slot["end"]:
            return slot["amount"], slot["reason"]
    return 0, None


# ======================================================
# 🔄 AUTO SURGE UPDATER (RAIN + PEAK)
# Run via cron / APScheduler / Celery beat
# ======================================================

async def auto_update_surge(redis):
    """
    Priority:
    1️⃣ Manual surge (admin)
    2️⃣ Rain surge
    3️⃣ Peak-hour surge
    """

    # 🚫 Manual surge overrides everything
    if await redis.get(REDIS_MANUAL_KEY):
        return

    # 🌧️ Rain surge
    if await _is_raining():
        await redis.set(REDIS_AMOUNT_KEY, RAIN_SURGE_AMOUNT)
        await redis.set(REDIS_REASON_KEY, "RAIN")
        await redis.set(REDIS_ACTIVE_KEY, 1)
        return

    # ⏰ Peak-hour surge
    amount, reason = _get_peak_surge(datetime.now())
    if amount > 0:
        await redis.set(REDIS_AMOUNT_KEY, amount)
        await redis.set(REDIS_REASON_KEY, reason)
        await redis.set(REDIS_ACTIVE_KEY, 1)
        return

    # ❌ No surge
    await redis.delete(REDIS_AMOUNT_KEY)
    await redis.delete(REDIS_REASON_KEY)
    await redis.delete(REDIS_ACTIVE_KEY)


# ======================================================
# 🛒 CHECKOUT READ (USED BEFORE PAYMENT)
# ======================================================

async def get_active_surge(redis) -> float:
    """
    Called from checkout before payment
    """
    value = await redis.get(REDIS_AMOUNT_KEY)
    return float(value) if value else 0.0


# ======================================================
# 📊 ADMIN CONTROLS
# ======================================================

async def admin_set_surge(redis, amount: float, reason: str = "MANUAL"):
    await redis.set(REDIS_AMOUNT_KEY, amount)
    await redis.set(REDIS_REASON_KEY, reason)
    await redis.set(REDIS_ACTIVE_KEY, 1)
    await redis.set(REDIS_MANUAL_KEY, 1)


async def admin_disable_surge(redis):
    await redis.delete(REDIS_AMOUNT_KEY)
    await redis.delete(REDIS_REASON_KEY)
    await redis.delete(REDIS_ACTIVE_KEY)
    await redis.delete(REDIS_MANUAL_KEY)


async def admin_get_surge(redis):
    return {
        "active": bool(await redis.get(REDIS_ACTIVE_KEY)),
        "amount": float(await redis.get(REDIS_AMOUNT_KEY) or 0),
        "reason": await redis.get(REDIS_REASON_KEY),
    }
