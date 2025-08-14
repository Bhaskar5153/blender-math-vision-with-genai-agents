import re

def sanitize_name(text: str) -> str:
    """
    Sanitize a string for use as a Blender object name.
    Replaces unsafe characters and Unicode symbols with semantic equivalents.
    """
    replacements = {
        "±": "pm",
        "√": "sqrt",
        "^": "pow",
        "+": "plus",
        "-": "minus",
        "*": "mul",
        "/": "div",
        "=": "equals",
        "(": "",
        ")": "",
        " ": "_"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove any remaining unsafe characters
    text = re.sub(r"[^\w_]", "", text)
    return text.lower()
