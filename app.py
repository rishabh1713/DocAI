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

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* Global font */
html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
}

/* Hide default streamlit header */
#MainMenu, footer, header { visibility: hidden; }

/* Main background */
.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.04);
    border-right: 1px solid rgba(255,255,255,0.08);
    backdrop-filter: blur(20px);
}

/* Title area */
.main-title {
    font-family: 'Sora', sans-serif;
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.2rem;
    animation: shimmer 3s ease-in-out infinite;
    background-size: 200% auto;
}

@keyframes shimmer {
    0% { background-position: 0% center; }
    50% { background-position: 100% center; }
    100% { background-position: 0% center; }
}

.subtitle {
    color: rgba(255,255,255,0.45);
    font-size: 0.95rem;
    font-weight: 300;
    letter-spacing: 0.05em;
    margin-bottom: 2rem;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(10px);
    margin-bottom: 1rem;
    padding: 0.5rem;
}

/* User message accent */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    border-left: 3px solid #a78bfa !important;
    background: rgba(167,139,250,0.06) !important;
}

/* Assistant message accent */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    border-left: 3px solid #34d399 !important;
    background: rgba(52,211,153,0.04) !important;
}

/* Chat input */
[data-testid="stChatInput"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 16px !important;
    color: white !important;
}

/* Buttons */
.stButton > button {
    border-radius: 12px !important;
    font-family: 'Sora', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(167,139,250,0.3) !important;
}

/* Suggestion chips */
.chip-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 1.5rem 0;
}

.chip {
    background: rgba(167,139,250,0.12);
    border: 1px solid rgba(167,139,250,0.3);
    border-radius: 50px;
    padding: 0.4rem 1rem;
    font-size: 0.82rem;
    color: #c4b5fd;
    cursor: pointer;
    transition: all 0.2s;
    font-family: 'Sora', sans-serif;
    white-space: nowrap;
}

.chip:hover {
    background: rgba(167,139,250,0.25);
    transform: translateY(-1px);
}

/* Welcome card */
.welcome-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 2.5rem;
    text-align: center;
    margin: 3rem auto;
    max-width: 600px;
    backdrop-filter: blur(10px);
}

.welcome-icon {
    font-size: 3.5rem;
    margin-bottom: 1rem;
}

.welcome-title {
    color: rgba(255,255,255,0.9);
    font-size: 1.4rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.welcome-text {
    color: rgba(255,255,255,0.45);
    font-size: 0.9rem;
    line-height: 1.7;
}

/* Steps */
.steps-row {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
    justify-content: center;
    flex-wrap: wrap;
}

.step {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 0.8rem 1.2rem;
    font-size: 0.82rem;
    color: rgba(255,255,255,0.6);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.step-num {
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    border-radius: 50%;
    width: 22px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 700;
    color: white;
    flex-shrink: 0;
}

/* Stats bar */
.stats-bar {
    display: flex;
    gap: 1.5rem;
    padding: 1rem 1.5rem;
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 1.5rem;
}

.stat-item {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}

.stat-label {
    font-size: 0.72rem;
    color: rgba(255,255,255,0.35);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.stat-value {
    font-size: 1.1rem;
    font-weight: 600;
    color: #a78bfa;
    font-family: 'JetBrains Mono', monospace;
}

/* Progress bar */
.stProgress > div > div {
    background: linear-gradient(90deg, #a78bfa, #60a5fa) !important;
    border-radius: 10px !important;
}

/* Sidebar text */
[data-testid="stSidebar"] * {
    color: rgba(255,255,255,0.8) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.03) !important;
    border: 2px dashed rgba(167,139,250,0.3) !important;
    border-radius: 16px !important;
    transition: all 0.2s;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(167,139,250,0.6) !important;
    background: rgba(167,139,250,0.06) !important;
}

/* Success/info/warning colors */
.stSuccess {
    background: rgba(52,211,153,0.1) !important;
    border: 1px solid rgba(52,211,153,0.3) !important;
    border-radius: 12px !important;
}

.stInfo {
    background: rgba(96,165,250,0.1) !important;
    border: 1px solid rgba(96,165,250,0.3) !important;
    border-radius: 12px !important;
}

/* Divider */
hr {
    border-color: rgba(255,255,255,0.08) !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(167,139,250,0.3);
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "notes_loaded" not in st.session_state:
    st.session_state.notes_loaded = False
if "total_pages" not in st.session_state:
    st.session_state.total_pages = 0
if "total_chunks" not in st.session_state:
    st.session_state.total_chunks = 0
if "file_name" not in st.session_state:
    st.session_state.file_name = ""
if "suggested_question" not in st.session_state:
    st.session_state.suggested_question = ""

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Upload Notes")

    uploaded_file = st.file_uploader(
        "PDF, TXT or Image",
        type=["pdf", "txt", "png", "jpg", "jpeg", "bmp", "tiff", "webp"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        ext = uploaded_file.name.split(".")[-1].upper()
        if ext in ["PNG", "JPG", "JPEG", "BMP", "TIFF", "WEBP"]:
            st.info(f"🖼️ Image detected — OCR ready")
        else:
            st.info(f"📄 {uploaded_file.name}")

        if st.button("⚡ Process File", type="primary", use_container_width=True):
            progress_bar = st.progress(0, text="Starting...")
            status_text = st.empty()

            def update_progress(percent: int, message: str):
                progress_bar.progress(percent, text=message)
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
                            f"⏳ Large PDF ({total_pages} pages). "
                            f"Est. {total_pages // 20}–{total_pages // 10} min."
                        )

                    update_progress(10, f"Reading {total_pages} pages...")
                    num_chunks = ingest_file(file_path, progress_callback=update_progress)
                    st.session_state.total_pages = total_pages

                else:
                    total_pages = 1
                    update_progress(30, "Extracting content...")
                    num_chunks = ingest_file(file_path, progress_callback=update_progress)
                    st.session_state.total_pages = 1

                update_progress(95, "Almost done...")
                delete_file(file_path)

                progress_bar.progress(100, text="Complete!")
                status_text.empty()

                st.session_state.notes_loaded = True
                st.session_state.total_chunks = num_chunks
                st.session_state.file_name = uploaded_file.name

                st.success(f"✅ Ready! {num_chunks} chunks indexed.")
                progress_bar.empty()

            except RuntimeError as e:
                st.error(f"❌ {e}")
                progress_bar.empty()
                status_text.empty()
            except ValueError as e:
                st.error(f"❌ {e}")
                progress_bar.empty()
                status_text.empty()
            except Exception as e:
                st.error(f"❌ {type(e).__name__}: {e}")
                progress_bar.empty()
                status_text.empty()

    st.divider()

    if st.session_state.notes_loaded:
        st.markdown(f"""
        <div style='background:rgba(52,211,153,0.08);border:1px solid rgba(52,211,153,0.2);
        border-radius:12px;padding:0.8rem 1rem;margin-bottom:0.8rem;'>
            <div style='font-size:0.75rem;color:rgba(255,255,255,0.4);margin-bottom:0.3rem;'>ACTIVE FILE</div>
            <div style='font-size:0.85rem;color:rgba(255,255,255,0.85);font-weight:600;
            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>
                📄 {st.session_state.file_name}
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style='background:rgba(255,255,255,0.04);border-radius:10px;
            padding:0.6rem;text-align:center;'>
                <div style='font-size:1.3rem;font-weight:700;color:#a78bfa;
                font-family:monospace;'>{st.session_state.total_pages}</div>
                <div style='font-size:0.65rem;color:rgba(255,255,255,0.35);'>PAGES</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style='background:rgba(255,255,255,0.04);border-radius:10px;
            padding:0.6rem;text-align:center;'>
                <div style='font-size:1.3rem;font-weight:700;color:#60a5fa;
                font-family:monospace;'>{st.session_state.total_chunks}</div>
                <div style='font-size:0.65rem;color:rgba(255,255,255,0.35);'>CHUNKS</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🗑️ Clear Notes", use_container_width=True):
            clear_collection()
            st.session_state.notes_loaded = False
            st.session_state.messages = []
            st.session_state.total_pages = 0
            st.session_state.total_chunks = 0
            st.session_state.file_name = ""
            st.rerun()
    else:
        st.markdown("""
        <div style='color:rgba(255,255,255,0.35);font-size:0.82rem;line-height:1.7;'>
        ⬆️ Upload a file to get started.<br><br>
        Supports PDF, images (JPG, PNG) and text files.
        </div>
        """, unsafe_allow_html=True)

    if st.button("🧹 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("""
    <div style='font-size:0.7rem;color:rgba(255,255,255,0.2);line-height:1.8;'>
    Powered by<br>
    🟣 Groq · LLaMA3<br>
    🔵 ChromaDB<br>
    🟢 EasyOCR · PyMuPDF
    </div>
    """, unsafe_allow_html=True)

# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">📚 AI Study Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ask anything from your notes — or just chat</div>', unsafe_allow_html=True)

# ── Welcome screen (shown when no chat yet) ───────────────────────────────────
if not st.session_state.messages:
    if not st.session_state.notes_loaded:
        st.markdown("""
        <div class="welcome-card">
            <div class="welcome-icon">🎓</div>
            <div class="welcome-title">Welcome to your AI Study Assistant</div>
            <div class="welcome-text">
                Upload your notes, textbooks, or images and ask anything.<br>
                Powered by Groq's LLaMA3 for lightning-fast answers.
            </div>
            <div class="steps-row">
                <div class="step">
                    <div class="step-num">1</div>
                    Upload a PDF or image
                </div>
                <div class="step">
                    <div class="step-num">2</div>
                    Click Process File
                </div>
                <div class="step">
                    <div class="step-num">3</div>
                    Ask your question
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        # Notes loaded but no chat yet — show suggestions
        st.markdown(f"""
        <div class="welcome-card">
            <div class="welcome-icon">✅</div>
            <div class="welcome-title">Notes loaded! Start asking questions.</div>
            <div class="welcome-text">
                <b style="color:#a78bfa">{st.session_state.file_name}</b> is ready.<br>
                {st.session_state.total_pages} pages · {st.session_state.total_chunks} chunks indexed
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**💡 Try asking:**")
        suggestions = [
            "📝 Summarize the main topics",
            "🔑 What are the key concepts?",
            "❓ Create 5 quiz questions",
            "📊 Explain the most complex part",
            "🔍 What is this document about?",
            "💡 Give me study tips for this"
        ]

        cols = st.columns(3)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 3]:
                if st.button(suggestion, use_container_width=True, key=f"sug_{i}"):
                    st.session_state.suggested_question = suggestion
                    st.rerun()

# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Handle suggested question click ──────────────────────────────────────────
if st.session_state.suggested_question:
    question = st.session_state.suggested_question
    st.session_state.suggested_question = ""

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                chunks = retrieve_relevant_chunks(question)
                answer = generate_answer(question, chunks)
            except Exception as e:
                answer = f"❌ Something went wrong: {e}"
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────────
if question := st.chat_input("Ask about your notes, or anything at all..."):

    # ── Smart router: is this about the notes or a general question? ──────────
    NOTE_KEYWORDS = [
        "summarize", "explain", "what is", "what are", "define",
        "chapter", "topic", "concept", "notes", "document", "pdf",
        "page", "according to", "mention", "describe", "list",
        "example", "difference", "compare", "how does", "why does"
    ]

    is_about_notes = (
        st.session_state.notes_loaded and
        any(kw in question.lower() for kw in NOTE_KEYWORDS)
    )

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if is_about_notes:
                    # Answer from the uploaded notes
                    chunks = retrieve_relevant_chunks(question)
                    answer = generate_answer(question, chunks)

                elif not st.session_state.notes_loaded:
                    # No notes uploaded — answer from general knowledge
                    from groq import Groq
                    from config.settings import GROQ_API_KEY
                    groq_client = Groq(api_key=GROQ_API_KEY)
                    response = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        temperature=0.7,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are a friendly, enthusiastic study assistant. "
                                    "Answer questions in a helpful, engaging, and creative way. "
                                    "Use examples, analogies, and clear structure. "
                                    "Format your answers with markdown — use **bold**, bullet points, "
                                    "and headers where helpful. Keep it educational but fun."
                                )
                            },
                            {"role": "user", "content": question}
                        ]
                    )
                    answer = response.choices[0].message.content

                else:
                    # Notes loaded but question seems general — try notes first,
                    # fall back to general knowledge
                    try:
                        chunks = retrieve_relevant_chunks(question)
                        # Check if retrieved chunks are actually relevant
                        if chunks and len(chunks[0]) > 50:
                            answer = generate_answer(question, chunks)
                        else:
                            raise ValueError("Not enough context in notes")
                    except Exception:
                        from groq import Groq
                        from config.settings import GROQ_API_KEY
                        groq_client = Groq(api_key=GROQ_API_KEY)
                        response = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            temperature=0.7,
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "You are a friendly, enthusiastic study assistant. "
                                        "Answer questions helpfully and creatively. "
                                        "Use markdown formatting with **bold**, bullet points, "
                                        "and headers. Keep answers educational but engaging."
                                    )
                                },
                                {"role": "user", "content": question}
                            ]
                        )
                        answer = response.choices[0].message.content
                        answer = f"*(Answering from general knowledge)*\n\n{answer}"

            except Exception as e:
                answer = f"❌ Something went wrong: {e}"

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})