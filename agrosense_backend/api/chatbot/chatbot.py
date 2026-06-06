import difflib
import os
import pickle
import re
import sys

# Force UTF-8 encoding for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from .diseasefile import disease_data as disease_db
    from .diseasefile import CROP_CARE, CROP_FERTILIZERS
except Exception:
    from .diseasefile import disease_data as disease_db
    CROP_CARE = {}
    CROP_FERTILIZERS = {"General": "Use balanced NPK after soil testing."}

from .knowledge_engine import search_agri_knowledge
from .market_service import get_market_price
from .weather_service import get_weather

try:
    from . import translator_service
except Exception:
    class _TranslatorFallback:
        @staticmethod
        def detect_language(_text):
            return "en"

        @staticmethod
        def translate_to_english(text):
            return text

        @staticmethod
        def translate_from_english(text, _lang):
            return text

    translator_service = _TranslatorFallback()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "chatbot_model.pkl")

model = None
vectorizer = None
try:
    with open(MODEL_PATH, "rb") as f:
        model, vectorizer = pickle.load(f)
except Exception:
    model = None
    vectorizer = None


def predict_intent_ml(user_text):
    """Return (intent, confidence) from the trained classifier."""
    if model is None or vectorizer is None:
        return None, 0.0

    try:
        text_vec = vectorizer.transform([user_text])
        predicted = model.predict(text_vec)[0]
        confidence = 0.0

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(text_vec)[0]
            confidence = float(max(proba))

        return str(predicted), confidence
    except Exception:
        return None, 0.0


last_crop = None
active_context = {
    "intent": None,
    "symptoms": [],
    "crop": None,
    "last_topic": None,
    "last_disease": None,
    "last_disease_crop": None,
    "last_disease_info": None,
}


def normalize_crop_name(crop_name):
    if not crop_name:
        return None
    crop_title = str(crop_name).strip().title()
    if crop_title == "Corn":
        return "Maize"
    if crop_title == "Soybean":
        return "Soyabean"
    return crop_title


def build_fertilizer_advice(crop_name):
    normalized = normalize_crop_name(crop_name)
    if normalized and normalized in CROP_FERTILIZERS:
        return CROP_FERTILIZERS[normalized]
    return CROP_FERTILIZERS.get("General", "Use balanced NPK after soil testing.")


def extract_crop(text, allow_fuzzy=False):
    text = str(text).lower()

    aliases = {
        "maize": "corn",
        "maizes": "corn",
        "paddy": "rice",
        "capsicum": "bell pepper",
        "capsicums": "bell pepper",
        "soybean": "soyabean",
        "soybeans": "soyabean",
        "potatoes": "potato",
        "tomatoes": "tomato",
        "carrots": "carrot",
        "onions": "onion",
    }

    for alias, standard_name in aliases.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", text):
            return standard_name.lower()

    available_crops = list(disease_db.keys())

    # 1) Phrase match with plural variants for multi-word crops.
    for crop in available_crops:
        crop_l = crop.lower()
        variants = {crop_l, f"{crop_l}s"}

        if crop_l.endswith("y") and len(crop_l) > 1:
            variants.add(f"{crop_l[:-1]}ies")
        if crop_l.endswith("o"):
            variants.add(f"{crop_l}es")

        if any(re.search(r"\b" + re.escape(v) + r"\b", text) for v in variants):
            return crop_l

    for crop in available_crops:
        if re.search(r"\b" + re.escape(crop.lower()) + r"\b", text):
            return crop.lower()

    # 2) Token-level singularization for words like potatoes/carrots.
    def _singularize(word):
        if len(word) <= 3:
            return word
        if word.endswith("ies") and len(word) > 4:
            return word[:-3] + "y"
        if word.endswith("oes") and len(word) > 4:
            return word[:-2]
        if word.endswith("es") and len(word) > 4:
            return word[:-2]
        if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
            return word[:-1]
        return word

    words = re.findall(r"[a-z]+", text)
    normalized_words = list(words)
    normalized_words.extend(_singularize(w) for w in words)

    if allow_fuzzy:
        for word in normalized_words:
            if len(word) < 4:
                continue
            matches = difflib.get_close_matches(word, [c.lower() for c in available_crops], n=1, cutoff=0.9)
            if matches:
                return matches[0]

    return None


