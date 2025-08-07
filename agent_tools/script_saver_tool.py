# this tool ensures that the script is saved correctly
import os
from dotenv import load_dotenv
load_dotenv()

def save_blender_script(script:str, filename:str, folder_name:str="blender_scripts") -> str:
    """
    Save the Blender script to a file.
    Args:
        script (str): The Blender script to save.
        filename (str): The name of the file to save the script as.
        folder_name (str): The name of the folder to save the script in.
    Returns:
        str: The path to the saved script file.
    """
    # Create the folder if it doesn't exist
    os.makedirs(folder_name, exist_ok=True)

    # Save the script to a file
    file_path = os.path.join(folder_name, filename)
    with open(file_path, "w") as f:
        f.write(script)

    return file_path