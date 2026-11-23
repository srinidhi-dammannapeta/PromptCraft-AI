
from utils.content_generator import client


def generate_prompt_response(technique, task, example=""):

    # Zero-Shot Prompting
    if technique == "Zero-Shot":
        prompt = f"""
        Perform the following task without using examples.

        Task: {task}

        Provide a clear and relevant response.
        """

    # One-Shot Prompting
    elif technique == "One-Shot":
        prompt = f"""
        Follow the given example to understand the expected output.

        Example:
        {example}

        Now perform this task:
        {task}
        """

    # Few-Shot Prompting
    elif technique == "Few-Shot":
        prompt = f"""
        Study the following examples and identify their pattern.

        Examples:
        {example}

        Now perform the following task using the same pattern:
        {task}
        """

    # Role-Based Prompting
    elif technique == "Role-Based":
        prompt = f"""
        Act as an experienced subject matter expert.

        Task:
        {task}

        Provide an accurate, professional and useful response.
        """

    # Structured Prompting
    elif technique == "Structured":
        prompt = f"""
        Complete the following task using a structured format.

        Task:
        {task}

        Organize your response using:
        1. Introduction
        2. Main Points
        3. Explanation
        4. Conclusion

        Use clear headings and meaningful language.
        """

    else:
        raise ValueError("Invalid prompting technique selected.")

    # Send the prompt to Gemini
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return prompt, response.text
