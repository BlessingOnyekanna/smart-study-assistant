import streamlit as st
import openai
import os
from dotenv import load_dotenv
from datetime import datetime
from fpdf import FPDF
import base64

load_dotenv()

st.set_page_config(
    page_title="Smart Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    .main-header {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1.5rem 0;
        animation: fadeInDown 0.8s ease-in;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.3rem;
        margin-bottom: 2rem;
        animation: fadeIn 1s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        border: 2px solid transparent;
        font-size: 1rem;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        border: 2px solid #667eea;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        border-left: 5px solid #667eea;
        transition: all 0.3s ease;
        margin: 0.5rem 0;
    }
    
    .stat-card:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .stat-card h2 {
        color: #667eea;
        font-size: 2.5rem;
        margin: 0;
        font-weight: 700;
    }
    
    .stat-card p {
        color: #666;
        margin: 0;
        font-size: 0.9rem;
    }
    
    .download-btn {
        display: inline-block;
        padding: 1rem 2rem;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        text-decoration: none;
        border-radius: 12px;
        font-weight: 600;
        margin: 1rem 0;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .download-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
        text-decoration: none;
    }
    
    .stTextArea textarea {
        border-radius: 12px;
        border: 2px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border: 2px solid #667eea;
        box-shadow: 0 0 15px rgba(102, 126, 234, 0.2);
    }
    
    .tip-box {
        background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%);
        border-left: 4px solid #667eea;
        padding: 1.5rem;
        border-radius: 12px;
        animation: slideInRight 0.8s ease;
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .success-badge {
        display: inline-block;
        background: #28a745;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        margin: 0.5rem 0;
    }
    
    div[data-testid="stExpander"] {
        background: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Setup OpenAI API (old syntax for openai==0.28.1)
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    st.error("⚠️ No API key found. Create a `.env` file with `OPENAI_API_KEY=...`")
    st.stop()

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "stats" not in st.session_state:
    st.session_state.stats = {
        "summaries": 0,
        "explanations": 0,
        "quizzes": 0,
        "flashcards": 0,
        "total": 0
    }

# Header
st.markdown('<h1 class="main-header">📚 Smart Study Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-Powered Learning Made Simple</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    max_tokens = st.slider("Response Length", 128, 512, 300, 10)
    temperature = st.slider("Creativity Level", 0.0, 1.0, 0.5, 0.1)
    
    st.divider()
    
    st.header("📊 Your Study Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="stat-card"><h2>{st.session_state.stats["total"]}</h2><p>Total Sessions</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-card"><h2>{len(st.session_state.history)}</h2><p>History Items</p></div>', unsafe_allow_html=True)
    
    st.divider()
    
    st.header("🗂️ Recent History")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history[-5:])):
            with st.expander(f"📝 {item['type']} - {item['timestamp']}"):
                st.caption(item['topic'][:100] + "...")
    else:
        st.caption("No history yet. Start studying!")
    
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.history = []
        st.session_state.stats = {"summaries": 0, "explanations": 0, "quizzes": 0, "flashcards": 0, "total": 0}
        st.rerun()

# Main content
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📝 Enter Your Study Material")
    user_input = st.text_area(
        "Paste text, notes, or enter a topic:",
        height=250,
        placeholder="Example: 'Explain photosynthesis' or paste your lecture notes here...",
        label_visibility="collapsed"
    )
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        summarize_btn = st.button("📋 Summarize", use_container_width=True)
    with col2:
        explain_btn = st.button("💡 Explain", use_container_width=True)
    with col3:
        quiz_btn = st.button("❓ Quiz Me", use_container_width=True)
    with col4:
        flashcard_btn = st.button("🃏 Flashcards", use_container_width=True)
    with col5:
        clear_btn = st.button("🧹 Clear", use_container_width=True)

with col_right:
    st.subheader("💡 Quick Tips")
    
    st.markdown("#### 📚 How to Use")
    
    st.markdown("**📋 Summarize**  \nGet key points from lengthy text in seconds")
    
    st.markdown("**💡 Explain**  \nBreak down complex topics into simple terms")
    
    st.markdown("**❓ Quiz Me**  \nTest your understanding with AI-generated questions")
    
    st.markdown("**🃏 Flashcards**  \nGenerate study flashcards with Q&A format")
    
    st.markdown("**📥 Download**  \nSave any result as a PDF for offline study")
    
    st.divider()
    
    st.markdown("#### 🎯 Pro Tips")
    st.markdown("""
    - Be specific in your questions
    - Paste full paragraphs for better summaries
    - Adjust creativity for varied responses
    - Use Quiz mode to reinforce learning
    """)

def call_chat(user_prompt):
    """Call OpenAI API using old syntax"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert study assistant. Provide clear, structured, and helpful responses."},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ Error: {str(e)}"

def create_pdf(title, content, action_type):
    """Generate PDF from content"""
    import re
    
    # Remove emojis and special unicode characters
    def clean_text(text):
        # Remove emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r'', text)
        
        # Replace common problematic characters
        text = text.replace('❌', '[ERROR]')
        text = text.replace('✅', '[SUCCESS]')
        text = text.replace('🤔', '')
        
        # Keep only ASCII-compatible characters
        text = text.encode('ascii', 'ignore').decode('ascii')
        return text
    
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "Smart Study Assistant", ln=True, align="C")
    pdf.ln(5)
    
    # Action type
    pdf.set_font("Arial", "I", 12)
    pdf.cell(0, 10, f"Type: {action_type}", ln=True, align="C")
    pdf.ln(5)
    
    # Date
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.ln(10)
    
    # Input section
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Input:", ln=True)
    pdf.set_font("Arial", "", 11)
    clean_title = clean_text(title[:500])
    pdf.multi_cell(0, 5, clean_title)
    pdf.ln(5)
    
    # Output section
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Output:", ln=True)
    pdf.set_font("Arial", "", 11)
    clean_content = clean_text(content)
    pdf.multi_cell(0, 5, clean_content)
    
    return pdf.output(dest='S').encode('latin-1')

def get_download_link(pdf_data, filename):
    """Generate download link for PDF"""
    b64 = base64.b64encode(pdf_data).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{filename}" class="download-btn">📥 Download PDF</a>'

def handle_action(action, text):
    """Process user request"""
    if not text.strip():
        st.warning("⚠️ Please enter some text or a topic first!")
        return
    
    # Define prompts
    prompts = {
        "Summarize": f"Provide a clear, concise summary of the following in 5-7 key points:\n\n{text}",
        "Explain": f"Explain the following topic in simple, beginner-friendly terms with examples:\n\n{text}",
        "Quiz": f"Create 3 multiple-choice quiz questions about the following topic. For each question, provide 4 options (A-D) and indicate the correct answer at the end:\n\n{text}",
        "Flashcard": f"Create 5 flashcards about the following topic. For each flashcard, provide:\n- Front: A question or key term\n- Back: The answer or definition\n\nFormat each flashcard clearly with 'FRONT:' and 'BACK:' labels.\n\nTopic:\n{text}"
    }
    
    with st.spinner(f"🤔 Processing your {action.lower()} request..."):
        result = call_chat(prompts[action])
        
        # Display result with badge
        st.markdown(f'<span class="success-badge">✅ {action} Complete!</span>', unsafe_allow_html=True)
        st.markdown("---")
        st.success(result)
        
        # Generate PDF and download link
        pdf_data = create_pdf(text, result, action)
        filename = f"{action.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        st.markdown(get_download_link(pdf_data, filename), unsafe_allow_html=True)
        
        st.balloons()  # Celebration animation!
        
        # Update stats with correct keys
        if action == "Summarize":
            st.session_state.stats["summaries"] += 1
        elif action == "Explain":
            st.session_state.stats["explanations"] += 1
        elif action == "Quiz":
            st.session_state.stats["quizzes"] += 1
        elif action == "Flashcard":
            st.session_state.stats["flashcards"] += 1
        
        st.session_state.stats["total"] += 1
        
        # Save to history
        st.session_state.history.append({
            "topic": text[:100],
            "type": action,
            "content": result,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

# Handle button clicks
if clear_btn:
    st.rerun()

if user_input:
    if summarize_btn:
        handle_action("Summarize", user_input)
    elif explain_btn:
        handle_action("Explain", user_input)
    elif quiz_btn:
        handle_action("Quiz", user_input)
    elif flashcard_btn:
        handle_action("Flashcard", user_input)
else:
    if summarize_btn or explain_btn or quiz_btn or flashcard_btn:
        st.warning("⚠️ Please enter some text or a topic first!")

# History display at bottom
if st.session_state.history:
    st.divider()
    st.subheader("📚 Study Session History")
    
    for i, item in enumerate(reversed(st.session_state.history[:10]), start=1):
        with st.expander(f"{i}. {item['type']} - {item['timestamp']}"):
            st.markdown("**Input:**")
            st.text(item["topic"])
            st.markdown("**Output:**")
            st.write(item["content"])

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>© 2025 Blessing Onyekanna | Built with ❤️ using Streamlit + OpenAI</p>
    <p>⭐ <a href='https://github.com/BlessingOnyekanna/smart-study-assistant' target='_blank'>Star on GitHub</a></p>
</div>
""", unsafe_allow_html=True)