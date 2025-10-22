# this tool is used to identify the subdomain of a given mathematical problem

from google import genai
import os
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
# Initialize the Google GenAI client
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

subdomain_list_algebra = [
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

subdomain_list_trigonometry = [
    "basic_trigonometric_ratios",
    "trigonometric_identities_and_equations",
    "graphical_trigonometry",
    "inverse_trigonometric_functions",
    "analytic_trigonometry",
    "trigonometry_of_general_triangles",
    "circular_and_polar_trigonometry",
    "applications_of_trigonometry"
]

subdomain_lists = {
    "algebra": subdomain_list_algebra,
    "trigonometry": subdomain_list_trigonometry
    # Add more domains and their subdomains here as needed
}


def classify_subdomain(user_input: str, domain: str) -> str:
    """
    Classify the user input into a specific subdomain of the given math domain.
    
    Args:
        user_input (str): The input text to classify.
        domain (str): The main domain to classify under.
    
    Returns:
        str: The classification result.
    """
    if not user_input:
        return "No input provided for classification."

    domain_key = domain.lower()
    subdomain_list = subdomain_lists.get(domain_key, None)

    if subdomain_list:
        prompt = (
            f"""
            Classify the following user input into one of the following subdomains of {domain}:
            {', '.join(subdomain_list)}
            User Input: {user_input}
            Provide the classification as a single word or phrase that best describes the subdomain of the input.
            """
        )
    else:
        prompt = (
            f"""
            Classify the following user input into a subdomain of {domain}.
            User Input: {user_input}
            Provide the classification as a single word or phrase that best describes the subdomain of the input.
            """
        )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    
    return response.text.strip()