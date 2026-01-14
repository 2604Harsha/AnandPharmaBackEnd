import json
import os
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.chat import ChatResponse
from services.product_service import search_products_by_name
from services.cart_service import add_to_cart, get_cart_items
from services.order_service import get_order_by_number

DATA_DIR = "data"


# -------------------------------------------------
# Language Detection
# -------------------------------------------------
def detect_language(text: str) -> str:
    t = text.lower().strip()

    # Explicit language selection
    if t in ["english", "en"]:
        return "en"
    if t in ["hindi"]:
        return "hin"
    if t in ["telugu"]:
        return "te"

    # Unicode detection
    for ch in text:
        if "\u0C00" <= ch <= "\u0C7F":  # Telugu
            return "te"
        if "\u0900" <= ch <= "\u097F":  # Hindi
            return "hi"

    return "en"


# -------------------------------------------------
# Language Responses
# -------------------------------------------------
LANG_RESPONSES = {
    "en": {
        "greet": "👋 Hi! Welcome to Anand Pharma. How can I help you?",
        "ask_med": "💊 Please type the medicine name",
        "not_found": "❌ Sorry, I couldn’t understand that.",
        "rx_required": "⚠️ This medicine requires a valid prescription.",
        "added_cart": "🛒 Medicine added to cart successfully!",
        "options": {
            "main": [
                "Search medicine",
                "Medicine usage",
                "View cart",
                "Track order",
                "Talk to pharmacist"
            ],
            "after_search": [
                "Add to cart",
                "Medicine usage",
                "View cart"
            ]
        }
    },
    "hi": {
        "greet": "👋 नमस्ते! आनंद फार्मा में आपका स्वागत है।",
        "ask_med": "💊 कृपया दवा का नाम लिखें",
        "not_found": "❌ मुझे समझ नहीं आया।",
        "rx_required": "⚠️ इस दवा के लिए प्रिस्क्रिप्शन आवश्यक है।",
        "added_cart": "🛒 दवा कार्ट में जोड़ दी गई है!",
        "options": {
            "main": [
                "दवा खोजें",
                "दवा का उपयोग",
                "कार्ट देखें",
                "ऑर्डर ट्रैक करें",
                "फार्मासिस्ट से बात करें"
            ],
            "after_search": [
                "कार्ट में जोड़ें",
                "दवा का उपयोग",
                "कार्ट देखें"
            ]
        }
    },
    "te": {
        "greet": "👋 హాయ్! ఆనంద్ ఫార్మాకు స్వాగతం.",
        "ask_med": "💊 మందు పేరును టైప్ చేయండి",
        "not_found": "❌ క్షమించండి, నాకు అర్థం కాలేదు.",
        "rx_required": "⚠️ ఈ మందుకు ప్రిస్క్రిప్షన్ అవసరం.",
        "added_cart": "🛒 మందు కార్ట్‌లోకి జోడించబడింది!",
        "options": {
            "main": [
                "మందు వెతకండి",
                "మందు ఉపయోగాలు",
                "కార్ట్ చూడండి",
                "ఆర్డర్ ట్రాక్ చేయండి",
                "ఫార్మాసిస్ట్‌తో మాట్లాడండి"
            ],
            "after_search": [
                "కార్ట్‌లో జోడించండి",
                "మందు ఉపయోగాలు",
                "కార్ట్ చూడండి"
            ]
        }
    }
}


