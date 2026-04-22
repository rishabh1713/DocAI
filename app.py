import sys
import os

# SQLite fix for Streamlit Cloud (Linux only)
if sys.platform != "win32":
    try:
        __import__('pysqlite3')
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    except ImportError:
        pass

import fitz
import streamlit as st
from services import ingest_file, retrieve_relevant_chunks, generate_answer, clear_collection
from utils import save_uploaded_file, delete_file

os.makedirs("uploads", exist_ok=True)

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
        type=["pdf", "txt", "png", "jpg", "jpeg", "bmp", "tiff", "webp"]
    )

    if uploaded_file:
        ext = uploaded_file.name.split(".")[-1].upper()
        if ext in ["PNG", "JPG", "JPEG", "BMP", "TIFF", "WEBP"]:
            st.info(f"🖼️ Image detected ({ext}) — OCR will extract text")
        else:
            st.info(f"📄 Document detected ({ext})")

        if st.button("⚡ Process File", type="primary", use_container_width=True):
            progress_bar = st.progress(0, text="Starting...")
            status_text = st.empty()   # ← this shows detailed status below bar

            def update_progress(percent: int, message: str):
                # Top bar shows percent + page info
                progress_bar.progress(percent, text=message)
                # Bottom text shows what's actually happening right now
                if percent < 20:
                    status_text.info("📂 Saving your file...")
                elif percent < 50:
                    status_text.info("🔍 Extracting text from pages...")
                elif percent < 70:
                    status_text.info("🤖 Running OCR on image pages...")
                elif percent < 90:
                    status_text.info("🗄️ Indexing into vector database...")
                elif percent < 100:
                    status_text.info("🧹 Cleaning up temp files...")
                else:
                    status_text.success("✅ All done!")

            try:
                update_progress(5, "Starting...")
                file_path = save_uploaded_file(uploaded_file)

                if ext == "PDF":
                    temp_pdf = fitz.open(file_path)
                    total_pages = len(temp_pdf)
                    temp_pdf.close()

                    if total_pages > 50:
                        st.warning(
                            f"⏳ Large PDF detected ({total_pages} pages). "
                            f"This may take {total_pages // 20}–{total_pages // 10} "
                            f"minutes. Please keep this tab open."
                        )

                    update_progress(10, f"Reading {total_pages} pages...")
                    num_chunks = ingest_file(
                        file_path,
                        progress_callback=update_progress
                    )

                    update_progress(95, "Almost done...")
                    delete_file(file_path)

                    progress_bar.progress(100, text="Complete!")
                    status_text.empty()
                    st.session_state.notes_loaded = True
                    st.success(
                        f"✅ Done! Processed {total_pages} pages "
                        f"→ {num_chunks} chunks indexed."
                    )
                    progress_bar.empty()

                else:
                    update_progress(30, "Extracting content...")
                    num_chunks = ingest_file(
                        file_path,
                        progress_callback=update_progress
                    )

                    update_progress(95, "Almost done...")
                    delete_file(file_path)

                    progress_bar.progress(100, text="Complete!")
                    status_text.empty()
                    st.session_state.notes_loaded = True
                    st.success(f"✅ Done! Indexed {num_chunks} chunks.")
                    progress_bar.empty()

            except RuntimeError as e:
                st.error(f"❌ Runtime Error: {e}")
                progress_bar.empty()
                status_text.empty()
            except ValueError as e:
                st.error(f"❌ Value Error: {e}")
                progress_bar.empty()
                status_text.empty()
            except Exception as e:
                st.error(f"❌ Unexpected Error: {type(e).__name__}: {e}")
                progress_bar.empty()
                status_text.empty()

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

# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ── Chat input ────────────────────────────────────────────────────────────────
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
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )