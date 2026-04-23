import sys
import os

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

# ── Refined Modern Color Palette ──────────────────────────────────────────────
if dark:
    bg_main        = "#09090b"  
    bg_sidebar     = "#121214"
    bg_card        = "rgba(39, 39, 42, 0.4)"
    border_color   = "rgba(255, 255, 255, 0.08)"
    text_primary   = "#fafafa"
    text_secondary = "#a1a1aa"
    text_muted     = "#52525b"
    accent1        = "#6366f1"  
    accent2        = "#8b5cf6"  
    accent3        = "#10b981"  
    chip_bg        = "rgba(99, 102, 241, 0.1)"
    chip_border    = "rgba(99, 102, 241, 0.2)"
    chip_text      = "#818cf8"
    input_bg       = "#18181b"
    input_border   = "rgba(255, 255, 255, 0.1)"
    toggle_icon    = "☀️"
    upload_bg      = "#18181b"
    upload_border  = "rgba(99, 102, 241, 0.4)"
    upload_text    = "#a1a1aa"
    sidebar_label  = "#e4e4e7"
    stat_bg        = "#18181b"
    stat_border    = "rgba(255, 255, 255, 0.05)"
    btn_bg         = "#18181b"
    btn_border     = "rgba(255, 255, 255, 0.1)"
    btn_text       = "#e4e4e7"
    shadow         = "0 8px 32px rgba(0, 0, 0, 0.4)"
    user_border    = "#6366f1"
    user_bg        = "rgba(99, 102, 241, 0.05)"
    asst_border    = "transparent"
    asst_bg        = "rgba(39, 39, 42, 0.3)"
    navbar_bg      = "rgba(9, 9, 11, 0.8)"
    welcome_bg     = "rgba(18, 18, 20, 0.6)"
    logo_doc_color = "#fafafa"
else:
    bg_main        = "#fafafa"
    bg_sidebar     = "#ffffff"
    bg_card        = "#ffffff"
    border_color   = "rgba(0, 0, 0, 0.08)"
    text_primary   = "#09090b"
    text_secondary = "#52525b"
    text_muted     = "#a1a1aa"
    accent1        = "#4f46e5"  
    accent2        = "#7c3aed"  
    accent3        = "#059669"  
    chip_bg        = "rgba(79, 70, 229, 0.08)"
    chip_border    = "rgba(79, 70, 229, 0.2)"
    chip_text      = "#4f46e5"
    input_bg       = "#ffffff"
    input_border   = "rgba(0, 0, 0, 0.12)"
    toggle_icon    = "🌙"
    upload_bg      = "#f8fafc"
    upload_border  = "rgba(79, 70, 229, 0.3)"
    upload_text    = "#64748b"
    sidebar_label  = "#09090b"
    stat_bg        = "#f8fafc"
    stat_border    = "rgba(0, 0, 0, 0.05)"
    btn_bg         = "#ffffff"
    btn_border     = "rgba(0, 0, 0, 0.12)"
    btn_text       = "#09090b"
    shadow         = "0 4px 20px rgba(0, 0, 0, 0.04)"
    user_border    = "#4f46e5"
    user_bg        = "rgba(79, 70, 229, 0.03)"
    asst_border    = "transparent"
    asst_bg        = "#ffffff"
    navbar_bg      = "rgba(250, 250, 250, 0.8)"
    welcome_bg     = "rgba(255, 255, 255, 0.7)"
    logo_doc_color = "#0f172a" # Dark navy for light mode

logo_gradient = "linear-gradient(135deg, #2563eb, #9333ea)"

# ── Clean, Modern CSS Injection ───────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Plus+Jakarta+Sans:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', sans-serif !important; }}
h1, h2, h3, h4, h5, h6 {{ font-family: 'Plus Jakarta Sans', sans-serif !important; }}
#MainMenu, footer {{ visibility: hidden; display: none; }}

/* Bring back the native expand sidebar button and style it */
header[data-testid="stHeader"] {{
    background: transparent !important;
    z-index: 100000 !important;
}}
[data-testid="collapsedControl"] {{
    top: 70px !important; 
    left: 15px !important;
    background: {bg_card} !important;
    border: 1px solid {border_color} !important;
    border-radius: 8px !important;
    box-shadow: {shadow} !important;
    z-index: 100000 !important;
    transition: all 0.2s ease;
    padding: 0.2rem !important;
}}
[data-testid="collapsedControl"]:hover {{
    background: {chip_bg} !important;
    border-color: {accent1} !important;
}}
[data-testid="collapsedControl"] svg {{
    fill: {text_primary} !important;
    color: {text_primary} !important;
}}

