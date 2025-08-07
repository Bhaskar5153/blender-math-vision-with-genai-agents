# from google import genai

# import os
# # Load environment variables from .env file
# from dotenv import load_dotenv
# load_dotenv()
# # Initialize the Google GenAI client
# os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")


# client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# response = client.models.generate_content(
#     model="gemini-2.5-flash",
#     contents="Explain how AI works in a few words",
# )

# print(response.text)