# -------------------------------------------------
# Chatbot Service
# -------------------------------------------------
class ChatbotService:

    def __init__(self):
        self.medicine_index = self._load_all_medicines()
        self.last_search_result = None

    # --------------------------------------------------
    # LOAD MEDICINES FROM JSON
    # --------------------------------------------------
    def _load_all_medicines(self):
        medicines = []

        if not os.path.exists(DATA_DIR):
            return medicines

        for file in os.listdir(DATA_DIR):
            if file.endswith(".json"):
                with open(os.path.join(DATA_DIR, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        medicines.extend(data)
                    elif isinstance(data, dict):
                        for key in ["medications", "tablets", "insulin"]:
                            medicines.extend(data.get(key, []))

        return medicines

    # --------------------------------------------------
    # JSON SEARCH
    # --------------------------------------------------
    def _search_json_medicine(self, query: str):
        query = query.lower()
        return [
            m for m in self.medicine_index
            if query in m.get("name", "").lower()
        ][:5]

    # --------------------------------------------------
    # MEDICINE USAGE
    # --------------------------------------------------
    def _get_medicine_usage(self, name: str):
        name = name.lower()
        for m in self.medicine_index:
            if name in m.get("name", "").lower():
                return m.get("description") or m.get("usage")
        return None

    # --------------------------------------------------
    # MAIN CHAT HANDLER
    # --------------------------------------------------
    async def process_message(
        self,
        message: str,
        db: AsyncSession,
        user_id: int
    ) -> ChatResponse:

        msg = message.lower().strip()
        lang_key = detect_language(message)
        lang = LANG_RESPONSES[lang_key]

        # ---------- GREETING ----------
        if msg in ["hi", "hello", "hey", "start", "నమస్తే", "హాయ్", "नमस्ते"]:
            return ChatResponse(
                reply=lang["greet"],
                options=lang["options"]["main"]
            )

        # ---------- ASK MEDICINE ----------
        if msg in ["search medicine", "medicine", "दवा", "మందు"]:
            return ChatResponse(reply=lang["ask_med"])

        # ---------- MEDICINE USAGE ----------
        if any(x in msg for x in ["usage of", "use of", "medicine usage"]):
            name = msg.replace("usage of", "").replace("use of", "").replace("medicine usage", "").strip()
            usage = self._get_medicine_usage(name)

            if not usage:
                return ChatResponse(reply="❌ Medicine usage not found")

            return ChatResponse(
                reply=f"💊 {name.title()} – Usage",
                items=[{"medicine": name.title(), "description": usage}],
                options=lang["options"]["after_search"]
            )

        # ---------- DB SEARCH (CLEAN & DEDUPED) ----------
        products = await search_products_by_name(db, msg)
        if products:
            self.last_search_result = products[0]

            seen = set()
            items = []
            rx_required = False

            for p in products:
                key = (p.name, p.price)
                if key in seen:
                    continue
                seen.add(key)

                items.append({
                    "name": p.name,
                    "price": p.price
                })

                if getattr(p, "requires_prescription", False):
                    rx_required = True

            reply = f"✅ **{products[0].name}** is available."
            if rx_required:
                reply += f"\n\n{lang['rx_required']}"

            return ChatResponse(
                reply=reply,
                items=items,
                options=lang["options"]["after_search"]
            )

        # ---------- JSON SEARCH ----------
        json_results = self._search_json_medicine(msg)
        if json_results:
            self.last_search_result = json_results[0]
            return ChatResponse(
                reply="✅ Medicine available",
                items=json_results,
                options=lang["options"]["after_search"]
            )

        # ---------- ADD TO CART ----------
        if "add to cart" in msg or "కార్ట్" in msg or "कार्ट" in msg:
            if not self.last_search_result:
                return ChatResponse(reply="🛒 Please search a medicine first")

            await add_to_cart(
                db=db,
                user_id=user_id,
                product_id=self.last_search_result.id,
                quantity=1
            )

            return ChatResponse(
                reply=lang["added_cart"],
                options=lang["options"]["main"]
            )

        # ---------- VIEW CART ----------
        if "view cart" in msg:
            cart_items = await get_cart_items(db, user_id)
            if not cart_items:
                return ChatResponse(reply="🛒 Your cart is empty")

            items = [{
                "name": i.product.name,
                "price": i.product.price,
                "quantity": i.quantity
            } for i in cart_items]

            return ChatResponse(
                reply="🛒 Your Cart",
                items=items,
                options=["Place order"]
            )

        # ---------- TRACK ORDER ----------
        if "track order" in msg or "track" in msg:
            return ChatResponse(reply="📦 Enter Order ID (ORD000123)")

        if msg.startswith("ord"):
            order = await get_order_by_number(db, msg.upper())
            if not order:
                return ChatResponse(reply="❌ Order not found")

            return ChatResponse(
                reply=f"📦 Order {order.order_number}",
                meta={
                    "status": order.status,
                    "payment": order.payment_status
                }
            )

        # ---------- PHARMACIST ----------
        if "pharmacist" in msg:
            return ChatResponse(
                reply="👩‍⚕️ Pharmacist Support",
                items=[{"phone": "+91 98765 43210", "time": "9 AM – 9 PM"}]
            )

        # ---------- FALLBACK ----------
        return ChatResponse(
            reply=lang["not_found"],
            options=lang["options"]["main"]
        )


chatbot_service = ChatbotService()
