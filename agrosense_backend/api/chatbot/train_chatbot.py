import random
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import os
print("Saving in:", os.getcwd())
templates = {
    "market": [
"What is the price of {crop}?",
"Market price of {crop}",
"Mandi price of {crop}",
"What is the rate of {crop}?",
"Today's price of {crop}",
"Current price of {crop}",
"How much is {crop} selling for?",
"Rate of {crop} in the market",
"Price of {crop} in {location}",
"Latest price of {crop}",
"How expensive is {crop} today?",
"Mandi rate of {crop}",
"What is the cost of {crop} today?"
],

    "weather": [
"What is the weather in {location}?",
"Weather forecast in {location}",
"Temperature in {location}",
"Will it rain in {location}?",
"Is it raining in {location}?",
"Current weather in {location}",
"Weather today in {location}",
"Humidity in {location}",
"How hot is it in {location}?",
"Rain prediction in {location}",
"Weather conditions in {location}",
"Is it sunny in {location}?"
],
   "scheme": [
"Government schemes for farmers",
"Farmer subsidy schemes",
"PM Kisan scheme details",
"Crop insurance scheme",
"Any agriculture subsidy?",
"Government support for farmers",
"Agriculture loan schemes",
"Financial schemes for farmers",
"Farmer welfare schemes",
"Government programs for agriculture"
],
    "disease": [
"My {crop} leaves have yellow spots",
"My {crop} leaves have brown spots",
"My {crop} plant is dying",
"White powder on {crop} leaves",
"Fungus on {crop}",
"Why are my {crop} leaves curling?",
"Disease in {crop}",
"{crop} plant infected",
"Pests attacking my {crop}",
"What disease affects {crop}?",
"{crop} leaves turning yellow",
"Spots appearing on {crop} leaves"
],
    "general": [
"Hello",
"Hi",
"Hey",
"Good morning",
"Good afternoon",
"Good evening",
"Hello chatbot",
"Hi chatbot",
"How are you",
"Are you there",
"Who are you",
"What is AgroSense",
"Can you help me",
"Hi there",
"Greetings"
],
    "help": [
"How to grow {crop}?",
"Best fertilizer for {crop}",
"How to increase {crop} yield?",
"What soil is best for {crop}?",
"How much water does {crop} need?",
"When should I plant {crop}?",
"Tips for growing {crop}",
"How to cultivate {crop}?",
"Best way to grow {crop}",
"How to protect {crop} from pests?",
"What nutrients are present in {crop}?",
"What are the benefits of {crop}?",
"Tell me about {crop}",
"Is {crop} healthy?",
"Is {crop} gluten free?",
"Why is {crop} important?",
"What are the uses of {crop}?",
"How many species of {crop} exist?"
]
}

crops = [

# Cereals
"wheat","rice","maize","corn","barley","sorghum","millet","ragi","foxtail millet",
"kodo millet","little millet","barnyard millet","proso millet","pearl millet",

# Pulses
"lentils","chickpea","pigeon pea","green gram","black gram","cowpea",
"field pea","horse gram","moth bean","rajma","soybean",

# Oilseeds
"mustard","groundnut","sunflower","sesame","linseed","castor","safflower",

# Vegetables
"potato","tomato","onion","garlic","ginger","turmeric","chilli","pepper",
"carrot","cabbage","cauliflower","spinach","lettuce","cucumber","pumpkin",
"bottle gourd","ridge gourd","bitter gourd","snake gourd","ash gourd",
"brinjal","eggplant","okra","ladyfinger","radish","turnip","beetroot",
"capsicum","peas","beans","sweet potato",

# Fruits
"apple","banana","mango","grapes","orange","lemon","papaya","guava",
"pomegranate","watermelon","muskmelon","strawberry","pineapple",
"jackfruit","lychee","pear","peach","plum","apricot","cherry","kiwi",

# Plantation crops
"tea","coffee","coconut","arecanut","rubber","jute","cocoa",

# Spices
"cardamom","clove","cinnamon","nutmeg","black pepper","fenugreek",
"coriander","cumin","fennel","mustard seed",

# Special / pseudo cereals
"amaranth","quinoa","buckwheat"
]


locations=[
    "andhra pradesh", "arunachal pradesh", "assam", "bihar",
    "chhattisgarh", "goa", "gujarat", "haryana",
    "himachal pradesh", "jharkhand", "karnataka", "kerala",
    "madhya pradesh", "maharashtra", "manipur", "meghalaya",
    "mizoram", "nagaland", "odisha", "punjab",
    "rajasthan", "sikkim", "tamil nadu", "telangana",
    "tripura", "uttar pradesh", "uttarakhand", "west bengal"
]

data = []
for intent, sentences in templates.items():
    for _ in range(300):
        sentence = random.choice(sentences)
        sentence = sentence.format(
            crop=random.choice(crops),
            location=random.choice(locations)
        )
        data.append([sentence, intent])
df = pd.DataFrame(data, columns=["text", "intent"])
# df.to_csv("d:/data/chatbot_dataset.csv", index=False)
df.to_csv("chatbot_dataset.csv", index=False)

print("Dataset saved as chatbot_dataset.csv")
X = df["text"]
y = df["intent"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
vectorizer = TfidfVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)
model = LogisticRegression(max_iter=200)

model.fit(X_train_vec, y_train)
y_pred = model.predict(X_test_vec)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nConfusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))

pickle.dump((model, vectorizer), open("chatbot_model.pkl", "wb"))

