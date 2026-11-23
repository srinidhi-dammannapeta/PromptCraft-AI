
from utils.content_generator import client


def generate_code(task, language, difficulty):

    prompt = f"""
    Act as an expert software developer and programming instructor.

    Generate a solution for the following programming task.

    Programming Task:
    {task}

    Programming Language:
    {language}

    Difficulty Level:
    {difficulty}

    Requirements:
    1. Generate correct and readable code.
    2. Follow proper programming practices.
    3. Use meaningful variable and function names.
    4. Include comments wherever necessary.
    5. Explain how the code works.
    6. Mention the expected output if applicable.
    7. Do not include unnecessary code.

    Format your response using these headings:
    1. Generated Code
    2. Code Explanation
    3. Expected Output
    """

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text
