from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.vectorstore import create_vectorstore


def extract_text_from_pdf(pdf_path):
    loader = PyPDFLoader(pdf_path)
    return loader.load()


def split_text_into_chunks(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    return text_splitter.split_documents(documents)


def process_pdf(pdf_path, chat_id, document_id):
    documents = extract_text_from_pdf(pdf_path)

    chunks = split_text_into_chunks(documents)

    if not chunks:
        raise ValueError("No readable text found in PDF.")

    create_vectorstore(
        chunks,
        chat_id=chat_id,
        document_id=document_id
    )

    return {
        "total_pages": len(documents),
        "total_chunks": len(chunks)
    }