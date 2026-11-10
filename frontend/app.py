
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="PDF Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state
if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False

if "active_section" not in st.session_state:
    st.session_state.active_section = "New Chat"


def create_new_chat():
    response = requests.post(
        f"{API_URL}/chats",
        timeout=30
    )
    response.raise_for_status()

    st.session_state.chat_id = response.json()["chat_id"]
    st.session_state.messages = []
    st.session_state.uploaded_files = []
    st.session_state.pdf_processed = False
    st.session_state.active_section = "New Chat"


# Create the first chat automatically
if st.session_state.chat_id is None:
    create_new_chat()

# Dark theme styling
st.markdown("""
<style>
.stApp {
    background-color: #171717;
    color: #ffffff;
}

[data-testid="stSidebar"] {
    background-color: #101010;
    border-right: 1px solid #303030;
}

[data-testid="stSidebar"] * {
    color: #eeeeee;
}

.main .block-container {
    max-width: 1000px;
    padding-top: 2rem;
    padding-bottom: 7rem;
}

.stChatMessage {
    background-color: #242424;
    border-radius: 14px;
    border: 1px solid #333333;
    padding: 15px;
}

.stChatInput textarea {
    background-color: #292929 !important;
    color: white !important;
}

.stButton button {
    background-color: #292929;
    color: white;
    border: 1px solid #444444;
    border-radius: 10px;
}

.stButton button:hover {
    background-color: #3a3a3a;
    color: white;
    border-color: #777777;
}

h1, h2, h3, p, label {
    color: #eeeeee;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("📚 PDF Assistant")
    st.caption("Your personal document AI")

    st.divider()

    if st.button("＋ New Chat", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.subheader("Workspace")

    if st.button("💬 Chat History", use_container_width=True):
        st.session_state.active_section = "Chat History"
        st.rerun()

    if st.button("📄 My Documents", use_container_width=True):
        st.session_state.active_section = "My Documents"
        st.rerun()

    if st.button("⚙️ Settings", use_container_width=True):
        st.session_state.active_section = "Settings"
        st.rerun()

    st.divider()

    st.subheader("Upload PDFs")

    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files and st.button("Process PDFs", use_container_width=True):
        try:
            files = [
                ("files", (file.name, file.getvalue(), "application/pdf"))
                for file in uploaded_files
            ]

            with st.spinner("Processing PDFs..."):
                response = requests.post(
                    f"{API_URL}/upload-pdfs",
                    data={"chat_id": st.session_state.chat_id},
                    files=files,
                    timeout=300
                )
                response.raise_for_status()
                result = response.json()

            st.session_state.pdf_processed = True
            st.session_state.uploaded_files = [
                item["filename"] for item in result["files"]
            ]

            st.success("PDFs processed successfully!")
            st.rerun()

        except requests.exceptions.RequestException as e:
            st.error(f"Upload failed: {e}")

    st.divider()
    st.caption("Powered by Gemini AI")

# Main content
if st.session_state.active_section == "New Chat":
    st.title("PDF Assistant")
    st.caption("Ask questions and get answers from your uploaded documents.")

    if not st.session_state.messages:
        st.markdown(
            "<div style='text-align:center; padding:70px 10px;'>"
            "<h2>How can I help you today?</h2>"
            "<p style='color:#999;'>Upload a PDF and start asking questions.</p>"
            "</div>",
            unsafe_allow_html=True
        )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if not st.session_state.pdf_processed:
        st.info("Upload and process a PDF from the sidebar to start chatting.")
    else:
        question = st.chat_input("Ask anything about your PDFs...")

        if question:
            with st.chat_message("user"):
                st.markdown(question)

            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        f"{API_URL}/ask",
                        json={
                            "question": question,
                            "chat_id": st.session_state.chat_id
                        },
                        timeout=120
                    )
                    response.raise_for_status()
                    answer = response.json()["answer"]

                    st.session_state.messages.append(
                        {"role": "user", "content": question}
                    )
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )
                    st.rerun()

                except requests.exceptions.RequestException as e:
                    st.error(f"Backend connection error: {e}")

elif st.session_state.active_section == "Chat History":
    st.title("💬 Chat History")

    try:
        response = requests.get(
            f"{API_URL}/chats",
            timeout=30
        )
        response.raise_for_status()

        chats = response.json()["chats"]

        if not chats:
            st.info("No conversations yet.")
        else:
            for chat in chats:
                chat_title = chat.get("title", "New Chat")
                chat_id = chat["chat_id"]

                if st.button(
                    f"💬 {chat_title}",
                    key=f"chat_{chat_id}",
                    use_container_width=True
                ):
                    st.session_state.chat_id = chat_id

                    messages_response = requests.get(
                        f"{API_URL}/chats/{chat_id}/messages",
                        timeout=30
                    )
                    messages_response.raise_for_status()

                    st.session_state.messages = (
                        messages_response.json()["messages"]
                    )

                    documents_response = requests.get(
                        f"{API_URL}/chats/{chat_id}/documents",
                        timeout=30
                    )
                    documents_response.raise_for_status()

                    documents = documents_response.json()["documents"]

                    st.session_state.uploaded_files = [
                        doc["filename"] for doc in documents
                    ]

                    st.session_state.pdf_processed = bool(documents)
                    st.session_state.active_section = "New Chat"
                    st.rerun()

    except requests.exceptions.RequestException as e:
        st.error(f"Could not load chat history: {e}")

elif st.session_state.active_section == "My Documents":
    st.title("📄 My Documents")

    if st.session_state.uploaded_files:
        for filename in st.session_state.uploaded_files:
            st.write(f"📄 {filename}")
    else:
        st.info("No documents uploaded in this session yet.")

elif st.session_state.active_section == "Settings":
    st.title("⚙️ Settings")
    st.write("PDF Assistant settings")
    st.caption("More preferences can be added here later.")
