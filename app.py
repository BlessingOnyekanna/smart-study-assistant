# app.py — Smart Study Assistant
# Requires: streamlit==1.32.2, openai==0.28.1, python-dotenv
import os
import streamlit as st
from dotenv import load_dotenv
import openai

# ---- Setup ----
load_dotenv()  # loads variables from .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Smart Study Assistant", page_icon="📚", layout="centered")
st.title("📚 Smart Study Assistant")
st.caption("Summarize or explain topics clearly — powered by AI.")

# Guardrails for missing API key
if not OPENAI_API_KEY:
    st.error("No API key found. Create a `.env` file with `OPENAI_API_KEY=...` and restart.")
    st.stop()

openai.api_key = OPENAI_API_KEY

# ---- Sidebar (options) ----
with st.sidebar:
    st.subheader("Settings")
    model = st.selectbox("Model", ["gpt-3.5-turbo"], index=0)
    max_tokens = st.slider("Max tokens", min_value=128, max_value=512, value=250, step=10)
    temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.4, 0.1)
    st.markdown("---")
    st.caption("Tip: Keep inputs focused. For long articles, paste one section at a time.")

# ---- Session state for history ----
if "history" not in st.session_state:
    st.session_state.history = []   # list of dicts: {action, prompt, output}

# ---- UI ----
user_input = st.text_area("✍🏽 Enter text or a question:", height=200, placeholder="Paste a paragraph or ask a question…")

col1, col2, col3 = st.columns([1,1,1])
summarize = col1.button("🔎 Summarize", use_container_width=True)
explain   = col2.button("💡 Explain Simply", use_container_width=True)
clear     = col3.button("🧹 Clear", use_container_width=True)

def call_chat(user_prompt: str) -> str:
    """Call OpenAI ChatCompletion (compatible with openai==0.28.1)."""
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a clear, student-friendly study assistant. Use concise, structured explanations."},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp["choices"][0]["message"]["content"].strip()

def handle(action: str, text: str):
    if not text.strip():
        st.warning("Please type or paste something first.")
        return
    with st.spinner(f"{action}…"):
        try:
            if action == "Summarize":
                prompt = f"Summarize the following text in 5–7 sentences. Keep key terms:\n\n{text}"
            else:  # Explain Simply
                prompt = (
                    "Explain the following topic clearly for a beginner. "
                    "Use simple examples and plain language. "
                    "If there are formulas or jargon, define them first.\n\n"
                    f"{text}"
                )
            out = call_chat(prompt)
            st.success(out)
            # Save to history
            st.session_state.history.insert(0, {"action": action, "prompt": text, "output": out})
        except Exception as e:
            st.error(f"Error: {e}")

if summarize:
    handle("Summarize", user_input)
elif explain:
    handle("Explain Simply", user_input)
elif clear:
    st.session_state.history.clear()
    st.experimental_rerun()

# ---- History panel ----
if st.session_state.history:
    st.markdown("### 🗂️ Recent Results")
    for i, item in enumerate(st.session_state.history[:5], start=1):
        with st.expander(f"{i}. {item['action']} result"):
            st.markdown("**Input:**")
            st.write(item["prompt"])
            st.markdown("**Output:**")
            st.write(item["output"])

# ---- Footer ----
st.markdown("---")
st.caption("© 2025 Blessing Onyekanna — Smart Study Assistant. Built with Streamlit + OpenAI.")
