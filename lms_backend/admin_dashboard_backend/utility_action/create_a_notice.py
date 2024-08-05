import json
import requests
import base64
import os

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
        # print(response.text)
        if response.status_code == 200:
            # print(response.json())
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Falcon API request failed with status code {response.status_code}: {response.text}")

class CreateANotice:

    def __init__(self):
        self.falcon_llm = FalconLLM()

    def generate_notice_content(self, topic):
        prompt = f"Write a 2-line notice on the following topic: {topic}. Example : if the topic is 'new library opening' the notice can be : 'We are pleased to announce the opening of our new library. The library will be open to all students from 9 AM to 5 PM.' Return a json with two keys - notice and title of notice. The value of notice should be the generated notice content and the value of title of notice should be the topic. Only return the JSON and not other text."
        response_text = self.falcon_llm.generate(prompt)
        return response_text

    def generate_image_prompt(self, topic):
        prompt = f"I want to create an image for the following topic: {topic}. Identify the keys elements that should be a part of image related to this topic and Return a JSON with the image prompt that I can pass to an LLM to generate image accordingly."
        response_text = self.falcon_llm.generate(prompt)
        return response_text

    def generate_image(self, image_prompt):
        
        url = "https://api.freepik.com/v1/ai/text-to-image"

        payload = {
            "prompt": image_prompt,
            "image": {"size": "square"},
            "num_images": 1
        }
        headers = {
            "x-freepik-api-key": "Enter Freepik API",
            "Accept-Language": "en-US",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        response = requests.request("POST", url, json=payload, headers=headers)

        if response.status_code == 200:
            image_data = response.json()
            if 'data' in image_data and len(image_data['data']) > 0:
                # Decode the base64 image and save it
                for i, img_data in enumerate(image_data['data']):
                    img_base64 = img_data['base64']
                    img_bytes = base64.b64decode(img_base64)
                    img_filename = f"static/generated_image_{i}.png"
                    with open(img_filename, "wb") as img_file:
                        img_file.write(img_bytes)
                    print(f"Image saved as {img_filename}")
                    return img_filename
            else:
                print("No images found for the given prompt.")
                return None
        else:
            print(f"Error in image generation request: {response.status_code}, {response.text}")
            return None

    def extract_json_from_string(self, string):
        json_start = string.find("{")
        json_end = string.rfind("}") + 1
        json_string = string[json_start:json_end]
        json_data = json.loads(json_string)
        return json_data

    def run_create_notice(self, topic):

        # Step 1: Generate notice content
        content = self.generate_notice_content(topic)
        content = self.extract_json_from_string(content)
        notice_content = content.get("notice")
        notice_title = content.get("title of notice")

        # Step 2: Generate image prompt
        image_prompt = self.generate_image_prompt(notice_title)

        # Step 3: Generate image
        img_filename=self.generate_image(image_prompt)
        return {"img_url":img_filename,"title": notice_title,"description": notice_content}
