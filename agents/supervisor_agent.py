
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from agent_tools.classifier_tool import classify_input
from agent_tools.subdomain_classification_tool import classify_subdomain
from agents.algebra_agent import AlgebraAgent
from agents.animation_agent import AnimationAgent
# from agents.geometry_agent import GeometryAgent
# from agents.calculus_agent import CalculusAgent
# from agents.statistics_agent import StatisticsAgent
# from agents.trigonometry_agent import TrigonometryAgent
# from agents.linear_algebra_agent import LinearAlgebraAgent
# from agents.number_theory_agent import NumberTheoryAgent
# from agents.combinatorics_agent import CombinatoricsAgent
# from agents.logic_agent import LogicAgent
# from agents.set_theory_agent import SetTheoryAgent
# from agents.graph_theory_agent import GraphTheoryAgent
# from agents.probability_agent import ProbabilityAgent

class SupervisorAgent:
    def __init__(self):
        self.domain_agents = {
            "algebra": AlgebraAgent(),
            # "geometry": GeometryAgent(),
            # "calculus": CalculusAgent(),
            # "statistics": StatisticsAgent(),
            # "trigonometry": TrigonometryAgent(),
            # "linear_algebra": LinearAlgebraAgent(),
            # "number_theory": NumberTheoryAgent(),
            # "combinatorics": CombinatoricsAgent(),
            # "logic": LogicAgent(),
            # "set_theory": SetTheoryAgent(),
            # "graph_theory": GraphTheoryAgent(),
            # "probability": ProbabilityAgent(),
            
        }
        self.animation_agent = AnimationAgent()

    def normalize_math_domain(self, raw_domain: str) -> str:
        """
        Normalize the raw domain string to a standard format.
        Args:
            raw_domain (str): The raw domain string to normalize.
        Returns:
            str: The normalized domain string.
        """
        return raw_domain.strip().replace(" ", "_").lower()
    
    def handle_user_input(self, user_input: str) -> dict:
        """
        Handle user input by classifying it and delegating to the appropriate agent.
        Args:
            user_input (str): The input text from the user.
        Returns:
            str: The response from the appropriate agent.
        """
        domain = classify_input(user_input)
        subdomain = classify_subdomain(user_input, domain)
        normalized_domain = self.normalize_math_domain(domain)
        agent = self.domain_agents.get(normalized_domain)
        
        if not agent:
            return {
                "domain": normalized_domain,
                "solution": f"No agent found for the domain: {domain}.",
                "agent": "None",
                "animation_agent": None,
                "blender_script": None,
                "user_input": user_input,
                "subdomain": subdomain,
            }

        
        solution = agent.solve(user_input)
        animation_plan = self.animation_agent.generate_markdown_animation_plan(user_input, solution, subdomain)
        blender_script = self.animation_agent.generate_blender_script(markdown_plan=animation_plan, user_input=user_input, subdomain=subdomain)
        return {
            "domain": domain,
            "subdomain": subdomain,
            "solution": solution,
            "agent": agent.__class__.__name__,
            "user_input": user_input,
            "animation_plan": animation_plan,
            "blender_script": blender_script
        
        }
        

if __name__ == "__main__":
    supervisor = SupervisorAgent()
    user_input = input("Enter a mathematical problem or concept: ")
    response = supervisor.handle_user_input(user_input)
    print(f"Domain: {response['domain']}")
    print(f"Solution: {response['solution']}")
    print(f"Agent Used: {response['agent']}")
    print(f"User Input: {response['user_input']}")
    print(f"Animation Plan: {response['animation_plan']}")
    print(f"Subdomain: {response['subdomain']}")
    print(f"blender script: {response['blender_script']}")