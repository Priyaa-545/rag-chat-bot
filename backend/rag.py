from backend.llm import get_llm
from backend.vectorstore import get_vectorstore


def retrieve_relevant_chunks(query, chat_id, k=3):
    vectorstore = get_vectorstore()

    results = vectorstore.similarity_search(
        query,
        k=k,
        filter={"chat_id": chat_id}
    )

    return results


def generate_answer(query, chat_id):
    results = retrieve_relevant_chunks(query, chat_id)

    if not results:
        return "No relevant information found in this chat's PDFs. Please upload a PDF first."

    context = "\n\n".join(
        [result.page_content for result in results]
    )

    llm = get_llm()

    prompt = f"""
    You are a helpful AI assistant.
    Answer the question using only the provided context.
    If the answer is not available in the context,
    clearly say that the uploaded PDFs do not contain the answer.

    Context:
    {context}

    Question:
    {query}

    Answer:
    """

    response = llm.invoke(prompt)

    return response.text