def extract_all_crops(text):
    if not text:
        return []

    text_lower = str(text).lower()
    found = []
    for crop in disease_db.keys():
        if re.search(r"\b" + re.escape(crop.lower()) + r"\b", text_lower):
            found.append(crop)
    return found


locations = [
    "delhi", "mumbai", "bangalore", "hyderabad", "chennai", "kolkata", "pune", "ahmedabad",
    "jaipur", "lucknow", "kanpur", "nagpur", "new delhi", "noida", "gurgaon", "dehradun",
]


def extract_location(message):
    text = str(message).lower()
    for city in locations:
        if city in text:
            return city

    match = re.search(r"weather in ([a-zA-Z\s]+)", text)
    if match:
        extracted = match.group(1).strip()
        matches = difflib.get_close_matches(extracted, locations, n=1, cutoff=0.6)
        if matches:
            return matches[0]
        return extracted

    return "pune"


def infer_cure_status(disease_name, disease_info):
    d_name = str(disease_name).lower()
    info_text = disease_info if isinstance(disease_info, str) else disease_info.get("treatment", "")
    info_text = str(info_text).lower()

    if "virus" in d_name or "viral" in info_text:
        return "Usually not fully curable once infected, but spread can be controlled."
    if "no cure" in info_text:
        return "No complete cure is available after infection, but management can reduce damage."
    return "Yes, it is generally manageable if detected early and treated promptly."


def treatability_label(disease_name, disease_info):
    status = infer_cure_status(disease_name, disease_info).lower()
    if "not fully curable" in status or "no complete cure" in status:
        return "Not fully curable"
    return "Curable"


def treatability_tag(disease_name, disease_info):
    label = treatability_label(disease_name, disease_info)
    return "[Not fully treatable]" if "Not fully" in label else "[Treatable]"


def build_disease_list_with_curability(crop_name, limit=8):
    diseases = []
    crop_data = disease_db.get(crop_name, {})
    for d_name, d_info in crop_data.items():
        if d_name == "Healthy":
            continue
        diseases.append(f"- {d_name} ({treatability_label(d_name, d_info)})")
        if len(diseases) >= limit:
            break
    return "\n".join(diseases)


def remember_last_diagnosis(crop_name, disease_name, disease_info):
    active_context["last_disease"] = disease_name
    active_context["last_disease_crop"] = crop_name
    active_context["last_disease_info"] = disease_info


def build_context_treatment_reply():
    d_name = active_context.get("last_disease")
    d_crop = active_context.get("last_disease_crop")
    d_info = active_context.get("last_disease_info")

    if not d_name or not d_crop:
        return None

    cure_status = infer_cure_status(d_name, d_info)
    if isinstance(d_info, dict):
        treatment = d_info.get("treatment", "No specific treatment recorded.")
        prevention = d_info.get("prevention", "No specific prevention recorded.")
    else:
        treatment = str(d_info) if d_info else "No specific treatment recorded."
        prevention = "Use sanitation, crop rotation, and preventive sprays."

    return "\n".join([
        f"**{d_name} ({d_crop}) {treatability_tag(d_name, d_info)}**",
        f"- **Curable?** {cure_status}",
        f"- **Treatment/Cure**: {treatment}",
        f"- **Prevention**: {prevention}",
        f"- **Fertilizer Advice ({d_crop})**: {build_fertilizer_advice(d_crop)}",
    ])


def find_specific_disease(text, preferred_crop=None):
    lowered = str(text).lower()
    pref = normalize_crop_name(preferred_crop)
    matches = []

    for crop_name, diseases in disease_db.items():
        for disease_name, disease_info in diseases.items():
            if disease_name == "Healthy":
                continue
            if disease_name.lower() in lowered:
                matches.append((crop_name, disease_name, disease_info))

    if not matches:
        return None

    if pref:
        for match in matches:
            if match[0] == pref:
                return match

    return matches[0]


