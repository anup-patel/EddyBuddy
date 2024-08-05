import speech_recognition as sr
from lms_backend.student_dashboard_backend.learning_coach.call_learning_coach import LearningCoach 
from lms_backend.student_dashboard_backend.performance_bot.call_performance_bot import PerformanceBot
import speech_recognition as sr
from gtts import gTTS
import os
from playsound import playsound
import requests
import json

class FalconLLM:
    def __init__(self, model="tiiuae/falcon-180b-chat"):
        self.api_key = "Enter AI71 API Here"
        self.model = model
        self.api_url = "https://api.ai71.ai/v1/" 
        self.url = f"{self.api_url}chat/completions"

    def generate(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
             {"role": "system", "content": "You are a helpful assistant."},
             {"role": "user", "content": f"{prompt}"}
         ]
     }
        response = requests.post(self.url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Falcon API request failed with status code {response.status_code}: {response.text}")

class SupportBot:
    def __init__(self):
        self.lc = LearningCoach()
        self.pb = PerformanceBot()
        self.recognizer = sr.Recognizer()
        self.llm = FalconLLM()

    # def speech_to_text(self, language):
    #     with sr.Microphone() as source:
    #         print("Please say something...")
    #         audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=5)
    #         try:
    #             text = self.recognizer.recognize_google(audio_data= audio, language=language)
    #             print(f"User said: {text}")
    #             return text
    #         except sr.UnknownValueError:
    #             print("Sorry, I could not understand the audio")
    #             return None
    #         except sr.RequestError as e:
    #             print(f"Could not request results; {e}")
    #             return None

    # def text_to_speech(self, text):
    #     tts = gTTS(text=text, lang='en')
    #     tts.save("response.mp3")
    #     playsound("response.mp3")
    #     os.remove("response.mp3")

    def determine_bot(self, query):

        prompt = f"""
        There are two types of bots available:
        1. Learning Coach Bot: This bot is used to help with learning activities such as practicing, studying, and asking doubts.
        2. Performance Bot: This bot is used to analyze performance, results, grades, attendance and building learning roadmaps.

        Given the query: "{query}", determine which bot should handle this request. Respond with a JSON object containing two keys: 'bot_name' and 'reason'. The 'bot_name' key should be either 'learning_coach' or 'performance_bot' and the 'reason' key should explain why that bot was chosen.
        """
        
        bot_decision = self.llm.generate(prompt)
        bot_decision = json.loads(bot_decision)
        bot_decision = bot_decision.get("bot_name", "learning_coach")

        return bot_decision


    def call_bot(self, bot_name, query, student_id):
        if bot_name.lower() == "learning_coach":
            print("Calling Learning Coach...")
            response = self.lc.run_learning_coach(query)
        elif bot_name.lower() == "performance_bot":
            print("Calling Performance Bot...")
            response = self.pb.run_performance_bot_support(query, student_id)
        #we can point this to a chatbot window in this case
        else:
            response = "I'm sorry, I couldn't understand your request."
        return response

    def run_support_bot(self, student_id,user_query,language = 'en-US'):        
        # Step 1: Convert speech to text
        # Step 1: Convert speech to text
        # self.text_to_speech("Hi, How can I help you today?")
        # user_query = self.speech_to_text()
        if user_query is None:
            return
        
        if language != "en-US":
            print("User is trying to navigate the page in regional language!")
            translation_prompt = f"Translate the following {language} question to English: {user_query}. Return a JSON object with the key 'translated_text' containing the translated text."
            user_query = self.llm.generate(translation_prompt)
            user_query = json.loads(user_query)
            user_query = user_query.get("translated_text", "I want help with understanding something")
        
        # Step 2: Determine which bot to call
        bot_name = self.determine_bot(user_query)
        
        # Step 3: Call the appropriate bot with the query
        response_text = self.call_bot(bot_name, user_query, student_id)

        if language != "en-US":
            translation_prompt = f"Translate the following English text to {language}: {response_text}. Return a JSON object with the key 'translated_text' containing the translated text."
            response_text = self.llm.generate(translation_prompt)
            response_text = json.loads(response_text, strict=False)
            response_text = response_text.get("translated_text", "")
            
        
        # Step 4: Convert the bot's response back to speech
        return response_text
        # self.text_to_speech(response_text)
    
    