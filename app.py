import streamlit as st
import openai
import os
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta
from fpdf import FPDF
import base64

# ---------- CONFIG ----------
st.set_page_config(
    page_title="Smart Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# ---------- SESSION ----------
ss = st.session_state

if "history" not in ss:
    ss.history = []
if "stats" not in ss:
    ss.stats = {
        "summaries": 0,
        "explanations": 0,
        "quizzes": 0,
        "flashcards": 0,
        "total": 0,
    }
if "last_output" not in ss:
    ss.last_output = ""
if "last_action" not in ss:
    ss.last_action = ""
if "last_input" not in ss:
    ss.last_input = ""
if "uploaded_text" not in ss:
    ss.uploaded_text = ""
if "theme" not in ss:
    ss.theme = "light"

# Pomodoro state
if "pomo_running" not in ss:
    ss.pomo_running = False
if "pomo_mode" not in ss:
    ss.pomo_mode = "Focus"  # or "Break"
if "pomo_end" not in ss:
    ss.pomo_end = None
if "pomo_focus_len" not in ss:
    ss.pomo_focus_len = 25
if "pomo_break_len" not in ss:
    ss.pomo_break_len = 5

# ---------- THEME CSS ----------
LIGHT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1.5rem !important;
}
.app-shell {
    max-width: 1180px;
    margin: 0 auto;
}

/* Light theme placeholders */
.stTextArea textarea::placeholder,
.stTextInput input::placeholder {
    color: #9ca3af !important;   /* soft gray */
    opacity: 1 !important;
}


