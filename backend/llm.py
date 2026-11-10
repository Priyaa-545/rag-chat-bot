import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()


# Function to initialize Gemini
def get_llm():

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file")

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        temperature=0.3,
        google_api_key=api_key
    )

    return llm


# Test Gemini connection
if __name__ == "__main__":

    llm = get_llm()

    response = llm.invoke(
        "Explain Retrieval Augmented Generation in two sentences."
    )

    print(response.content)