pimport random
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import os
print("Saving in:", os.getcwd())
templates = {
    "market": [
"What is the price of {crop}?",
"Market price of {crop}",
"Mandi price of {crop}",
"What is the rate of {crop}?",
"Today's price of {crop}",
"Current price of {crop}",
"How much is {crop} selling for?",
"Rate of {crop} in the market",
"Price of {crop} in {location}",
"Latest price of {crop}",
"How expensive is {crop} today?",
"Mandi rate of {crop}",
"What is the cost of {crop} today?"
],

    "weather": [
"What is the weather in {location}?",
"Weather forecast in {location}",
"Temperature in {location}",
"Will it rain in {location}?",
"Is it raining in {location}?",
"Current weather in {location}",
"Weather today in {location}",
"Humidity in {location}",
"How hot is it in {location}?",
"Rain prediction in {location}",
"Weather conditions in {location}",
"Is it sunny in {location}?"
],
   "scheme": [
"Government schemes for farmers",
"Farmer subsidy schemes",
"PM Kisan scheme details",
"Crop insurance scheme",
"Any agriculture subsidy?",
"Government support for farmers",
"Agriculture loan schemes",
"Financial schemes for farmers",
"Farmer welfare schemes",
"Government programs for agriculture"
],
    "disease": [
"My {crop} leaves have yellow spots",
"My {crop} leaves have brown spots",
"My {crop} plant is dying",
"White powder on {crop} leaves",
"Fungus on {crop}",
"Why are my {crop} leaves curling?",
"Disease in {crop}",
"{crop} plant infected",
"Pests attacking my {crop}",
"What disease affects {crop}?",
"{crop} leaves turning yellow",
"Spots appearing on {crop} leaves"
],
    "general": [
"Hello",
"Hi",
"Hey",
"Good morning",
"Good afternoon",
"Good evening",
"Hello chatbot",
"Hi chatbot",
"How are you",
"Are you there",
"Who are you",
"What is AgroSense",
"Can you help me",
"Hi there",
"Greetings"
],
    "help": [
"How to grow {crop}?",
"Best fertilizer for {crop}",
"How to increase {crop} yield?",
"What soil is best for {crop}?",
"How much water does {crop} need?",
"When should I plant {crop}?",
"Tips for growing {crop}",
"How to cultivate {crop}?",
"Best way to grow {crop}",
"How to protect {crop} from pests?",
"What nutrients are present in {crop}?",
"What are the benefits of {crop}?",
"Tell me about {crop}",
"Is {crop} healthy?",
"Is {crop} gluten free?",
"Why is {crop} important?",
"What are the uses of {crop}?",
"How many species of {crop} exist?"
]
}

crops = [

# Cereals
"wheat","rice","maize","corn","barley","sorghum","millet","ragi","foxtail millet",
"kodo millet","little millet","barnyard millet","proso millet","pearl millet",

# Pulses
"lentils","chickpea","pigeon pea","green gram","black gram","cowpea",
"field pea","horse gram","moth bean","rajma","soybean",

# Oilseeds
"mustard","groundnut","sunflower","sesame","linseed","castor","safflower",

# Vegetables
"potato","tomato","onion","garlic","ginger","turmeric","chilli","pepper",
"carrot","cabbage","cauliflower","spinach","lettuce","cucumber","pumpkin",
"bottle gourd","ridge gourd","bitter gourd","snake gourd","ash gourd",
"brinjal","eggplant","okra","ladyfinger","radish","turnip","beetroot",
"capsicum","peas","beans","sweet potato",

# Fruits
"apple","banana","mango","grapes","orange","lemon","papaya","guava",
"pomegranate","watermelon","muskmelon","strawberry","pineapple",
"jackfruit","lychee","pear","peach","plum","apricot","cherry","kiwi",

# Plantation crops
"tea","coffee","coconut","arecanut","rubber","jute","cocoa",

# Spices
"cardamom","clove","cinnamon","nutmeg","black pepper","fenugreek",
"coriander","cumin","fennel","mustard seed",

# Special / pseudo cereals
"amaranth","quinoa","buckwheat"
]


locations=[
    "andhra pradesh", "arunachal pradesh", "assam", "bihar",
    "chhattisgarh", "goa", "gujarat", "haryana",
    "himachal pradesh", "jharkhand", "karnataka", "kerala",
    "madhya pradesh", "maharashtra", "manipur", "meghalaya",
    "mizoram", "nagaland", "odisha", "punjab",
    "rajasthan", "sikkim", "tamil nadu", "telangana",
    "tripura", "uttar pradesh", "uttarakhand", "west bengal"
]

data = []
for intent, sentences in templates.items():
    for _ in range(300):
        sentence = random.choice(sentences)
        sentence = sentence.format(
            crop=random.choice(crops),
            location=random.choice(locations)
        )
        data.append([sentence, intent])
df = pd.DataFrame(data, columns=["text", "intent"])
# df.to_csv("d:/data/chatbot_dataset.csv", index=False)
df.to_csv("chatbot_dataset.csv", index=False)

print("Dataset saved as chatbot_dataset.csv")
X = df["text"]
y = df["intent"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
vectorizer = TfidfVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)
model = LogisticRegression(max_iter=200)

model.fit(X_train_vec, y_train)
y_pred = model.predict(X_test_vec)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nConfusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))

pickle.dump((model, vectorizer), open("chatbot_model.pkl", "wb"))

print("Model saved as chatbot_model.pkl")rint("Model saved as chatbot_model.pkl")