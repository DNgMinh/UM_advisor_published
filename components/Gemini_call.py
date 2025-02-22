import os
import google.generativeai as genai_old
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from dotenv import load_dotenv

load_dotenv()

class GeminiService():
    def __init__(self, model_name: str = "gemini-2.0-flash", instruction1_file: str = "components/instruction1.txt", historyLimit: int = 3):
        genai_old.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_name = model_name
        self.model = genai_old.GenerativeModel(model_name=model_name)
        # instruction_path = os.path.abspath(instruction_file)
        self.instruction1 = self.loadFile(instruction1_file)
        # self.instruction2 = self.loadFile(instruction2_file)
        self.historyLimit = historyLimit
        self.chatHistory = []

        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


    def loadFile(self, file):
        with open(file, "r", encoding="utf-8") as f:
            return " ".join(line.strip() for line in f if line.strip())

        
    def getResponse(self, prompt: str, relevant_context: str) -> str:
        # print(relevant_context)
        # instruction = self.instruction1 if type == 1 else self.instruction2
        # instruction = self.instruction1

        historyText = "\n".join([f"User: {p}\nGemini: {r}" for p, r in self.chatHistory])

        full_prompt = f"## Instructions ##\n{self.instruction1}\n\n## Relevant University Info ##\n{relevant_context}\n\n## Chat History ##\n{historyText}\n\nUser: {prompt}"
        response = self.model.generate_content(full_prompt)

        if response and response.text:
            if not response.text[0] == "0" and not response.text[-1] == "0":
                # Store only the user prompt and response
                self.chatHistory.append((prompt, response.text))

            # Limit history size to save memory
            if len(self.chatHistory) > self.historyLimit:
                self.chatHistory.pop(0)  # Remove the oldest message

            return response.text
        else:
            return "No response received"
        
    def getResponseWithSearch(self, prompt: str) -> str:
        """
        Generate a response using Google Search grounding.
        """
        google_search_tool = Tool(
            google_search = GoogleSearch()
        )

        historyText = "\n".join([f"User: {p}\nGemini: {r}" for p, r in self.chatHistory])

        # print(f"I am a University of Manitoba student. {prompt}\n## Chat History ##\n{historyText}")

        response = self.client.models.generate_content(
            model=self.model_name,
            contents = f"I am a University of Manitoba student. {prompt}\n## Chat History ##\n{historyText}",
            config=GenerateContentConfig(
                tools=[google_search_tool],
                response_modalities=["TEXT"],
            )
        )

        if response and response.candidates:
            for each in response.candidates[0].content.parts:
                # if each.text.strip():  # Ensure the response is not empty
                #     if self.chatHistory:
                #         self.chatHistory[-1] = (prompt, each.text)  # Replace last element
                #     else:
                self.chatHistory.append((prompt, each.text))  # Add if empty
                
                if len(self.chatHistory) > self.historyLimit:
                    self.chatHistory.pop(0)  # Remove the oldest message

                return each.text  # Return only the first available response
            
            return "No response received with search grounding."
        else:
            return "No response received."


