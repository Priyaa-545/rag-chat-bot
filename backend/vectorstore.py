import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "pdf_documents"


def get_embeddings():
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file")

    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key
    )


def get_vectorstore():
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_PATH,
        embedding_function=get_embeddings()
    )


def create_vectorstore(chunks, chat_id, document_id):
    vectorstore = get_vectorstore()

    for chunk in chunks:
        chunk.metadata["chat_id"] = chat_id
        chunk.metadata["document_id"] = document_id

    vectorstore.add_documents(chunks)

    return vectorstore


def delete_document(chat_id, document_id):
    vectorstore = get_vectorstore()

    vectorstore.delete(
        where={
            "$and": [
                {"chat_id": chat_id},
                {"document_id": document_id}
            ]
        }
    )


def delete_chat_documents(chat_id):
    vectorstore = get_vectorstore()

    vectorstore.delete(
        where={"chat_id": chat_id}
    )