def build_specific_disease_reply(text, preferred_crop=None):
    match = find_specific_disease(text, preferred_crop)
    if not match:
        return None

    crop_name, disease_name, disease_info = match
    is_cure_query = re.search(r"\b(cure|curable|treat|treatment|control|manage|prevent|fertilizer|medicine)\b", str(text).lower())
    if not is_cure_query:
        return None

    remember_last_diagnosis(crop_name, disease_name, disease_info)
    cure_status = infer_cure_status(disease_name, disease_info)

    if isinstance(disease_info, dict):
        treatment = disease_info.get("treatment", "No specific treatment recorded.")
        prevention = disease_info.get("prevention", "No specific prevention recorded.")
    else:
        treatment = str(disease_info)
        prevention = "Use sanitation, crop rotation, and preventive sprays."

    return "\n".join([
        f"**{disease_name} ({crop_name}) {treatability_tag(disease_name, disease_info)}**",
        f"- **Curable?** {cure_status}",
        f"- **Treatment/Cure**: {treatment}",
        f"- **Prevention**: {prevention}",
        f"- **Fertilizer Advice ({crop_name})**: {build_fertilizer_advice(crop_name)}",
    ])


def disease_response(user_input, context_crop=None):
    text = str(user_input).lower()
    crop = extract_crop(text, allow_fuzzy=True) or context_crop

    if crop:
        crop = crop.title()

    if crop and crop in disease_db:
        crop_diseases = disease_db[crop]

        if re.search(r"\b(diseases|problems|issues|common)\b", text):
            diseases = build_disease_list_with_curability(crop, limit=8)
            if diseases:
                return f"Common diseases affecting **{crop}** are:\n{diseases}"

        matched = []
        for d_name, d_info in crop_diseases.items():
            if d_name == "Healthy":
                continue
            token = d_name.lower().replace("-", " ")
            if token in text:
                matched.append((d_name, d_info))

        if matched:
            d_name, d_info = matched[0]
            remember_last_diagnosis(crop, d_name, d_info)
            if isinstance(d_info, dict):
                treatment = d_info.get("treatment", "No specific treatment recorded.")
                prevention = d_info.get("prevention", "No specific prevention recorded.")
            else:
                treatment = str(d_info)
                prevention = "Use sanitation, crop rotation, and preventive sprays."
            return "\n".join([
                f"Likely issue in **{crop}**: **{d_name} {treatability_tag(d_name, d_info)}**",
                f"- Treatment/Cure: {treatment}",
                f"- Prevention: {prevention}",
                f"- Fertilizer Advice ({crop}): {build_fertilizer_advice(crop)}",
            ])

        disease_list = ", ".join([d for d in crop_diseases if d != "Healthy"])
        return f"Crop: {crop}\nCommon diseases: {disease_list}\n\nTell symptoms for better diagnosis."

    if not crop:
        return "Please mention the crop and symptoms (e.g., Tomato yellow leaves)."

    return "No data available for this crop."


def build_crop_advice_reply(user_text, crop_hint=None):
    explicit_crop = extract_crop(user_text, allow_fuzzy=False)
    followup_ref = re.search(r"\b(it|this|that|same)\b", str(user_text).lower())

    crop = explicit_crop
    if not crop and crop_hint and followup_ref:
        crop = crop_hint

    if crop:
        crop = normalize_crop_name(crop)

    if not crop:
        return None

    lower_text = str(user_text).lower()
    wants_fertilizer = re.search(r"\b(fertilizer|fertiliser|npk|nutrient|dose|dosage|manure|apply|application)\b", lower_text)
    wants_care = re.search(r"\b(care|cultivate|cultivation|grow|growing|water|irrigation|soil|planting|harvest)\b", lower_text)

    if wants_fertilizer:
        return f"**Fertilizer Advice ({crop})**: {build_fertilizer_advice(crop)}"

    if wants_care:
        care_text = CROP_CARE.get(crop, CROP_CARE.get("General", "Follow local best practices and soil-test-based nutrient planning."))
        return f"**Crop Care ({crop})**: {care_text}"

    return None


