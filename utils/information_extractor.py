
from utils.content_generator import client


def extract_information(text):
    prompt = f"""
    Act as an intelligent information extraction system.

    Analyze the following text and extract the information
    under these headings:

    1. Main Topic
       Identify the central subject of the text.

    2. Summary
       Provide a short and meaningful summary.

    3. Important Keywords
       List the most relevant keywords and phrases.

    4. Named Entities
       Identify the following wherever available:
       - Person Names
       - Organizations
       - Locations
       - Dates
       - Important Numbers

    5. Key Points
       List the most important information in bullet points.

    Instructions:
    - Use only information present in the given text.
    - Do not invent or assume missing information.
    - If any information is unavailable, mention "Not found".
    - Organize the output using clear headings.

    Text to analyze:
    {text}
    """

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text
