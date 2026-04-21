# 📚 AI Study Assistant

A RAG (Retrieval Augmented Generation) based study tool built with Streamlit.  
Upload your notes → Ask questions → Get answers grounded in your own material.

---

## 🚀 Live Demo

> Deployed on Streamlit Cloud → [https://docai17r.streamlit.app/](https://share.streamlit.io)
---

## 🧠 How It Works

```
Your PDF/TXT notes
      ↓
Extract text (PyPDF)
      ↓
Split into chunks (LangChain)
      ↓
Store in vector DB (ChromaDB)
      ↓
User asks a question
      ↓
Find relevant chunks (similarity search)
      ↓
Send chunks + question to LLM (Groq)
      ↓
Answer displayed in chat
```

---

## 🛠️ Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| UI | Streamlit | Chat interface + file upload |
| PDF Reading | PyPDF | Extract text from PDF files |
| Text Chunking | LangChain | Split text into searchable pieces |
| Vector Database | ChromaDB | Store and search text embeddings |
| LLM | Groq (LLaMA3-8b) | Generate answers from context |
| Config | python-dotenv | Manage API keys securely |

---

## 📁 Project Structure

```
ai-study-assistant/
├── app.py                          # Streamlit UI — entry point only
├── packages.txt                    # System dependencies for Streamlit Cloud
├── requirements.txt                # Python dependencies
├── .env                            # API keys (never commit this!)
├── .gitignore                      # Excludes .env, venv, __pycache__
├── README.md
│
├── config/
│   ├── __init__.py
│   └── settings.py                 # All config: model, chunk size, paths
│
├── services/
│   ├── __init__.py
│   ├── ingestion_service.py        # PDF → text → chunks → ChromaDB
│   ├── retrieval_service.py        # Similarity search on stored chunks
│   └── llm_service.py              # Prompt building + Groq LLM call
│
└── utils/
    ├── __init__.py
    └── file_handler.py             # Save and validate uploaded files
```

Each file has a single responsibility — making the codebase easy to extend and debug.

---

## ⚙️ Setup & Run Locally

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/ai-study-assistant.git
cd ai-study-assistant
```

**2. Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Add your API key**

Create a `.env` file in the root folder:
```
GROQ_API_KEY=gsk_your_key_here
```

Get your free Groq API key at [console.groq.com](https://console.groq.com)

**5. Run the app**
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## ☁️ Deploy on Streamlit Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select repo → set main file as `app.py`
4. Go to **Advanced settings → Secrets** and add:
```toml
GROQ_API_KEY = "gsk_your_key_here"
```
5. Click **Deploy**

---

## 📌 Features

- Upload PDF or TXT notes
- Ask questions in plain English
- Answers generated only from your uploaded notes
- Chat history maintained within session
- Clear notes and start fresh anytime
- Fast responses powered by Groq (LLaMA3)

---

## 🔮 Future Improvements

- [ ] Support multiple file uploads
- [ ] Show source chunks alongside answers
- [ ] Conversation memory across turns
- [ ] Support for DOCX files
- [ ] Export chat history as PDF

---

## 🧩 Design Principles

This project follows the **Single Responsibility Principle**:

| File | Responsibility |
|---|---|
| `app.py` | UI only — never processes data |
| `settings.py` | Config only — change model/params here |
| `ingestion_service.py` | File reading and indexing only |
| `retrieval_service.py` | Vector search only |
| `llm_service.py` | LLM call only |
| `file_handler.py` | Disk I/O only |

Want to swap Groq for OpenAI? Edit only `llm_service.py`.  
Want to swap ChromaDB for Pinecone? Edit only `retrieval_service.py`.

---

## 📄 License

MIT — free to use and modify.

---

## 🙋 Author

Built by [Rishabh Kumar](https://github.com/rishabh1713)  
Feel free to ⭐ the repo if you found it useful!
