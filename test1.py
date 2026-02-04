import pyttsx3
from textblob import TextBlob
import random
import os
import time

# =======================
# Initialisation TTS
# =======================
engine = pyttsx3.init()
voices = engine.getProperty('voices')

# =======================
# Textes exemples
# =======================
example_texts = [
    "Je suis tellement heureux aujourd'hui, tout va bien !",
    "Je me sens triste et seul, rien ne va...",
    "Aujourd'hui est un jour comme les autres.",
    "Quelle belle surprise ! Je n'y croyais pas !",
    "Je suis très fatigué et stressé par le travail.",
    "J'ai juste besoin d'une tasse de café.",
    "C'est incroyable ce qui m'arrive !",
    "Je n'ai pas envie de parler à qui que ce soit.",
    "Le ciel est bleu et les oiseaux chantent.",
    "Rien de spécial aujourd'hui, tout est calme."
]

# =======================
# Musiques par humeur
# =======================
music_files = {
    "heureux": ["happy1.mp3", "happy2.mp3"],
    "triste": ["sad1.mp3", "sad2.mp3"],
    "calme": ["calm1.mp3", "calm2.mp3"],
    "excité": ["excited1.mp3", "excited2.mp3"],
    "fatigué": ["tired1.mp3", "tired2.mp3"]
}

# =======================
# Réponses amusantes par humeur
# =======================
responses = {
    "heureux": ["Super ! Lisons avec énergie ! 😄", "Youpi ! Lecture joyeuse !"],
    "triste": ["Je vais lire doucement... 😢", "Prenons notre temps, lecture triste."],
    "calme": ["Lecture tranquille... 😌", "Un texte neutre, relaxons-nous."],
    "excité": ["Wouah ! Lisons avec enthousiasme ! 🤩", "Ça va bouger ! Lecture excitée !"],
    "fatigué": ["Lecture lente, je suis fatigué... 😴", "Doucement, lecture calme."]
}

# =======================
# Choix aléatoire du texte
# =======================
text = random.choice(example_texts)

# =======================
# Analyse sentiment avec TextBlob
# =======================
polarity = TextBlob(text).sentiment.polarity

# Déterminer humeur avancée
if polarity > 0.5:
    mood = "excité"
elif polarity > 0.2:
    mood = "heureux"
elif polarity < -0.5:
    mood = "triste"
elif polarity < -0.2:
    mood = "fatigué"
else:
    mood = "calme"

# Choisir voix aléatoire
voice_id = random.choice(voices).id
engine.setProperty('voice', voice_id)

# Choisir vitesse selon humeur
rate_dict = {"heureux":180, "excité":200, "triste":120, "fatigué":110, "calme":150}
engine.setProperty('rate', rate_dict[mood])

# Choisir musique aléatoire
music_file = random.choice(music_files[mood])

# Choisir réponse amusante
response_text = random.choice(responses[mood])

# =======================
# Afficher infos
# =======================
print(f"\n📜 Texte choisi : {text}")
print(f"🎭 Humeur détectée : {mood}")
print(f"🎤 Voix choisie : {voice_id}")
print(f"⏱ Vitesse lecture : {rate_dict[mood]}")
print(f"🎶 Musique choisie : {music_file}")
print(f"💬 Réponse avant lecture : {response_text}\n")

# =======================
# Animation du texte à l’écran
# =======================
for char in response_text:
    print(char, end="", flush=True)
    time.sleep(0.05)
print("\n")

# =======================
# Lire réponse
# =======================
engine.say(response_text)
engine.runAndWait()

# =======================
# Lire le texte
# =======================
for char in text:
    print(char, end="", flush=True)
    time.sleep(0.03)
print("\n")

engine.say(text)
engine.runAndWait()

# =======================
# Jouer musique
# =======================
if os.path.exists(music_file):
    os.system(f"start {music_file}")  # Windows
else:
    print(f"(Pas de musique trouvée pour {mood})")
