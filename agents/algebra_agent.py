# Import necessary modules
import os
from dotenv import load_dotenv
from google import genai
from agent_tools.classifier_tool import classify_input
from agent_tools.subdomain_classification_tool import classify_subdomain
# Load environment variables from .env file
load_dotenv()
# Initialize the Google GenAI client
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


# create algebra agent
class AlgebraAgent:
    def __init__(self):
        self.name = "Algebra Agent"
        self.description = "Handles algebra-related queries and tasks."

    

    def solve(self, user_input: str) -> str:
        """
        Process the user input and return a response related to algebra.
        Args:
            user_input (str): The input text from the user.
        Returns:
            str: The response to the user's query.
        """

        # Here you would implement the logic to handle algebra-related queries with genai client and gemini 2.5 flash model.
        prompt = (
            f"""
            +  You are an algebra expert.
            +  Provide a detailed explanation or solution to the following algebra problem:
            +  {user_input}
            """
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        return response.text.strip()
    
    

