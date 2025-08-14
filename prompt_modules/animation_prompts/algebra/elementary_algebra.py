def build_prompt(solution_text: str, user_input: str) -> str:
    return f"""
🎓 You are a cinematic Blender animation agent for math education.

Your task is to visualize an **elementary algebra** problem and its solution using clear, symbolic, and engaging animation.

────────────────────────────────────────────
📌 Problem: {user_input}
✅ Solution: {solution_text}
────────────────────────────────────────────

🎬 Animation Instructions:
+ Represent variables (e.g., x, y) as labeled 3D boxes or spheres.
+ Use ➕ ➖ ✖️ ➗ symbols as animated arrows between objects.
+ Show constants (e.g., 3, 5) as floating number blocks.
+ Animate each algebraic operation step-by-step:
    - Highlight the current operation with glowing symbols.
    - Fade in/out objects as they are simplified or eliminated.
+ Use a clean whiteboard or classroom background.
+ Emphasize solving for the unknown (e.g., isolate x).
+ Include visual cues for equality (=) and balance (e.g., scales or mirrored layout).
+ Use motion to show transformation: move, scale, fade, rotate.

📦 Assets to consider:
+ VariableBox(x), ConstantBlock(3), OperationArrow(➕), EqualsBar(=)
+ Background: ClassroomScene or WhiteboardGrid

🧠 Goal:
Make the animation intuitive for middle/high school students. Each step should match the algebraic logic and help learners understand the transformation from problem to solution.

🛑 Do not include any Markdown formatting like ```python or ``` in the output.

# Respond with:
# 1. 🎞️ A step-by-step animation plan
# 2. 🧱 Asset suggestions
# 3. ⏱️ Timing and transitions

"""


def build_blender_prompt(markdown_plan: str) -> str:
    return f"""
You are a Blender 4.4.3+ animation expert.

Convert the following Markdown animation plan into a Python script using bpy.

{markdown_plan}

Requirements:
+ Output only the raw Python script — no Markdown formatting like ```python or ```
+ Ensure compatibility with Blender 4.4.3+ APIs
+ Avoid deprecated or context-sensitive calls (e.g., bpy.context.active_object)
+ Explicitly select and activate objects before modifying them:
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
+ Add all objects to the correct collection and ensure visibility in viewport and render
+ Use semantic animation cues (fade, slide, highlight)
+ Use real-world assets where appropriate
+ Ensure the script runs without errors in Blender's scripting editor
"""