/* Topbar */
.topbar {
    background: #ffffff;
    border-radius: 18px;
    padding: 0.85rem 1.4rem;
    border: 1px solid rgba(148,163,184,0.28);
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 14px 38px rgba(15,23,42,0.06);
    margin-bottom: 1.6rem;
}
.brand {
    display: flex;
    gap: .7rem;
    align-items: center;
}
.brand-icon {
    width: 28px;
    height: 28px;
    border-radius: 9px;
    background: linear-gradient(135deg,#4f46e5,#22c55e);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    font-size: 16px;
}
.brand-title {
    font-weight: 700;
    font-size: 1.05rem;
    color: #111827;
}
.brand-sub {
    font-size: .7rem;
    color: #9ca3af;
}

.nav-links {
    display: flex;
    gap: .4rem;
    align-items: center;
}
.nav-pill {
    padding: .3rem .85rem;
    border-radius: 999px;
    font-size: .72rem;
    color: #6b7280;
    background: transparent;
    border: 1px solid transparent;
    cursor: pointer;
}
.nav-pill:hover {
    color: #4f46e5;
    border-color: rgba(79,70,229,0.18);
    background: rgba(249,250,251,0.9);
}
.nav-pill.active {
    color: #4f46e5;
    background: #eef2ff;
    border-color: rgba(79,70,229,0.35);
    font-weight: 600;
}

/* Hero */
.hero-title {
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    background: linear-gradient(120deg,#4f46e5 0%,#7c3aed 40%,#f97316 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: .15rem;
}
.hero-sub {
    font-size: .9rem;
    color: #6b7280;
    max-width: 520px;
}

/* Cards */
.input-card,
.side-card,
.result-card {
    background: #ffffff;
    border-radius: 18px;
    border: 1px solid rgba(226,232,240,0.95);
    box-shadow: 0 10px 26px rgba(15,23,42,0.03);
}
.input-card {
    padding: 1rem 1rem .9rem;
}
.side-card {
    padding: .85rem .9rem .9rem;
    margin-bottom: .8rem;
}
.result-card {
    padding: 1rem 1rem 1.25rem;
    margin-top: .5rem;
}

/* File uploader */
[data-testid="stFileUploader"] section {
    border-radius: 14px;
    border: 1px dashed rgba(148,163,184,0.6);
    background: #f9fafb;
}

/* Text area */
.stTextArea textarea {
    border-radius: 14px !important;
    border: 1px solid #e5e7eb !important;
    font-size: .85rem !important;
    background: #f9fafb !important;
    padding: .7rem .8rem !important;
}
.stTextArea textarea:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 1px rgba(79,70,229,0.12);
    background: #ffffff !important;
}

/* Buttons */
.stButton button {
    border-radius: 999px !important;
    font-weight: 600 !important;
    font-size: .78rem !important;
    padding: 0.35rem 0.4rem !important;
    border: none !important;
    background: linear-gradient(135deg,#4f46e5,#7c3aed) !important;
    color: #ffffff !important;
    box-shadow: 0 9px 22px rgba(79,70,229,0.25);
    transition: all .18s ease-in-out;
}
.stButton button:hover {
    transform: translateY(-1px);
    box-shadow: 0 14px 30px rgba(79,70,229,0.32);
}
.stButton button:active {
    transform: translateY(1px);
    box-shadow: 0 6px 16px rgba(79,70,229,0.2);
}

/* Badges & history */
.badge {
    display: inline-flex;
    align-items: center;
    gap: .25rem;
    padding: .22rem .7rem;
    border-radius: 999px;
    background: rgba(79,70,229,0.06);
    color: #4338ca;
    font-size: .7rem;
    font-weight: 600;
    margin-bottom: .4rem;
}
.stat-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0,1fr));
    gap: .5rem;
}
.stat-item {
    padding: .5rem .55rem;
    border-radius: 12px;
    border: 1px solid rgba(229,231,235,1);
    background: linear-gradient(180deg,#ffffff,#f9fafb);
}
.stat-title {
    font-size: .6rem;
    color: #9ca3af;
}
.stat-value {
    font-size: 1.05rem;
    font-weight: 700;
    color: #111827;
}
.history-item {
    padding: .45rem .5rem;
    border-radius: 10px;
    background: #f9fafb;
    border: 1px solid rgba(229,231,235,1);
    margin-bottom: .34rem;
}
.history-type {
    font-size: .7rem;
    font-weight: 600;
    color: #111827;
}
.history-time {
    font-size: .6rem;
    color: #9ca3af;
}
.history-tag {
    font-size: .58rem;
    color: #6b7280;
    font-style: italic;
}

/* Footer */
.footer {
    text-align: center;
    color: #9ca3af;
    font-size: .7rem;
    padding-top: 1.2rem;
}

/* Anim */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
"""

DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

:root {
    color-scheme: dark;
}

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

/* Core backgrounds */
.stApp {
    background-color: #020817 !important;
}
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top,#020817,#020817) !important;
}
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1.5rem !important;
}
.app-shell {
    max-width: 1180px;
    margin: 0 auto;
}

/* Dark theme placeholders */
.stTextArea textarea::placeholder,
.stTextInput input::placeholder {
    color: #6b7280 !important;   /* visible but subtle */
    opacity: 1 !important;
}

/* File uploader helper text */
[data-testid="stFileUploader"] *::placeholder {
    color: #6b7280 !important;
}


/* Sidebar */
[data-testid="stSidebar"] {
    background: #020817 !important;
    box-shadow: 4px 0 26px rgba(0,0,0,0.55);
    border-right: 1px solid #111827;
}
[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}

/* Topbar */
.topbar {
    background: radial-gradient(circle at top left,#0b1020,#020817);
    border-radius: 18px;
    padding: 0.85rem 1.4rem;
    border: 1px solid rgba(75,85,99,0.9);
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 18px 40px rgba(0,0,0,0.9);
    margin-bottom: 1.6rem;
}
.brand {
    display: flex;
    gap: .7rem;
    align-items: center;
}
.brand-icon {
    width: 28px;
    height: 28px;
    border-radius: 9px;
    background: linear-gradient(135deg,#4f46e5,#22c55e);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    font-size: 16px;
}
.brand-title {
    font-weight: 700;
    font-size: 1.05rem;
    color: #e5e7eb;
}
.brand-sub {
    font-size: .7rem;
    color: #9ca3af;
}
.nav-links {
    display: flex;
    gap: .4rem;
    align-items: center;
}
.nav-pill {
    padding: .3rem .85rem;
    border-radius: 999px;
    font-size: .72rem;
    color: #9ca3af;
    background: transparent;
    border: 1px solid transparent;
    cursor: pointer;
}
.nav-pill:hover {
    color: #c7d2fe;
    border-color: rgba(79,70,229,0.4);
    background: #020817;
}
.nav-pill.active {
    color: #e5e7eb;
    background: #111827;
    border-color: rgba(79,70,229,0.7);
    font-weight: 600;
}

/* Hero */
.hero-title {
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    background: linear-gradient(120deg,#60a5fa 0%,#a855f7 40%,#f97316 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: .15rem;
}
.hero-sub {
    font-size: .9rem;
    color: #9ca3af;
    max-width: 520px;
}

/* Cards */
.input-card,
.side-card,
.result-card {
    background: #050815;
    border-radius: 18px;
    border: 1px solid #111827;
    box-shadow: 0 18px 45px rgba(0,0,0,0.9);
}
.input-card {
    padding: 1rem 1rem .9rem;
}
.side-card {
    padding: .85rem .9rem .9rem;
    margin-bottom: .8rem;
}
.result-card {
    padding: 1rem 1rem 1.25rem;
    margin-top: .5rem;
}

/* File uploader */
[data-testid="stFileUploader"] section {
    border-radius: 14px;
    border: 1px dashed rgba(148,163,184,0.7);
    background: #020817;
    color: #9ca3af;
}

/* Text area & inputs */
.stTextArea textarea,
.stTextInput input {
    border-radius: 14px !important;
    border: 1px solid #374151 !important;
    font-size: .85rem !important;
    background: #020817 !important;
    color: #e5e7eb !important;
    padding: .7rem .8rem !important;
}
.stTextArea textarea:focus,
.stTextInput input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 1px rgba(99,102,241,0.35);
}

/* Selects, sliders, captions */
.stSelectbox div,
.stCaption,
.stMarkdown,
label {
    color: #e5e7eb !important;
}
.stSlider > div[data-baseweb="slider"] > div {
    background-color: #111827 !important;
}

/* Buttons */
.stButton button {
    border-radius: 999px !important;
    font-weight: 600 !important;
    font-size: .78rem !important;
    padding: 0.35rem 0.4rem !important;
    border: none !important;
    background: linear-gradient(135deg,#4f46e5,#7c3aed) !important;
    color: #ffffff !important;
    box-shadow: 0 18px 55px rgba(0,0,0,1);
    transition: all .18s ease-in-out;
}
.stButton button:hover {
    transform: translateY(-1px);
    box-shadow: 0 24px 70px rgba(0,0,0,1);
}
.stButton button:active {
    transform: translateY(1px);
    box-shadow: 0 10px 30px rgba(0,0,0,1);
}

/* Badges & stats */
.badge {
    display: inline-flex;
    align-items: center;
    gap: .25rem;
    padding: .22rem .7rem;
    border-radius: 999px;
    background: rgba(79,70,229,0.25);
    color: #e5e7eb;
    font-size: .7rem;
    font-weight: 600;
    margin-bottom: .4rem;
}
.stat-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0,1fr));
    gap: .5rem;
}
.stat-item {
    padding: .5rem .55rem;
    border-radius: 12px;
    border: 1px solid #111827;
    background: radial-gradient(circle at top,#111827,#020817);
}
.stat-title {
    font-size: .6rem;
    color: #9ca3af;
}
.stat-value {
    font-size: 1.05rem;
    font-weight: 700;
    color: #e5e7eb;
}

/* History */
.history-item {
    padding: .45rem .5rem;
    border-radius: 10px;
    background: #020817;
    border: 1px solid #111827;
    margin-bottom: .34rem;
}
.history-type {
    font-size: .7rem;
    font-weight: 600;
    color: #e5e7eb;
}
.history-time {
    font-size: .6rem;
    color: #6b7280;
}
.history-tag {
    font-size: .58rem;
    color: #9ca3af;
    font-style: italic;
}

/* Footer */
.footer {
    text-align: center;
    color: #6b7280;
    font-size: .7rem;
    padding-top: 1.2rem;
}

/* Anim */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
"""



# ---------- THEME TOGGLE UI ----------
with st.sidebar:
    st.write("")  # small spacing
    dark_toggle = st.toggle("🌙 Dark mode", value=(ss.theme == "dark"))
    ss.theme = "dark" if dark_toggle else "light"

# Inject theme CSS
if ss.theme == "dark":
    st.markdown(DARK_CSS, unsafe_allow_html=True)
else:
    st.markdown(LIGHT_CSS, unsafe_allow_html=True)

# ---------- SIDEBAR: SETTINGS + POMODORO ----------
with st.sidebar:
    # Response settings
    st.markdown("<div class='side-card'>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Response Settings", unsafe_allow_html=True)
    max_tokens = st.slider("Response length", 128, 1024, 300, 8)
    temperature = st.slider("Creativity", 0.0, 1.0, 0.5, 0.05)
    st.markdown("</div>", unsafe_allow_html=True)

    # Target level
    st.markdown("<div class='side-card'>", unsafe_allow_html=True)
    st.markdown("#### 🎓 Target Level", unsafe_allow_html=True)
    difficulty_level = st.selectbox(
        "Tune explanations & quizzes for:",
        ["Auto", "Beginner", "High School", "University", "Advanced"],
        index=0,
        label_visibility="collapsed",
    )
    st.caption("Current: " + difficulty_level)
    st.markdown("</div>", unsafe_allow_html=True)

    # Style preset
    st.markdown("<div class='side-card'>", unsafe_allow_html=True)
    st.markdown("#### ✍️ Style", unsafe_allow_html=True)
    style_preset = st.selectbox(
        "Preferred style:",
        ["Default", "Short & Direct", "Step-by-Step", "With Examples", "With Analogies"],
        index=0,
        label_visibility="collapsed",
    )
    st.caption("Current: " + style_preset)
    st.markdown("</div>", unsafe_allow_html=True)

    # Stats
    st.markdown("<div class='side-card'>", unsafe_allow_html=True)
    st.markdown("#### 📊 Your Stats", unsafe_allow_html=True)
    s = ss.stats
    st.markdown("<div class='stat-grid'>", unsafe_allow_html=True)
    for label, val in [
        ("Total", s["total"]),
        ("Summaries", s["summaries"]),
        ("Explanations", s["explanations"]),
        ("Quizzes", s["quizzes"]),
        ("Flashcards", s["flashcards"]),
    ]:
        st.markdown(
            f"<div class='stat-item'><div class='stat-title'>{label}</div>"
            f"<div class='stat-value'>{val}</div></div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Pomodoro timer
    st.markdown("<div class='side-card'>", unsafe_allow_html=True)
    st.markdown("#### ⏱️ Pomodoro Focus Timer", unsafe_allow_html=True)
    ss.pomo_focus_len = int(
        st.number_input("Focus (min)", min_value=10, max_value=90, value=ss.pomo_focus_len, step=5)
    )
    ss.pomo_break_len = int(
        st.number_input("Break (min)", min_value=3, max_value=30, value=ss.pomo_break_len, step=1)
    )

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("▶ Start", key="pomo_start"):
            ss.pomo_mode = "Focus"
            ss.pomo_running = True
            ss.pomo_end = datetime.now() + timedelta(minutes=ss.pomo_focus_len)
    with col_p2:
        if st.button("⏹ Reset", key="pomo_reset"):
            ss.pomo_running = False
            ss.pomo_end = None
            ss.pomo_mode = "Focus"

    # Display timer
    if ss.pomo_running and ss.pomo_end:
        remaining = ss.pomo_end - datetime.now()
        if remaining.total_seconds() <= 0:
            # Switch or stop
            if ss.pomo_mode == "Focus":
                ss.pomo_mode = "Break"
                ss.pomo_end = datetime.now() + timedelta(minutes=ss.pomo_break_len)
                st.success("Focus session complete. Break started! 🌿")
            else:
                ss.pomo_running = False
                ss.pomo_end = None
                ss.pomo_mode = "Focus"
                st.success("Break finished. Back to focus when you're ready ✨")
        if ss.pomo_running and ss.pomo_end:
            remaining = ss.pomo_end - datetime.now()
            total = int(remaining.total_seconds())
            mins, secs = divmod(max(total, 0), 60)
            st.markdown(
                f"<div style='font-size:1.6rem; font-weight:700; text-align:center; margin-top:.4rem;'>"
                f"{ss.pomo_mode}: {mins:02d}:{secs:02d}</div>",
                unsafe_allow_html=True,
            )
            # auto refresh
            time.sleep(1)
            st.experimental_rerun()
    else:
        st.caption("Set durations, press Start, and keep this tab open while you study.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Tips
    st.markdown("<div class='side-card'>", unsafe_allow_html=True)
    st.markdown("#### 💡 Study Tips", unsafe_allow_html=True)
    st.markdown("- Use Pomodoro for deep work on one topic.")
    st.markdown("- Generate quizzes after each focus block.")
    st.markdown("- Save PDFs for last-minute revision.")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- HELPERS ----------
def clean_text(text: str) -> str:
    text = text.replace("✅", "[OK]").replace("❌", "[ERROR]").replace("🤔", "")
    return text.encode("ascii", "ignore").decode("ascii")

def generate_pdf(input_text, output_text, action_type):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Smart Study Assistant", ln=True, align="C")
    pdf.ln(3)

    pdf.set_font("Arial", "I", 11)
    pdf.cell(0, 8, f"Type: {action_type}", ln=True, align="C")
    pdf.ln(2)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.ln(6)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 7, "Input:", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, clean_text(input_text))
    pdf.ln(3)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 7, "Output:", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, clean_text(output_text))

    return pdf.output(dest="S").encode("latin-1")

def get_download_link(pdf_data, filename):
    b64 = base64.b64encode(pdf_data).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{filename}" class="download-btn">📥 Download PDF</a>'

def call_chat(prompt: str) -> str:
    if not openai.api_key:
        return "❌ Error: OPENAI_API_KEY is missing. Set it in your .env file (not in GitHub)."
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert study assistant. Be clear, structured, and learner-friendly."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ Error: {e}"

def extract_text_from_file(uploaded_file) -> str:
    try:
        name = uploaded_file.name.lower()
        if name.endswith(".txt"):
            return uploaded_file.read().decode("utf-8", errors="ignore")
        if name.endswith(".pdf"):
            from PyPDF2 import PdfReader
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        if name.endswith(".docx"):
            import docx2txt
            tmp_path = os.path.join("/tmp", f"upload_{datetime.now().timestamp()}.docx")
            with open(tmp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            return docx2txt.process(tmp_path) or ""
    except Exception as e:
        st.error(f"Could not read file: {e}")
    return ""

def build_prompt(action: str, text: str, difficulty: str, style: str) -> str:
    level_hint = ""
    if difficulty == "Beginner":
        level_hint = "Explain as if to a complete beginner. "
    elif difficulty == "High School":
        level_hint = "Aim at an advanced high-school student. "
    elif difficulty == "University":
        level_hint = "Aim at a typical university student. "
    elif difficulty == "Advanced":
        level_hint = "Aim at an advanced learner; keep it rigorous. "

    style_hint = ""
    if style == "Short & Direct":
        style_hint = "Keep it concise and direct. "
    elif style == "Step-by-Step":
        style_hint = "Use a clear step-by-step structure with numbered steps. "
    elif style == "With Examples":
        style_hint = "Include simple, concrete examples. "
    elif style == "With Analogies":
        style_hint = "Use analogies and intuitive explanations. "

    base_prompts = {
        "Summarize": (
            "Summarize the following in 5-8 bullet points. Highlight key concepts, formulas, and definitions. "
        ),
        "Explain": (
            "Explain the following clearly using headings and short paragraphs. "
        ),
        "Quiz": (
            "Create 3 multiple-choice questions (A–D) from this content. "
            "After each question, include the correct answer on a new line starting with 'Answer:'. "
        ),
        "Flashcard": (
            "Create 5 flashcards strictly in this format:\nFRONT: ...\nBACK: ...\n"
        ),
    }

    prefix = base_prompts.get(action, "")
    meta = level_hint + style_hint
    return prefix + meta + "\n\n" + text

def handle_action(action: str, text: str, topic_label: str):
    if not text.strip():
        st.warning("⚠️ Please enter some text or upload a file first.")
        return

    prompt = build_prompt(action, text, difficulty_level, style_preset)

    with st.spinner(f"Generating your {action.lower()}..."):
        result = call_chat(prompt)

    ss.last_input = text
    ss.last_output = result
    ss.last_action = action

    # stats
    if action == "Summarize":
        ss.stats["summaries"] += 1
    elif action == "Explain":
        ss.stats["explanations"] += 1
    elif action == "Quiz":
        ss.stats["quizzes"] += 1
    elif action == "Flashcard":
        ss.stats["flashcards"] += 1
    ss.stats["total"] += 1

    # history
    tag = topic_label.strip() if topic_label.strip() else (
        text[:40] + ("..." if len(text) > 40 else "")
    )
    ss.history.append(
        {
            "topic": text[:110],
            "type": action,
            "content": result,
            "timestamp": datetime.now().strftime("%H:%M"),
            "tag": tag,
        }
    )

def render_quiz(output_text: str):
    blocks = [b.strip() for b in output_text.split("\n\n") if b.strip()]
    if not blocks:
        st.write(output_text)
        return
    for i, block in enumerate(blocks, start=1):
        if "Answer:" in block:
            q_part, ans = block.rsplit("Answer:", 1)
            st.markdown(f"**Q{i}.** {q_part.strip()}")
            with st.expander("Show answer", expanded=False):
                st.markdown(f"**Answer:** {ans.strip()}")
        else:
            st.markdown(block)

def render_flashcards(output_text: str):
    lines = [l for l in output_text.splitlines() if l.strip()]
    cards = []
    front, back = None, None
    for line in lines:
        if line.startswith("FRONT:"):
            if front or back:
                cards.append((front, back))
            front = line.replace("FRONT:", "").strip()
            back = None
        elif line.startswith("BACK:"):
            back = line.replace("BACK:", "").strip()
    if front or back:
        cards.append((front, back))

    if not cards:
        st.write(output_text)
        return

    for idx, (f_txt, b_txt) in enumerate(cards, start=1):
        st.markdown(f"**Card {idx}:** {f_txt}")
        with st.expander("Show answer", expanded=False):
            st.markdown(b_txt)

# ---------- MAIN UI ----------
st.markdown("<div class='app-shell'>", unsafe_allow_html=True)

# Topbar
st.markdown(
    """
<div class="topbar">
  <div class="brand">
    <div class="brand-icon">📚</div>
    <div>
        <div class="brand-title">Smart Study Assistant</div>
        <div class="brand-sub">AI summaries, explanations, quizzes & flashcards with focus tools built in.</div>
    </div>
  </div>
  <div class="nav-links">
    <div class="nav-pill active">Workspace</div>
    <div class="nav-pill">Recent</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# Layout
left, right = st.columns([1.55, 0.45])

with left:
    st.markdown(
        "<div class='hero-title'>AI study buddy with real UI energy.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='hero-sub'>Upload notes, tune your level & style, and turn raw content into clear, exam-ready outputs.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='input-card'>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "📂 Or upload a file (PDF, DOCX, TXT)",
        type=["pdf", "docx", "txt"],
        label_visibility="visible",
    )
    if uploaded_file is not None:
        extracted = extract_text_from_file(uploaded_file)
        if extracted:
            ss.uploaded_text = extracted
            st.success(
                f"Loaded content from `{uploaded_file.name}` "
                f"({len(extracted)} characters). You can edit it below."
            )

    topic_label = st.text_input(
        "🏷️ Topic label (optional)",
        placeholder="e.g. 'Data Structures midterm', 'Neural Networks intro', 'IELTS Reading'",
        key="topic_label",
    )

    default_text = (
        ss.uploaded_text
        if ss.last_input == "" and ss.uploaded_text
        else ss.last_input
    )

    user_text = st.text_area(
        "✍️ What are we working on?",
        height=190,
        placeholder="Paste your notes or type a topic, e.g. 'Explain overfitting and regularization'...",
        key="input_text",
        value=default_text,
    )

    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 0.9])
    with c1:
        if st.button("📋 Summarize", use_container_width=True):
            handle_action("Summarize", user_text, topic_label)
    with c2:
        if st.button("💡 Explain", use_container_width=True):
            handle_action("Explain", user_text, topic_label)
    with c3:
        if st.button("❓ Quiz Me", use_container_width=True):
            handle_action("Quiz", user_text, topic_label)
    with c4:
        if st.button("🃏 Flashcards", use_container_width=True):
            handle_action("Flashcard", user_text, topic_label)
    with c5:
        if st.button("🧹 Clear", use_container_width=True):
            ss.last_output = ""
            ss.last_action = ""
            ss.last_input = ""
            ss.uploaded_text = ""
            st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Output
    st.markdown("### 📤 Output")
    st.markdown("<div class='result-card'>", unsafe_allow_html=True)

    if ss.last_output:
        st.markdown(
            f"<div class='badge'>✅ {ss.last_action}</div>",
            unsafe_allow_html=True,
        )

        if ss.last_action == "Quiz":
            render_quiz(ss.last_output)
        elif ss.last_action == "Flashcard":
            render_flashcards(ss.last_output)
        else:
            st.write(ss.last_output)

        pdf_bytes = generate_pdf(
            ss.last_input or "",
            ss.last_output,
            ss.last_action,
        )
        link = get_download_link(
            pdf_bytes,
            f"{ss.last_action.lower()}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        )
        st.markdown(link, unsafe_allow_html=True)

        # Study path
        if ss.last_action in ["Summarize", "Explain"] and openai.api_key:
            with st.expander(
                "🎯 Suggested study path (what to learn next)", expanded=True
            ):
                roadmap_prompt = (
                    "Based on this topic/content, suggest a focused 5-step study roadmap "
                    "to fully understand and master it. Be concrete but concise:\n\n"
                    + (ss.last_input or "")
                )
                roadmap = call_chat(roadmap_prompt)
                st.markdown(roadmap)
    else:
        st.info("Paste content or upload a file above, then choose an action to see results here.")

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='side-card'>", unsafe_allow_html=True)
    st.markdown("#### 🌱 How to use", unsafe_allow_html=True)
    st.markdown("- Start with **Explain** for new topics.")
    st.markdown("- Use **Summarize** for compact notes.")
    st.markdown("- Use **Quiz Me** to test recall.")
    st.markdown("- Turn key ideas into **Flashcards**.")
    st.markdown("- Run Pomodoro blocks while studying each output.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='side-card'>", unsafe_allow_html=True)
    st.markdown("#### 🗂️ Recent activity", unsafe_allow_html=True)
    if ss.history:
        for item in reversed(ss.history[-7:]):
            st.markdown(
                f"""
            <div class='history-item'>
                <div class='history-type'>{item['type']} • <span class='history-time'>{item['timestamp']}</span></div>
                <div class='history-tag'>Tag: {item.get('tag','General')}</div>
                <div style='font-size:.66rem; margin-top:.14rem;'>{item['topic']}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        st.caption("No sessions yet. Your work will appear here.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
<div class='footer'>
    Built by Blessing · Smart Study Assistant · Light & Dark modes · Pomodoro-ready · API keys stay in .env 🔐
</div>
</div>
""",
    unsafe_allow_html=True,
)