.stApp {{ background-color: {bg_main} !important; }}

/* ── The Theme Toggle Button Positioned in Navbar ── */
div[data-testid="stMainBlockContainer"] .stButton:first-of-type {{
    position: fixed;
    top: 10px;
    right: 24px;
    z-index: 100001;
    width: auto;
}}
div[data-testid="stMainBlockContainer"] .stButton:first-of-type button {{
    background: {bg_card} !important;
    border: 1px solid {border_color} !important;
    border-radius: 8px !important;
    padding: 0.35rem 0.6rem !important;
    box-shadow: {shadow} !important;
    transition: all 0.2s ease;
    font-size: 1.1rem !important;
}}
div[data-testid="stMainBlockContainer"] .stButton:first-of-type button:hover {{
    background: {chip_bg} !important;
    border-color: {accent1} !important;
    transform: translateY(-1px);
}}

/* ── Sidebar Elements ── */
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
    border: 1.5px dashed {upload_border} !important;
    border-radius: 12px !important;
    transition: all 0.2s ease;
}}
[data-testid="stSidebar"] [data-testid="stFileUploader"]:hover {{
    border-color: {accent1} !important;
    background: {chip_bg} !important;
}}
[data-testid="stSidebar"] [data-testid="stFileUploader"] * {{
    color: {upload_text} !important;
}}
[data-testid="stSidebar"] .stButton > button {{
    background: {btn_bg} !important;
    border: 1px solid {btn_border} !important;
    color: {btn_text} !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease;
    padding: 0.5rem 1rem !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    border-color: {text_secondary} !important;
    transform: translateY(-1px);
}}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
    background: {logo_gradient} !important;
    border: none !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3) !important;
}}
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {{
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4) !important;
    transform: translateY(-2px);
}}

/* ── Top navbar ── */
.top-navbar {{
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 56px;
    background: {navbar_bg};
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
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
    gap: 0.75rem;
}}
.navbar-wordmark {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.15rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    display: flex;
    align-items: baseline;
}}
.navbar-doc {{ color: {text_primary}; }}
.navbar-ai {{
    background: {logo_gradient};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.navbar-tagline {{
    font-size: 0.7rem;
    color: {text_muted};
    letter-spacing: 0.05em;
    padding-left: 0.75rem;
    border-left: 1px solid {border_color};
    font-weight: 500;
    margin-left: 0.25rem;
}}

/* ── Sidebar Custom Logo Component ── */
.custom-logo-wrapper {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 5px 0 25px 0;
}}
.custom-icon {{
    width: 32px;
    height: 38px;
    background: {logo_gradient};
    border-radius: 4px 14px 14px 4px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: flex-start;
    padding-left: 6px;
    gap: 5px;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
    position: relative;
}}
.custom-icon::after {{
    content: '';
    position: absolute;
    bottom: -3px;
    left: 0;
    width: 100%;
    height: 6px;
    background: {logo_gradient};
    border-radius: 0 0 14px 4px;
    z-index: -1;
    opacity: 0.6;
}}
.custom-icon-line {{
    width: 16px;
    height: 3px;
    background: #ffffff;
    border-radius: 2px;
}}
.custom-icon-line.short {{ width: 10px; }}
.custom-text {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1;
}}
.custom-text-doc {{ color: {logo_doc_color}; }}
.custom-text-ai {{
    background: {logo_gradient};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}

/* ── Main content ── */
.main .block-container {{
    padding-top: 5rem !important;
    padding-bottom: 6rem !important;
    max-width: 860px !important;
}}

/* ── Welcome section ── */
.welcome-wrap {{
    position: relative;
    max-width: 640px;
    margin: 2rem auto;
    border-radius: 24px;
    overflow: hidden;
}}
.welcome-logo-bg {{
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 120%;
    height: 120%;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 70%);
    filter: blur(40px);
    z-index: 0;
    pointer-events: none;
}}
.welcome-card {{
    position: relative;
    z-index: 1;
    background: {welcome_bg};
    border: 1px solid {border_color};
    border-radius: 24px;
    padding: 3rem 2.5rem;
    text-align: center;
    box-shadow: {shadow};
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
}}
.welcome-title {{
    color: {text_primary};
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.75rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
    letter-spacing: -0.02em;
}}
.welcome-text {{
    color: {text_secondary};
    font-size: 0.95rem;
    line-height: 1.6;
    margin-bottom: 2rem;
}}
.steps-row {{
    display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap;
}}
.step {{
    background: {chip_bg}; border: 1px solid {chip_border}; border-radius: 8px;
    padding: 0.5rem 1rem; font-size: 0.85rem; color: {chip_text};
    display: flex; align-items: center; gap: 0.5rem; font-weight: 500;
}}
.step-num {{
    background: {accent1}; border-radius: 4px; width: 20px; height: 20px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.7rem; font-weight: 700; color: white; flex-shrink: 0;
}}

/* ── Stat pills & File card ── */
.stat-row {{ display: flex; gap: 0.5rem; margin-bottom: 1rem; }}
.stat-pill {{
    flex: 1; background: {stat_bg}; border: 1px solid {stat_border};
    border-radius: 8px; padding: 0.75rem; text-align: center;
}}
.stat-val {{ font-size: 1.25rem; font-weight: 600; color: {text_primary}; }}
.stat-lbl {{ font-size: 0.65rem; color: {text_muted}; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.2rem; }}
.file-card {{
    background: {'rgba(16, 185, 129, 0.05)' if dark else 'rgba(5, 150, 105, 0.03)'};
    border: 1px solid {'rgba(16, 185, 129, 0.2)' if dark else 'rgba(5, 150, 105, 0.15)'};
    border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.75rem;
}}
.file-card-label {{ font-size: 0.65rem; color: {text_muted}; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; font-weight: 500; }}
.file-card-name {{ font-size: 0.9rem; color: {text_primary}; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {{
    background: {bg_card} !important;
    border: 1px solid {border_color} !important;
    border-radius: 12px !important;
    margin-bottom: 1rem;
    padding: 1.25rem !important;
    box-shadow: {shadow};
}}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
    background: {user_bg} !important;
    border: 1px solid {chip_border} !important;
    border-left: 4px solid {user_border} !important;
}}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {{
    background: {asst_bg} !important;
    border-left: 4px solid transparent !important;
}}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3 {{ color: {text_primary} !important; line-height: 1.6 !important; }}
[data-testid="stChatMessage"] code {{
    background: {bg_main} !important; border: 1px solid {border_color} !important;
    border-radius: 4px !important; padding: 0.2rem 0.4rem !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 0.85em !important; color: {accent1} !important;
}}

/* ── Chat input ── */
[data-testid="stBottom"] > div {{
    padding: 1rem 1rem 1.5rem 1rem !important;
    background: linear-gradient(to top, {bg_main} 80%, transparent) !important; border: none !important;
}}
[data-testid="stChatInput"] {{ background: transparent !important; border: none !important; padding: 0 !important; max-width: 860px !important; margin: 0 auto !important; }}
[data-testid="stChatInput"] textarea {{
    background: {input_bg} !important; border: 1px solid {input_border} !important;
    border-radius: 12px !important; color: {text_primary} !important;
    font-size: 0.95rem !important; min-height: 52px !important; max-height: 150px !important;
    padding: 14px 45px 14px 18px !important; box-shadow: 0 4px 20px rgba(0,0,0,0.05) !important; transition: border-color 0.2s ease;
}}
[data-testid="stChatInput"] textarea:focus {{ border-color: {accent1} !important; }}

/* ── Suggestions Buttons ── */
.stButton > button[key^="sug_"] {{
    background: {bg_card} !important; border: 1px solid {border_color} !important; color: {text_secondary} !important;
    border-radius: 8px !important; padding: 0.75rem !important; font-size: 0.85rem !important; text-align: left !important; justify-content: flex-start !important;
}}
.stButton > button[key^="sug_"]:hover {{ background: {chip_bg} !important; border-color: {chip_border} !important; color: {text_primary} !important; }}

.stProgress > div > div > div > div {{ background: {logo_gradient} !important; border-radius: 8px !important; }}
hr {{ border-color: {border_color} !important; margin: 2rem 0 !important; }}
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {border_color}; border-radius: 8px; }}
::-webkit-scrollbar-thumb:hover {{ background: {text_muted}; }}
</style>
""", unsafe_allow_html=True)

# ── TOP NAVBAR ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="top-navbar">
    <div class="navbar-left">
        <div class="navbar-wordmark">
            <span class="navbar-doc">Doc</span><span class="navbar-ai">AI</span>
        </div>
        <span class="navbar-tagline">STUDY ASSISTANT</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── DARK/LIGHT TOGGLE (Positioned via CSS into Navbar Right) ──────────────────
if st.button(toggle_icon, key="theme_toggle", help="Toggle dark/light mode"):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # --- Custom Logo Design injected here ---
    st.markdown(f"""
    <div class="custom-logo-wrapper">
        <div class="custom-icon">
            <div class="custom-icon-line"></div>
            <div class="custom-icon-line"></div>
            <div class="custom-icon-line short"></div>
        </div>
        <div class="custom-text">
            <span class="custom-text-doc">Doc</span><span class="custom-text-ai">AI</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='font-size:0.9rem;font-weight:600;color:{sidebar_label};
    font-family:Plus Jakarta Sans,sans-serif;margin-bottom:0.8rem;'>
    📂 Upload Documents
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
            <div class="file-card-label">Active Document</div>
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

        if st.button("🗑️ Clear Context", use_container_width=True):
            clear_collection()
            st.session_state.notes_loaded = False
            st.session_state.messages = []
            st.session_state.total_pages = 0
            st.session_state.total_chunks = 0
            st.session_state.file_name = ""
            st.rerun()
    else:
        st.markdown(f"""
        <div style='color:{upload_text};font-size:0.85rem;line-height:1.6;padding:0.5rem 0;'>
        Upload a PDF, image, or text file to inject context into the AI.
        </div>
        """, unsafe_allow_html=True)

    if st.button("🧹 Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown(f"""
    <div style='font-size:0.75rem;color:{text_muted};line-height:1.8;text-align:center;'>
    Powered by <b>Groq LLaMA 3.3</b><br>
    ChromaDB & PyMuPDF
    </div>
    """, unsafe_allow_html=True)

# ── MAIN AREA ─────────────────────────────────────────────────────────────────
if not st.session_state.messages:
    if not st.session_state.notes_loaded:
        st.markdown(f"""
        <div class="welcome-wrap">
            <div class="welcome-logo-bg"></div>
            <div class="welcome-card">
                <div class="welcome-title">Welcome to DocAI</div>
                <div class="welcome-text">
                    Upload your notes, textbooks, or images and ask anything.<br>
                    Powered by Groq's LLaMA3 for lightning-fast answers.
                </div>
                <div class="steps-row">
                    <div class="step"><div class="step-num">1</div>Upload File</div>
                    <div class="step"><div class="step-num">2</div>Process</div>
                    <div class="step"><div class="step-num">3</div>Ask Away</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="welcome-wrap">
            <div class="welcome-logo-bg"></div>
            <div class="welcome-card">
                <div class="welcome-title">✅ Context Loaded</div>
                <div class="welcome-text">
                    <b style="color:{accent1}">{st.session_state.file_name}</b> is ready for queries.<br>
                    Indexed {st.session_state.total_pages} pages across {st.session_state.total_chunks} vector chunks.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"<div style='color:{text_secondary};font-weight:600;font-size:0.85rem;margin-bottom:0.8rem;text-transform:uppercase;letter-spacing:0.05em;'>💡 Suggested Queries</div>", unsafe_allow_html=True)
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
                if st.button(s, use_container_width=True, key=f"sug_btn_{i}"):
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
        with st.spinner("Analyzing context..."):
            try:
                chunks = retrieve_relevant_chunks(question)
                answer = generate_answer(question, chunks)
            except Exception as e:
                answer = f"❌ Error retrieving data: {e}"
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────────
if question := st.chat_input("Ask about your notes, or anything else..."):
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
        with st.spinner("Generating response..."):
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
                        answer = f"*General Knowledge Fallback*\n\n{response.choices[0].message.content}"
            except Exception as e:
                answer = f"❌ Encountered an issue: {e}"

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})