# this module contains the TrigonometryAgent class
import os
import sys
from google import genai
from dotenv import load_dotenv

# load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY)

class TrigonometryAgent:
    def __init__(self):
        self.name = "Trigonometry Agent"
        self.description = "Handles the trigonometry related questions and tasks."

    def solve(self, user_input: str) -> str:
        """
        Process the user input and return a response related to trigonometry.
        Args:
            user_input (str): The input text from the user.

        Returns:
            str: The response generated for the user input.
        """
        # Here you would implement the logic to process the user input
        prompt = (
            f"""
            +  You are an trigonometry expert.
            +  Provide a detailed explanation or solution to the following trigonometry problem:
            +  {user_input}
            """
        )
        # and generate a response related to trigonometry.
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        # This could involve calling the subdomain classification tool,
        # and then using the classification to generate a relevant response.

        return response.text.strip()
    