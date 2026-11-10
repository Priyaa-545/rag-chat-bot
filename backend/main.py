
import os
import shutil
import tempfile
import traceback
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from pydantic import BaseModel

from backend.pdf_processor import process_pdf
from backend.rag import generate_answer
from backend.vectorstore import delete_document, delete_chat_documents

from backend.database import (
    init_db,
    create_chat as save_chat,
    get_all_chats,
    get_chat,
    save_document,
    get_chat_documents,
    delete_document_record,
    delete_chat_record,
    save_message,
    get_chat_messages,
    update_chat_title
)


app = FastAPI(title="PDF RAG Chatbot")

# Initialize database
init_db()


class QuestionRequest(BaseModel):
    question: str
    chat_id: str


@app.get("/")
def home():
    return {"message": "PDF RAG Chatbot API is running"}


# 1. Create a new chat
@app.post("/chats")
def create_new_chat():

    chat_id = str(uuid.uuid4())

    save_chat(chat_id)

    return {
        "message": "New chat created successfully!",
        "chat_id": chat_id
    }


# 2. Get all chats
@app.get("/chats")
def list_chats():

    return {
        "chats": get_all_chats()
    }


# 3. Get messages of a particular chat
@app.get("/chats/{chat_id}/messages")
def get_messages(chat_id: str):

    if not get_chat(chat_id):
        raise HTTPException(
            status_code=404,
            detail="Chat not found."
        )

    return {
        "messages": get_chat_messages(chat_id)
    }


# 4. Get documents of a particular chat
@app.get("/chats/{chat_id}/documents")
def list_documents(chat_id: str):

    if not get_chat(chat_id):
        raise HTTPException(
            status_code=404,
            detail="Chat not found."
        )

    return {
        "documents": get_chat_documents(chat_id)
    }


# 5. Upload PDFs
@app.post("/upload-pdfs")
async def upload_pdfs(
    chat_id: str = Form(...),
    files: list[UploadFile] = File(...)
):

    if not get_chat(chat_id):
        raise HTTPException(
            status_code=404,
            detail="Chat not found."
        )

    if not files:
        raise HTTPException(
            status_code=400,
            detail="Please upload at least one PDF."
        )

    results = []

    for file in files:

        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed."
            )

        temp_path = None
        document_id = str(uuid.uuid4())

        try:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as temp_file:

                shutil.copyfileobj(file.file, temp_file)
                temp_path = temp_file.name

            result = process_pdf(
                temp_path,
                chat_id=chat_id,
                document_id=document_id
            )

            # Save document information in SQLite
            save_document(
                document_id=document_id,
                chat_id=chat_id,
                filename=file.filename,
                pages=result["total_pages"],
                chunks=result["total_chunks"]
            )

            results.append({
                "document_id": document_id,
                "filename": file.filename,
                "pages": result["total_pages"],
                "chunks": result["total_chunks"]
            })

        except Exception as e:

            traceback.print_exc()

            raise HTTPException(
                status_code=500,
                detail=f"Error processing {file.filename}: {str(e)}"
            )

        finally:

            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

            await file.close()

    return {
        "message": "PDFs processed successfully!",
        "files": results
    }


# 6. Delete one PDF
@app.delete("/chats/{chat_id}/documents/{document_id}")
def remove_document(chat_id: str, document_id: str):

    if not get_chat(chat_id):
        raise HTTPException(
            status_code=404,
            detail="Chat not found."
        )

    documents = get_chat_documents(chat_id)

    if not any(doc["document_id"] == document_id for doc in documents):
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    try:

        delete_document(chat_id, document_id)

        delete_document_record(
            chat_id,
            document_id
        )

        return {
            "message": "Document deleted successfully!"
        }

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# 7. Delete an entire chat
@app.delete("/chats/{chat_id}")
def remove_chat(chat_id: str):

    if not get_chat(chat_id):
        raise HTTPException(
            status_code=404,
            detail="Chat not found."
        )

    try:

        delete_chat_documents(chat_id)

        delete_chat_record(chat_id)

        return {
            "message": "Chat and its documents deleted successfully!"
        }

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# 8. Ask a question
@app.post("/ask")
def ask_question(request: QuestionRequest):

    if not get_chat(request.chat_id):
        raise HTTPException(
            status_code=404,
            detail="Chat not found."
        )

    try:

        # Generate answer
        answer = generate_answer(
            request.question,
            request.chat_id
        )

        # Save user question
        save_message(
            request.chat_id,
            "user",
            request.question
        )

        # Save AI response
        save_message(
            request.chat_id,
            "assistant",
            answer
        )

        # Set chat title from the first question
        messages = get_chat_messages(request.chat_id)

        if len(messages) == 2:
            update_chat_title(
                request.chat_id,
                request.question[:40]
            )

        return {
            "answer": answer
        }

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )