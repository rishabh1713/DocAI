import sys
import os
import base64

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
    page_title="DocAI – Study Assistant",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

dark = st.session_state.dark_mode

if dark:
    bg_main        = "#0d0f1a"
    bg_sidebar     = "#111827"
    bg_card        = "rgba(255,255,255,0.05)"
    border_color   = "rgba(255,255,255,0.12)"
    text_primary   = "#f0f2ff"
    text_secondary = "rgba(240,242,255,0.60)"
    text_muted     = "rgba(240,242,255,0.35)"
    accent1        = "#5b7fff"
    accent2        = "#a78bfa"
    accent3        = "#34d399"
    chip_bg        = "rgba(91,127,255,0.15)"
    chip_border    = "rgba(91,127,255,0.40)"
    chip_text      = "#93b4ff"
    input_bg       = "#1a1f35"
    input_border   = "rgba(91,127,255,0.4)"
    toggle_icon    = "☀️"
    upload_bg      = "#1e2438"
    upload_border  = "rgba(91,127,255,0.5)"
    upload_text    = "#c0ccff"
    sidebar_label  = "#e0e6ff"
    stat_bg        = "#1e2438"
    stat_border    = "rgba(91,127,255,0.25)"
    btn_bg         = "#1e2438"
    btn_border     = "rgba(91,127,255,0.35)"
    btn_text       = "#c0ccff"
    shadow         = "0 4px 24px rgba(0,0,0,0.5)"
    user_border    = "#5b7fff"
    user_bg        = "rgba(91,127,255,0.08)"
    asst_border    = "#34d399"
    asst_bg        = "rgba(52,211,153,0.06)"
    navbar_bg      = "rgba(13,15,26,0.97)"
    wm_opacity     = "0.13"
    welcome_bg     = "rgba(20,24,45,0.92)"
else:
    bg_main        = "#f0f2fa"
    bg_sidebar     = "#ffffff"
    bg_card        = "rgba(255,255,255,0.9)"
    border_color   = "rgba(59,91,219,0.15)"
    text_primary   = "#111827"
    text_secondary = "#374151"
    text_muted     = "#9ca3af"
    accent1        = "#3b5bdb"
    accent2        = "#7c3aed"
    accent3        = "#059669"
    chip_bg        = "rgba(59,91,219,0.08)"
    chip_border    = "rgba(59,91,219,0.25)"
    chip_text      = "#3b5bdb"
    input_bg       = "#ffffff"
    input_border   = "rgba(59,91,219,0.35)"
    toggle_icon    = "🌙"
    upload_bg      = "#f0f4ff"
    upload_border  = "rgba(59,91,219,0.35)"
    upload_text    = "#3b5bdb"
    sidebar_label  = "#111827"
    stat_bg        = "#f0f4ff"
    stat_border    = "rgba(59,91,219,0.2)"
    btn_bg         = "#f0f4ff"
    btn_border     = "rgba(59,91,219,0.25)"
    btn_text       = "#3b5bdb"
    shadow         = "0 4px 16px rgba(59,91,219,0.1)"
    user_border    = "#3b5bdb"
    user_bg        = "rgba(59,91,219,0.05)"
    asst_border    = "#059669"
    asst_bg        = "rgba(5,150,105,0.04)"
    navbar_bg      = "rgba(255,255,255,0.97)"
    wm_opacity     = "0.09"
    welcome_bg     = "rgba(240,242,255,0.92)"

# ── Load logo ─────────────────────────────────────────────────────────────────
logo_b64 = ""
for name in ["logo.png", "logo.jpg", "logo.jpeg"]:
    if os.path.exists(name):
        with open(name, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        break

logo_img_tag = f'<img src="data:image/png;base64,{logo_b64}" style="width:28px;height:28px;border-radius:7px;object-fit:contain;background:white;padding:2px;" />' if logo_b64 else '<div style="width:28px;height:28px;border-radius:7px;background:linear-gradient(135deg,#5b7fff,#a78bfa);display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:800;color:white;">D</div>'

wm_img = f'<img src="data:image/png;base64,{logo_b64}" style="width:100%;height:100%;object-fit:contain;" />' if logo_b64 else ""

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{ font-family: 'Outfit', sans-serif !important; }}
#MainMenu, footer, header {{ visibility: hidden; }}

