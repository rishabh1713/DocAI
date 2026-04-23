# 📘 DocAI — Your AI Study Buddy

> **Learn Smarter. Ask Better. Achieve More.**

DocAI is a RAG-based AI study assistant that lets you upload your notes, PDFs, or images and ask questions — getting answers grounded in your own material. Built with a clean dark/light UI, OCR support, and blazing-fast responses via Groq.

---

## 🚀 Live Demo

> [**Try DocAI Live →**](https://docai17r.streamlit.app/)

---

## ✨ Features

- 📄 **PDF, TXT, and Image upload** — drag and drop any study material
- 🤖 **RAG pipeline** — answers are grounded in your uploaded content
- 🖼️ **OCR support** — extracts text from images and image-heavy PDFs using Groq Vision API
- 🧠 **Smart question routing** — detects if a question is about your notes or general knowledge and responds accordingly
- 🌗 **Dark / Light mode toggle** — switch themes instantly
- 📊 **Live progress bar** — shows real-time page processing status on large PDFs
- 💡 **Suggested queries** — one-click starter questions after uploading
- 🗂️ **Multi-format OCR** — handles pure text pages, image-only pages, and mixed pages separately for maximum accuracy
- 💬 **General chat fallback** — answers general questions even without uploaded notes using Groq LLaMA3

---

## 🛠️ Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| UI | Streamlit | Chat interface, file upload, dark/light toggle |
| Styling | Custom CSS + Google Fonts | Inter, Plus Jakarta Sans, JetBrains Mono |
| PDF Reading | PyPDF + PyMuPDF (fitz) | Text extraction and page rendering |
| OCR | Groq Vision API (Pixtral / LLaMA4 Scout) | Image and scanned page text extraction |
| Text Chunking | LangChain | Splits text into overlapping 500-char chunks |
| Vector Database | ChromaDB | Stores and searches text embeddings |
| LLM | Groq · LLaMA 3.3 70B Versatile | Answer generation |
| Config | python-dotenv | Secure API key management |

---

## 📁 Project Structure

```
ai-study-assistant/
│
├── app.py                          # Streamlit UI — entry point only
├── logo.jpg                        # DocAI logo (used in navbar + watermark)
├── packages.txt                    # System deps for Streamlit Cloud
├── requirements.txt                # Python dependencies
├── .env                            # API keys (never commit this!)
├── .gitignore
├── README.md
│
├── config/
│   ├── __init__.py
│   └── settings.py                 # Model names, chunk size, API keys, paths
│
├── services/
│   ├── __init__.py
│   ├── ingestion_service.py        # PDF/image → text → chunks → ChromaDB
│   ├── retrieval_service.py        # Similarity search on stored chunks
│   ├── llm_service.py              # Prompt building + Groq LLM call
│   └── vision_ocr_service.py       # Groq Vision API OCR for images/pages
│
└── utils/
    ├── __init__.py
    └── file_handler.py             # File save, validate, delete, is_image check
```

---

## ⚙️ How It Works

```
Upload PDF / Image / TXT
         ↓
┌─────────────────────────────┐
│     ingestion_service.py    │
│                             │
│  Text page? → PyPDF extract │
│  Image page? → Groq Vision  │
│  Mixed page? → Both         │
│                             │
│  Chunk text (500 chars)     │
│  Store in ChromaDB          │
└─────────────────────────────┘
         ↓
   User asks a question
         ↓
┌─────────────────────────────┐
│    retrieval_service.py     │
│  Similarity search → top 3  │
│       chunks returned       │
└─────────────────────────────┘
         ↓
┌─────────────────────────────┐
│      llm_service.py         │
│  Chunks + Question → Groq   │
│  LLaMA 3.3 → Answer         │
└─────────────────────────────┘
         ↓
   Answer shown in chat
```

---

## 🧩 Design Principles

Each file has **one single responsibility**:

| File | Responsibility |
|---|---|
| `app.py` | UI only — never processes data |
| `settings.py` | All config — change model or params here |
| `ingestion_service.py` | File reading, OCR routing, and indexing |
| `retrieval_service.py` | Vector similarity search only |
| `llm_service.py` | Prompt building and LLM call only |
| `vision_ocr_service.py` | Groq Vision API calls only |
| `file_handler.py` | Disk I/O — save, validate, delete |

Want to swap Groq for OpenAI? Edit only `llm_service.py` and `vision_ocr_service.py`.
Want to swap ChromaDB for Pinecone? Edit only `retrieval_service.py`.

---

## ⚙️ Setup & Run Locally

**1. Clone the repo**
```bash
git clone https://github.com/rishabh1713/ai-study-assistant.git
cd ai-study-assistant
```

**2. Create and activate virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Add your API keys**

Create a `.env` file in the root:
```
GROQ_API_KEY=gsk_your_groq_key_here
```

Get your free Groq API key at [console.groq.com](https://console.groq.com)

**5. Run**
```bash
streamlit run app.py
```

---

## ☁️ Deploy on Streamlit Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select repo → main file `app.py`
4. Go to **Advanced settings → Secrets** and add:
```toml
GROQ_API_KEY = "gsk_your_key_here"
```
5. Click **Deploy** ✅

---

## 📦 Requirements

```
streamlit
pypdf
pymupdf
langchain
langchain-community
langchain-openai
chromadb
groq
python-dotenv
pillow
numpy
```

`packages.txt` (for Streamlit Cloud):
```
libsqlite3-dev
```

---

## 🔮 Future Improvements

- [ ] Multiple file uploads in one session
- [ ] Show source chunks alongside answers
- [ ] Export chat history as PDF
- [ ] Support DOCX files
- [ ] Hindi / regional language OCR support
- [ ] Conversation memory across sessions

---

## 📄 License

MIT — free to use and modify.

---

## 🙋 Author

Built by [Rishabh Kumar](https://github.com/rishabh1713)

⭐ Star the repo if you found it useful!