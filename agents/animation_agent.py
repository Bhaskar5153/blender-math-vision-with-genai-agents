# agents/animation_agent.py

import os
import sys
os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
from google import genai
from IPython.display import Markdown

from agent_tools.script_saver_tool import save_blender_script
from agent_tools.save_animation_plan_tool import sanitize_filename, save_animation_plan
from agent_tools.name_sanitize_tool import sanitize_name
from agent_tools.subdomain_classification_tool import classify_subdomain
from prompt_modules.animation_prompts.algebra import elementary_algebra

# Load environment variables
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))



class AnimationAgent:
    def __init__(self):
        self.name = "Animation Agent"
        self.description = "Creates animations for math problems to enhance understanding and engagement."

    def generate_markdown_animation_plan(self, user_input: str, solution_text: str, subdomain: str) -> Markdown:
        """
        Generate a markdown animation plan based on the user input, solution, and subdomain.
        """
        if subdomain == "elementary_algebra":
            prompt = elementary_algebra.build_prompt(solution_text, user_input)
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            markdown_plan = response.text.strip()
            animation_plan_filepath = save_animation_plan(markdown=markdown_plan, user_input=user_input)
            return animation_plan_filepath
        else:
            return Markdown(f"⚠️ Animation for subdomain '{subdomain}' is not implemented yet.")

    def generate_blender_script(self, markdown_plan: str, user_input: str, subdomain: str) -> str:
        """
        Generate a Blender script for the animation based on the markdown plan.
        """
        # Use markdown_plan directly as a string
        plan_content = markdown_plan

        if subdomain == "elementary_algebra":
            blender_prompt = elementary_algebra.build_blender_prompt(plan_content)
            response = client.models.generate_content(model="gemini-2.5-flash", contents=blender_prompt)
            blender_script = response.text.strip()

            filename = f"{subdomain}_{sanitize_name(user_input)}.py"
            filepath = save_blender_script(blender_script, filename)
            return filepath
        else:
            raise ValueError(f"Blender script generation for subdomain '{subdomain}' is not implemented.")