.stApp {{
    background-color: {bg_main} !important;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background: {bg_sidebar} !important;
    border-right: 1px solid {border_color} !important;
}}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] small {{
    color: {sidebar_label} !important;
}}
[data-testid="stSidebar"] [data-testid="stFileUploader"] {{
    background: {upload_bg} !important;
    border: 2px dashed {upload_border} !important;
    border-radius: 12px !important;
}}
[data-testid="stSidebar"] [data-testid="stFileUploader"] * {{
    color: {upload_text} !important;
}}
[data-testid="stSidebar"] .stButton > button {{
    background: {btn_bg} !important;
    border: 1.5px solid {btn_border} !important;
    color: {btn_text} !important;
    border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
}}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {accent1}, {accent2}) !important;
    border: none !important;
    color: #ffffff !important;
}}

/* ── Top navbar ── */
.top-navbar {{
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 52px;
    background: {navbar_bg};
    backdrop-filter: blur(20px);
    border-bottom: 1px solid {border_color};
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1.5rem;
    z-index: 99999;
}}
.navbar-left {{
    display: flex;
    align-items: center;
    gap: 0.55rem;
}}
.navbar-wordmark {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    display: flex;
    align-items: baseline;
    gap: 0px;
}}
.navbar-doc {{ color: {text_primary}; }}
.navbar-ai {{
    background: linear-gradient(135deg, {accent1}, {accent2});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.navbar-tagline {{
    font-size: 0.65rem;
    color: {text_muted};
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding-left: 0.55rem;
    border-left: 1px solid {border_color};
    font-weight: 400;
    margin-left: 0.3rem;
}}

/* DocAI badge top RIGHT */
.navbar-right {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: {btn_bg};
    border: 1px solid {btn_border};
    border-radius: 10px;
    padding: 0.28rem 0.7rem 0.28rem 0.45rem;
}}
.navbar-right-text {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: -0.01em;
}}
.nr-doc {{ color: {text_primary}; }}
.nr-ai {{
    background: linear-gradient(135deg, {accent1}, {accent2});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

/* ── Main content ── */
.main .block-container {{
    padding-top: 4.2rem !important;
    padding-bottom: 2rem !important;
    max-width: 820px !important;
}}

/* ── Welcome section with logo watermark behind ── */
.welcome-wrap {{
    position: relative;
    max-width: 580px;
    margin: 0.5rem auto 1.5rem;
    border-radius: 20px;
    overflow: hidden;
}}
.welcome-logo-bg {{
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 85%;
    height: 85%;
    opacity: {wm_opacity};
    filter: blur(6px) saturate(0.4);
    z-index: 0;
    pointer-events: none;
    display: flex;
    align-items: center;
    justify-content: center;
}}
.welcome-logo-bg img {{
    width: 100%;
    height: 100%;
    object-fit: contain;
}}
.welcome-card {{
    position: relative;
    z-index: 1;
    background: {welcome_bg};
    border: 1px solid {border_color};
    border-radius: 20px;
    padding: 2rem 2rem 1.75rem;
    text-align: center;
    box-shadow: {shadow};
    backdrop-filter: blur(8px);
}}
.welcome-icon {{ font-size: 2.5rem; margin-bottom: 0.6rem; }}
.welcome-title {{
    color: {text_primary};
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 0.4rem;
}}
.welcome-text {{
    color: {text_secondary};
    font-size: 0.88rem;
    line-height: 1.7;
    margin-bottom: 1.25rem;
}}
.steps-row {{
    display: flex;
    gap: 0.6rem;
    justify-content: center;
    flex-wrap: wrap;
}}
.step {{
    background: {chip_bg};
    border: 1px solid {chip_border};
    border-radius: 10px;
    padding: 0.45rem 0.85rem;
    font-size: 0.8rem;
    color: {chip_text};
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-weight: 500;
}}
.step-num {{
    background: linear-gradient(135deg, {accent1}, {accent2});
    border-radius: 50%;
    width: 18px; height: 18px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.65rem; font-weight: 700; color: white; flex-shrink: 0;
}}

/* ── Stat pills ── */
.stat-row {{
    display: flex; gap: 0.5rem; margin-bottom: 0.75rem;
}}
.stat-pill {{
    flex: 1; background: {stat_bg};
    border: 1px solid {stat_border};
    border-radius: 10px; padding: 0.5rem; text-align: center;
}}
.stat-val {{
    font-size: 1.15rem; font-weight: 700; color: {accent1};
    font-family: 'JetBrains Mono', monospace;
}}
.stat-lbl {{
    font-size: 0.6rem; color: {text_muted};
    text-transform: uppercase; letter-spacing: 0.08em;
}}

/* ── File card ── */
.file-card {{
    background: {'rgba(52,211,153,0.08)' if dark else 'rgba(5,150,105,0.06)'};
    border: 1px solid {'rgba(52,211,153,0.25)' if dark else 'rgba(5,150,105,0.2)'};
    border-radius: 10px; padding: 0.65rem 0.9rem; margin-bottom: 0.65rem;
}}
.file-card-label {{
    font-size: 0.62rem; color: {text_muted};
    text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.2rem;
}}
.file-card-name {{
    font-size: 0.85rem; color: {text_primary}; font-weight: 600;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {{
    background: {bg_card} !important;
    border: 1px solid {border_color} !important;
    border-radius: 14px !important;
    margin-bottom: 0.75rem;
    box-shadow: {shadow};
}}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
    border-left: 3px solid {user_border} !important;
    background: {user_bg} !important;
}}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {{
    border-left: 3px solid {asst_border} !important;
    background: {asst_bg} !important;
}}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3 {{
    color: {text_primary} !important;
}}

/* ── Chat input — truly compact, no surrounding box ── */
[data-testid="stBottom"] > div {{
    padding: 0.4rem 0 0.4rem 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
[data-testid="stBottom"] {{
    background: transparent !important;
    border-top: 1px solid {border_color} !important;
    padding: 0 !important;
}}
[data-testid="stChatInput"] {{
    background: transparent !important;
    border: none !important;
    padding: 0.3rem 0 !important;
}}
[data-testid="stChatInput"] textarea {{
    background: {input_bg} !important;
    border: 1.5px solid {input_border} !important;
    border-radius: 12px !important;
    color: {text_primary} !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.9rem !important;
    min-height: 46px !important;
    max-height: 46px !important;
    height: 46px !important;
    padding: 12px 50px 12px 16px !important;
    resize: none !important;
    overflow: hidden !important;
    line-height: 1.3 !important;
}}
[data-testid="stChatInput"] textarea::placeholder {{
    color: {text_muted} !important;
}}

/* ── Progress bar ── */
.stProgress > div > div > div > div {{
    background: linear-gradient(90deg, {accent1}, {accent2}) !important;
    border-radius: 8px !important;
}}

/* ── Alerts ── */
.stSuccess > div {{
    background: {'rgba(52,211,153,0.1)' if dark else 'rgba(5,150,105,0.08)'} !important;
    border: 1px solid {'rgba(52,211,153,0.3)' if dark else 'rgba(5,150,105,0.25)'} !important;
    border-radius: 10px !important; color: {text_primary} !important;
}}
.stInfo > div {{
    background: {'rgba(91,127,255,0.1)' if dark else 'rgba(59,91,219,0.08)'} !important;
    border: 1px solid {'rgba(91,127,255,0.25)' if dark else 'rgba(59,91,219,0.2)'} !important;
    border-radius: 10px !important; color: {text_primary} !important;
}}
.stError > div {{
    background: rgba(239,68,68,0.1) !important;
    border: 1px solid rgba(239,68,68,0.3) !important;
    border-radius: 10px !important;
}}
.stWarning > div {{
    background: rgba(245,158,11,0.1) !important;
    border: 1px solid rgba(245,158,11,0.3) !important;
    border-radius: 10px !important;
}}

.stButton > button {{
    border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.83rem !important;
    transition: all 0.15s ease !important;
}}
hr {{ border-color: {border_color} !important; }}
::-webkit-scrollbar {{ width: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{
    background: {'rgba(91,127,255,0.3)' if dark else 'rgba(59,91,219,0.2)'};
    border-radius: 8px;
}}
</style>
""", unsafe_allow_html=True)

# ── TOP NAVBAR ────────────────────────────────────────────────────────────────
# LEFT: logo icon + DocAI wordmark + tagline
# RIGHT: mini DocAI badge with logo icon
st.markdown(f"""
<div class="top-navbar">
    <div class="navbar-left">
        {logo_img_tag}
        <div class="navbar-wordmark">
            <span class="navbar-doc">Doc</span><span class="navbar-ai">AI</span>
        </div>
        <span class="navbar-tagline">AI Study Assistant</span>
    </div>
    <div class="navbar-right">
        {logo_img_tag}
        <div class="navbar-right-text">
            <span class="nr-doc">Doc</span><span class="nr-ai">AI</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── DARK/LIGHT TOGGLE — positioned below navbar ───────────────────────────────
# Hidden via CSS from navbar, placed as Streamlit button
st.markdown("<div style='height:0.1rem'></div>", unsafe_allow_html=True)
_, tcol = st.columns([14, 1])
with tcol:
    if st.button(toggle_icon, key="theme_toggle", help="Toggle dark/light mode"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='font-size:1rem;font-weight:700;color:{sidebar_label};
    font-family:Space Grotesk,sans-serif;margin-bottom:0.6rem;padding-top:0.5rem'>
    📂 Upload Notes
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload file",
        type=["pdf", "txt", "png", "jpg", "jpeg", "bmp", "tiff", "webp"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        ext = uploaded_file.name.split(".")[-1].upper()
        if ext in ["PNG", "JPG", "JPEG", "BMP", "TIFF", "WEBP"]:
            st.info(f"🖼️ Image — OCR ready")
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
                        st.warning(f"⏳ Large PDF ({total_pages} pages). Est. {total_pages // 20}–{total_pages // 10} min.")
                    update_progress(10, f"Reading {total_pages} pages...")
                    num_chunks = ingest_file(file_path, progress_callback=update_progress)
                    st.session_state.total_pages = total_pages
                else:
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
                st.success(f"✅ {num_chunks} chunks indexed.")
                progress_bar.empty()

            except RuntimeError as e:
                st.error(f"❌ {e}"); progress_bar.empty(); status_text.empty()
            except ValueError as e:
                st.error(f"❌ {e}"); progress_bar.empty(); status_text.empty()
            except Exception as e:
                st.error(f"❌ {type(e).__name__}: {e}"); progress_bar.empty(); status_text.empty()

    st.divider()

    if st.session_state.notes_loaded:
        st.markdown(f"""
        <div class="file-card">
            <div class="file-card-label">Active File</div>
            <div class="file-card-name">📄 {st.session_state.file_name}</div>
        </div>
        <div class="stat-row">
            <div class="stat-pill">
                <div class="stat-val">{st.session_state.total_pages}</div>
                <div class="stat-lbl">Pages</div>
            </div>
            <div class="stat-pill">
                <div class="stat-val">{st.session_state.total_chunks}</div>
                <div class="stat-lbl">Chunks</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🗑️ Clear Notes", use_container_width=True):
            clear_collection()
            st.session_state.notes_loaded = False
            st.session_state.messages = []
            st.session_state.total_pages = 0
            st.session_state.total_chunks = 0
            st.session_state.file_name = ""
            st.rerun()
    else:
        st.markdown(f"""
        <div style='color:{upload_text};font-size:0.82rem;line-height:1.8;padding:0.3rem 0;'>
        ⬆️ Upload a PDF, image,<br>or text file to get started.
        </div>
        """, unsafe_allow_html=True)

    if st.button("🧹 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown(f"""
    <div style='font-size:0.7rem;color:{text_muted};line-height:2;'>
    🟦 Groq · LLaMA 3.3<br>
    🟪 ChromaDB · Vector DB<br>
    🟩 PyMuPDF · Groq Vision
    </div>
    """, unsafe_allow_html=True)

# ── MAIN AREA ─────────────────────────────────────────────────────────────────
if not st.session_state.messages:
    if not st.session_state.notes_loaded:
        # Welcome card with logo blurred BEHIND it
        st.markdown(f"""
        <div class="welcome-wrap">
            <div class="welcome-logo-bg">
                {wm_img}
            </div>
            <div class="welcome-card">
                <div class="welcome-title">Welcome to DocAI</div>
                <div class="welcome-text">
                    Upload your notes, textbooks, or images and ask anything.<br>
                    Powered by Groq's LLaMA3 for lightning-fast answers.
                </div>
                <div class="steps-row">
                    <div class="step"><div class="step-num">1</div>Upload a PDF or image</div>
                    <div class="step"><div class="step-num">2</div>Click Process File</div>
                    <div class="step"><div class="step-num">3</div>Ask your question</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="welcome-wrap">
            <div class="welcome-logo-bg">
                {wm_img}
            </div>
            <div class="welcome-card">
                <div class="welcome-title">✅ Notes loaded! Start asking.</div>
                <div class="welcome-text">
                    <b style="color:{accent1}">{st.session_state.file_name}</b> is ready.<br>
                    {st.session_state.total_pages} pages · {st.session_state.total_chunks} chunks indexed
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"<div style='color:{text_secondary};font-weight:600;font-size:0.88rem;margin-bottom:0.4rem;'>💡 Try asking:</div>", unsafe_allow_html=True)
        suggestions = [
            "📝 Summarize the main topics",
            "🔑 What are the key concepts?",
            "❓ Create 5 quiz questions",
            "📊 Explain the complex parts",
            "🔍 What is this document about?",
            "💡 Give me study tips for this"
        ]
        cols = st.columns(3)
        for i, s in enumerate(suggestions):
            with cols[i % 3]:
                if st.button(s, use_container_width=True, key=f"sug_{i}"):
                    st.session_state.suggested_question = s
                    st.rerun()

# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Handle suggestion click ───────────────────────────────────────────────────
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
                    chunks = retrieve_relevant_chunks(question)
                    answer = generate_answer(question, chunks)
                elif not st.session_state.notes_loaded:
                    from groq import Groq
                    from config.settings import GROQ_API_KEY
                    groq_client = Groq(api_key=GROQ_API_KEY)
                    response = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        temperature=0.7,
                        messages=[
                            {"role": "system", "content": (
                                "You are DocAI, a friendly and enthusiastic study assistant. "
                                "Answer questions helpfully and creatively. "
                                "Use markdown — **bold**, bullet points, headers. "
                                "Keep it educational but fun."
                            )},
                            {"role": "user", "content": question}
                        ]
                    )
                    answer = response.choices[0].message.content
                else:
                    try:
                        chunks = retrieve_relevant_chunks(question)
                        if chunks and len(chunks[0]) > 50:
                            answer = generate_answer(question, chunks)
                        else:
                            raise ValueError("Not enough context")
                    except Exception:
                        from groq import Groq
                        from config.settings import GROQ_API_KEY
                        groq_client = Groq(api_key=GROQ_API_KEY)
                        response = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            temperature=0.7,
                            messages=[
                                {"role": "system", "content": (
                                    "You are DocAI, a friendly study assistant. "
                                    "Answer helpfully using markdown formatting."
                                )},
                                {"role": "user", "content": question}
                            ]
                        )
                        answer = f"*Answering from general knowledge*\n\n{response.choices[0].message.content}"
            except Exception as e:
                answer = f"❌ Something went wrong: {e}"

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})