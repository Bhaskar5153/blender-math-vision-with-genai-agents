# this tool is used for classifying text or user input
from google import genai
import os
# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Initialize the Google GenAI client
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))



# function to classify the user input

def classify_input(user_input:str) -> str:
    """
    Args:
        user_input (str): The input text to classify.
    Returns:
        str: The classification result.

    description:
        This function takes user input and classifies it into one of the predefined mathematical categories.
        It uses the Google GenAI model to generate a classification based on the input text.
    """
    if not user_input:
        return "No input provided for classification."

    # prompt the model to classify the input
    prompt = (
        f"""
        Classify the following user input into one of the following categories:
        1. Algebra
        2. Geometry
        3. Calculus
        4. Statistics
        5. Trigonometry
        6. Linear Algebra
        7. Number Theory
        8. Combinatorics
        9. Logic
        10. Set Theory
        11. Graph Theory
        12. Probability
        and many more.
        User Input: {user_input}
        Provide the classification as a single word or phrase that best describes the category of the input.
        """
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        
        
    )
    return response.text


# Example usage
if __name__ == "__main__":
    user_input = input("Enter a mathematical problem or concept to classify: ")
    classification_result = classify_input(user_input)
    print(f"Classification Result: {type(classification_result)}")
    print(classification_result)
    
