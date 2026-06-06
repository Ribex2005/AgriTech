import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# -------------------------
# Load datasets
# -------------------------
plant_data = []
bigplant_data = []
# Load embeddings model once at startup


# Load small plant dataset
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

file_path = os.path.join(BASE_DIR, "plant_dataset.jsonl")

with open(file_path, "r", encoding="utf-8") as f:
     for line in f:
        plant_data.append(json.loads(line))

# Load big plant dataset
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

file_path = os.path.join(BASE_DIR, "plant_dataset.jsonl")

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        bigplant_data.append(json.loads(line))

# -------------------------
# Extract questions and answers
# -------------------------
questions = []
answers = []

# Extract from plant dataset
for item in plant_data:
    q = item.get("instruction") or item.get("question", "")
    a = item.get("response") or item.get("output") or item.get("answer", "")
    if q and a:
        questions.append(q)
        answers.append(a)

# Extract from big plant dataset
for item in bigplant_data:
    q = item.get("instruction") or item.get("question") or item.get("prompt", "")
    a = item.get("response") or item.get("output") or item.get("answer") or item.get("completion", "")
    if q and a:
        questions.append(q)
        answers.append(a)

print("Total questions loaded:", len(questions))

if len(questions) == 0:
    raise ValueError("Dataset empty. Check JSON format.")

# -------------------------
# TF-IDF vectorizer
# -------------------------
vectorizer = TfidfVectorizer(stop_words="english")
question_vectors = vectorizer.fit_transform(questions)

# -------------------------
# Help topic keywords
# -------------------------
help_topics = {
    "fertilizer": ["fertilizer", "urea", "dosage", "application", "manure", "nutrient"],
    "pesticide": ["pesticide", "insecticide", "fungicide", "spray", "control", "caterpillar", "worm"],
    "livestock": ["cow", "calf", "livestock", "deworm", "wound", "treatment", "veterinary"],
    "crop_care": ["grow", "cultivate", "planting", "yield", "water", "soil", "harvest", "care", "protect"]
}

# -------------------------
# Search function
# -------------------------
def search_agri_knowledge(user_question):
    user_text = user_question.lower()

    # 1️⃣ Check if question contains any help keywords
    is_help = any(word in user_text for words in help_topics.values() for word in words)

    if is_help:
        # filter questions and answers for help topics only
        filtered_questions = []
        filtered_answers = []
        for q, a in zip(questions, answers):
            q_lower = q.lower()
            if any(word in q_lower for words in help_topics.values() for word in words):
                filtered_questions.append(q)
                filtered_answers.append(a)

        if filtered_questions:
            user_vec = vectorizer.transform([user_question])
            question_vectors_filtered = vectorizer.transform(filtered_questions)
            similarity = cosine_similarity(user_vec, question_vectors_filtered)
            best_match_index = similarity.argmax()
            score = similarity[0][best_match_index]
            if score > 0.2:
                return filtered_answers[best_match_index]
            else:
                return "Sorry, I couldn't find information about this crop."

    # 2️⃣ Default: search all questions
    user_vec = vectorizer.transform([user_question])
    similarity = cosine_similarity(user_vec, question_vectors)
    best_match_index = similarity.argmax()
    score = similarity[0][best_match_index]
    
    if score > 0.15:  # Permissive but excludes noise
        return answers[best_match_index]
    else:
        return "I'm not exactly sure about that. Could you ask about a specific crop disease, market price, or weather?"