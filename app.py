import sys

# SQLite fix for Streamlit Cloud (Linux only)
if sys.platform != "win32":
    try:
        __import__('pysqlite3')
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    except ImportError:
        pass

import streamlit as st
from services import ingest_file, retrieve_relevant_chunks, generate_answer, clear_collection
from utils import save_uploaded_file, delete_file

st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI Study Assistant")
st.caption("Upload notes or images → Ask anything  |  Powered by Groq 🚀")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "notes_loaded" not in st.session_state:
    st.session_state.notes_loaded = False

with st.sidebar:
    st.header("📂 Upload Notes")

    uploaded_file = st.file_uploader(
        "PDF, TXT or Image (JPG, PNG...)",
        # ← image types added here
        type=["pdf", "txt", "png", "jpg", "jpeg", "bmp", "tiff", "webp"]
    )

    if uploaded_file:
        # Show file type detected so user knows OCR will run
        ext = uploaded_file.name.split(".")[-1].upper()
        if ext in ["PNG", "JPG", "JPEG", "BMP", "TIFF", "WEBP"]:
            st.info(f"🖼️ Image detected ({ext}) — OCR will extract text")
        else:
            st.info(f"📄 Document detected ({ext})")

        if st.button("⚡ Process File", type="primary", use_container_width=True):
            with st.spinner("Reading and indexing your notes..."):
                try:
                    file_path = save_uploaded_file(uploaded_file)
                    num_chunks = ingest_file(file_path)
                    delete_file(file_path)
                    st.session_state.notes_loaded = True
                    st.success(f"✅ Done! Indexed {num_chunks} chunks.")
                except RuntimeError as e:
                    st.error(f"❌ Runtime Error: {e}")
                except ValueError as e:
                    st.error(f"❌ Value Error: {e}")
                except Exception as e:
                    st.error(f"❌ Unexpected Error: {type(e).__name__}: {e}")

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
    st.caption("Built with Streamlit + Groq + ChromaDB + EasyOCR")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if question := st.chat_input("Ask a question about your notes..."):
    if not st.session_state.notes_loaded:
        st.error("⚠️ Please upload and process a file first!")
    else:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    chunks = retrieve_relevant_chunks(question)
                    answer = generate_answer(question, chunks)
                except Exception as e:
                    answer = f"❌ Something went wrong: {e}"
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})