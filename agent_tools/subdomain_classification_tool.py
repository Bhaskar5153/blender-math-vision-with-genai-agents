# this tool is used to identify the subdomain of a given mathematical problem

from google import genai
import os
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
# Initialize the Google GenAI client
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

subdomain_list = [
    "elementary_algebra",
    "linear_algebra",
    "abstract_algebra",
    "boolean_algebra",
    "polynomial_algebra",
    "commutative_algebra",
    "universal_algebra",
    "homological_algebra",
    "computational_algebra"
]


def classify_subdomain(user_input:str, domain:str="algebra") -> str:
    """
    Classify the user input into a specific subdomain of algebra.
    
    Args:
        user_input (str): The input text to classify.
        domain (str): The main domain to classify under, default is "algebra".
    
    Returns:
        str: The classification result.
    """
    if not user_input:
        return "No input provided for classification."

    # prompt the model to classify the input
    prompt = (
        f"""
        Classify the following user input into one of the following subdomains of {domain}:
        {', '.join(subdomain_list)}
        User Input: {user_input}
        Provide the classification as a single word or phrase that best describes the subdomain of the input.
        """
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    
    return response.text.strip()