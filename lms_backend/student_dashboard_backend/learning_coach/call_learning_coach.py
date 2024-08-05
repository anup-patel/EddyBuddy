from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import FAISS
import json
import requests


class FalconLLM:
    def __init__(self, model="tiiuae/falcon-180b-chat"):
        self.api_key = "ENTER AI71 API"
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
        

class LearningCoach:
    def __init__(self):
        self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.db = FAISS.load_local('../db/notes_vector_store', self.embeddings, allow_dangerous_deserialization=True)
        self.llm = FalconLLM()

    def run_learning_coach(self, query):
        result = self.db.similarity_search(query, k=1)[0]
        context = result.page_content

        prompt = f"Based on the following notes:\n\n{context}\n\nAnswer the following question: {query}"
        
        response = self.llm.generate(prompt)
        return response
    
# ******* sample code *******    
# if __name__ == "__main__":
#     lc = LearningCoach()
#     query = "What is the capital of France?"
#     response = lc.run_learning_coach(query)
#     print(response)