def get_bot_response(user_input_raw):
    global last_crop, active_context

    original_input = str(user_input_raw)
    detected_lang = "en"
    try:
        detected_lang = translator_service.detect_language(original_input)
    except Exception:
        detected_lang = "en"

    try:
        english_input = translator_service.translate_to_english(original_input) if detected_lang != "en" else original_input
    except Exception:
        english_input = original_input

    user_text = english_input.lower().strip()

    if re.search(r"\b(hi|hello|hey|namaste|greetings)\b", user_text):
        reply = "Hello! I am AgriChat. Ask about crop diseases, weather, market prices, or farming tips."
        if detected_lang != "en":
            try:
                reply = translator_service.translate_from_english(reply, detected_lang)
            except Exception:
                pass
        return {"response": reply, "intent": "greeting", "context": active_context}

    current_crop = extract_crop(user_text, allow_fuzzy=False)
    if current_crop:
        last_crop = current_crop
        active_context["crop"] = current_crop

    direct_crop_advice = build_crop_advice_reply(user_text, current_crop or last_crop)
    if direct_crop_advice:
        intent = "knowledge"
        if re.search(r"\b(fertilizer|fertiliser|npk|nutrient|dose|dosage|manure|apply|application)\b", user_text):
            active_context["last_topic"] = "fertilizer"
        elif re.search(r"\b(care|cultivate|cultivation|grow|growing|water|irrigation|soil|planting|harvest)\b", user_text):
            active_context["last_topic"] = "crop_care"
        active_context["intent"] = intent
        if detected_lang != "en":
            try:
                direct_crop_advice = translator_service.translate_from_english(direct_crop_advice, detected_lang)
            except Exception:
                pass
        return {"response": direct_crop_advice, "intent": intent, "context": active_context}

    followup_treat_query = re.search(r"\b(treat|treatment|cure|curable|control|manage|prevent|medicine)\b.*\b(it|this|that)\b", user_text)
    if followup_treat_query:
        memory_reply = build_context_treatment_reply()
        if memory_reply:
            if detected_lang != "en":
                try:
                    memory_reply = translator_service.translate_from_english(memory_reply, detected_lang)
                except Exception:
                    pass
            return {"response": memory_reply, "intent": "disease", "context": active_context}

    predicted_intent, _confidence = predict_intent_ml(user_text)

    # Fallback only if model is unavailable/failed.
    if not predicted_intent:
        if "weather" in user_text:
            predicted_intent = "weather"
        elif "price" in user_text or "rate" in user_text:
            predicted_intent = "market"
        elif any(k in user_text for k in ["scheme", "loan", "subsidy", "news", "gov", "help"]):
            predicted_intent = "scheme"
        elif current_crop or "disease" in user_text:
            predicted_intent = "disease"
        else:
            predicted_intent = "general"

    if predicted_intent == "weather":
        city = extract_location(user_text)
        answer = get_weather(city)
        intent = "weather"
    elif predicted_intent == "market":
        crop = extract_crop(user_text, allow_fuzzy=False) or last_crop
        answer = get_market_price(crop) if crop else "Please specify which crop price you want."
        intent = "market"
    elif predicted_intent in ["scheme", "help", "knowledge"]:
        answer = search_agri_knowledge(user_text)
        intent = "knowledge"
    elif predicted_intent == "disease":
        answer = build_specific_disease_reply(english_input, current_crop or last_crop)
        if not answer:
            answer = disease_response(english_input, current_crop or last_crop)
        intent = "disease"
    else:
        answer = search_agri_knowledge(user_text)
        intent = "general"

    active_context["intent"] = intent

    if detected_lang != "en":
        try:
            answer = translator_service.translate_from_english(answer, detected_lang)
        except Exception:
            pass

    return {
        "response": answer,
        "intent": intent,
        "context": active_context,
    }


if __name__ == "__main__":
    print("AGRI-TECH AI ASSISTANT READY")
    while True:
        user_input_raw = input("You: ").strip()
        if user_input_raw.lower() in ["exit", "quit", "bye"]:
            break
        result = get_bot_response(user_input_raw)
        print("Bot:", result.get("response", ""))