import sys

# SQLite fix for Streamlit Cloud (Linux only) — skip on Windows
if sys.platform != "win32":
    try:
        __import__('pysqlite3')
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    except ImportError:
        pass

import streamlit as st
from services import ingest_file, retrieve_relevant_chunks, generate_answer, clear_collection
from utils import save_uploaded_file, delete_file

# ── Page config ───────────────────────────────────────────
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI Study Assistant")
st.caption("Upload your notes → Ask anything  |  Powered by Groq 🚀")

# ── Session state ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "notes_loaded" not in st.session_state:
    st.session_state.notes_loaded = False

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.header("📂 Upload Notes")

    uploaded_file = st.file_uploader(
        "Choose a PDF or TXT file",
        type=["pdf", "txt"]
    )

    if uploaded_file:
        if st.button("⚡ Process File", type="primary", use_container_width=True):
            with st.spinner("Reading and indexing your notes..."):
                try:
                    file_path = save_uploaded_file(uploaded_file)
                    num_chunks = ingest_file(file_path)
                    delete_file(file_path)
                    st.session_state.notes_loaded = True
                    st.success(f"✅ Done! Indexed {num_chunks} chunks.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    st.divider()

    if st.session_state.notes_loaded:
        st.success("✅ Notes loaded. Ask away!")
        if st.button("🗑️ Clear Notes", use_container_width=True):
            clear_collection()
            st.session_state.notes_loaded = False
            st.session_state.messages = []
            st.rerun()
    else:
        st.info("⬆️ Upload a file to get started.")

    if st.button("🧹 Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("Built with Streamlit + Groq + ChromaDB")

# ── Chat history ──────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ── Chat input ────────────────────────────────────────────
if question := st.chat_input("Ask a question about your notes..."):
    if not st.session_state.notes_loaded:
        st.error("⚠️ Please upload and process a file first!")
    else:
        # Show user message
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        # Get and show answer
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    chunks = retrieve_relevant_chunks(question)
                    answer = generate_answer(question, chunks)
                except Exception as e:
                    answer = f"❌ Something went wrong: {e}"
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})