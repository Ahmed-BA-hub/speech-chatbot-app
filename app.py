import streamlit as st
import nltk
from nltk.chat.util import Chat, reflections
from nltk.tokenize import sent_tokenize
import speech_recognition as sr
import random
import platform
import os

# ----------- Detect Cloud Environment ------------
IS_CLOUD = os.getenv("STREAMLIT_ENV") == "cloud" or platform.system() == "Linux"

# ----------- NLTK Punkt Setup ---------------------
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

# ----------- Load Corpus --------------------------
with open("chatbot.txt", "r", encoding="utf-8") as file:
    corpus = file.read()

sent_tokens = sent_tokenize(corpus)

# ----------- Chatbot Rules ------------------------
pairs = [
    [r"hi|hello|hey", ["Hello!", "Hi there!", "Hey! How can I help?"]],
    [r"how are you", ["I'm a bot, but I'm functioning perfectly!"]],
    [r"what is your name\??", ["I'm your speech-enabled chatbot."]],
    [r"what (.*) do you (.*)", ["I'm trained to help you with basic conversations."]],
    [r"(.*) (weather|time|news)", ["I'm a simple bot and don't have access to real-time info."]],
    [r"quit", ["Goodbye!"]],
    [r"(.*)", ["I'm not sure I understand. Can you rephrase that?"]]
]
chatbot = Chat(pairs, reflections)

# ----------- Streamlit Session State ----------------
if "recording" not in st.session_state:
    st.session_state.recording = False
if "audio_data" not in st.session_state:
    st.session_state.audio_data = None

# ----------- Mic Logic (Local Only) -----------------
def start_recording():
    st.session_state.recording = True
    st.info("🎙️ Listening... speak now and press STOP when done.")

def stop_recording():
    if IS_CLOUD:
        st.warning("❌ Microphone not supported on Streamlit Cloud.")
        return

    st.session_state.recording = False
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🔈 Capturing audio... Please speak clearly.")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            text = recognizer.recognize_google(audio)
            st.session_state.audio_data = text
        except sr.WaitTimeoutError:
            st.session_state.audio_data = "No speech detected. Try again."
        except sr.UnknownValueError:
            st.session_state.audio_data = "Sorry, I could not understand the audio."
        except sr.RequestError:
            st.session_state.audio_data = "Speech recognition service failed."

# ----------- Chatbot Response ------------------------
def chatbot_response(user_input):
    if not user_input.strip():
        return "I didn't catch that. Can you say it again?"

    response = chatbot.respond(user_input)
    if not response or response.strip() == "":
        for sentence in sent_tokens:
            if user_input.lower() in sentence.lower():
                return sentence
        return random.choice(sent_tokens)
    return response

# ----------- Streamlit UI ----------------------------
st.title("🧠 Speech-Enabled Chatbot")
st.write("Talk or type to chat with the bot.")

input_type = st.radio("Choose input type:", ["Text", "Speech"])
user_input = ""

if input_type == "Text":
    user_input = st.text_input("You:")

elif input_type == "Speech":
    if IS_CLOUD:
        st.warning("🎙️ Microphone is disabled on Streamlit Cloud. Please use Text input.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎙️ Start Recording"):
                start_recording()
        with col2:
            if st.button("⏹️ Stop Recording"):
                stop_recording()

        if st.session_state.audio_data:
            user_input = st.session_state.audio_data
            st.text_area("Transcribed Text:", value=user_input, height=100)

# ----------- Bot Reply -------------------------------
if user_input:
    with st.spinner("Bot is thinking..."):
        response = chatbot_response(user_input)
    st.text_area("Bot says:", value=response, height=100)
