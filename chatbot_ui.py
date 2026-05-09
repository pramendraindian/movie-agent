import streamlit as st
import requests

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ChatBot",
    page_icon="💬",
    layout="centered",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap');

/* ── Root palette ── */
:root {
    --bg:        #0e0f13;
    --surface:   #16181f;
    --border:    #2a2d38;
    --accent:    #6ee7b7;       /* mint green */
    --accent2:   #38bdf8;       /* sky blue  */
    --txt:       #e8eaf0;
    --txt-muted: #6b7280;
    --user-bg:   #1e3a2f;
    --bot-bg:    #1a1c24;
    --radius:    14px;
    --font-body: 'DM Sans', sans-serif;
    --font-head: 'DM Serif Display', serif;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    font-family: var(--font-body);
    color: var(--txt);
}

/* hide Streamlit chrome */
#MainMenu, header, footer { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── App wrapper ── */
[data-testid="stAppViewContainer"] > .main {
    max-width: 760px;
    margin: 0 auto;
    padding: 2rem 1.5rem 7rem;
}

/* ── Header ── */
.chat-header {
    text-align: center;
    padding: 2.5rem 0 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}
.chat-header h1 {
    font-family: var(--font-head);
    font-size: 2.4rem;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    letter-spacing: -0.5px;
}
.chat-header p {
    color: var(--txt-muted);
    font-size: 0.9rem;
    margin: 0.4rem 0 0;
}

/* ── Chat bubbles ── */
.bubble-row {
    display: flex;
    align-items: flex-end;
    gap: 10px;
    margin-bottom: 1.1rem;
    animation: fadeUp 0.25s ease both;
}
.bubble-row.user  { flex-direction: row-reverse; }

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

.avatar {
    width: 34px; height: 34px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
}
.avatar.bot  { background: linear-gradient(135deg, var(--accent), var(--accent2)); color: #0e0f13; }
.avatar.user { background: var(--border); }

.bubble {
    max-width: 72%;
    padding: 0.75rem 1.1rem;
    border-radius: var(--radius);
    font-size: 0.95rem;
    line-height: 1.6;
    word-break: break-word;
    position: relative;
}
.bubble.bot {
    background: var(--bot-bg);
    border: 1px solid var(--border);
    border-bottom-left-radius: 4px;
    color: var(--txt);
}
.bubble.user {
    background: var(--user-bg);
    border: 1px solid #2a4a3a;
    border-bottom-right-radius: 4px;
    color: var(--accent);
}

/* ── Typing indicator ── */
.typing { display: flex; gap: 5px; align-items: center; padding: 4px 0; }
.typing span {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--accent);
    animation: blink 1.2s infinite ease-in-out;
}
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink {
    0%,80%,100% { opacity: 0.2; transform: scale(0.8); }
    40%         { opacity: 1;   transform: scale(1); }
}

/* ── Input bar ── */
[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 0; left: 50%;
    transform: translateX(-50%);
    width: min(760px, 100%);
    background: var(--surface) !important;
    border-top: 1px solid var(--border) !important;
    padding: 0.75rem 1.5rem 1rem !important;
    z-index: 999;
}
[data-testid="stChatInput"] textarea {
    background: var(--bg) !important;
    color: var(--txt) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: var(--font-body) !important;
    font-size: 0.95rem !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(110,231,183,0.15) !important;
}
[data-testid="stChatInputSubmitButton"] svg { color: var(--accent) !important; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 4rem 0;
    color: var(--txt-muted);
}
.empty-state .icon { font-size: 3rem; margin-bottom: 0.75rem; }
.empty-state p { font-size: 0.95rem; }

/* ── Error bubble ── */
.bubble.error {
    background: #2d1515;
    border-color: #5c2828;
    color: #f87171;
}
</style>
""", unsafe_allow_html=True)

# ── Config ────────────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000/chat"   # ← change if your server runs elsewhere

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="chat-header">
  <h1>💬 ChatBot</h1>
  <p>Powered by your FastAPI intent service</p>
</div>
""", unsafe_allow_html=True)

# ── Render history ─────────────────────────────────────────────────────────────
def render_bubble(role: str, text: str, is_error: bool = False):
    if role == "user":
        st.markdown(f"""
        <div class="bubble-row user">
            <div class="avatar user">🧑</div>
            <div class="bubble user">{text}</div>
        </div>""", unsafe_allow_html=True)
    else:
        bubble_cls = "error" if is_error else "bot"
        st.markdown(f"""
        <div class="bubble-row bot">
            <div class="avatar bot">✦</div>
            <div class="bubble {bubble_cls}">{text}</div>
        </div>""", unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">✦</div>
        <p>Send a message to get started.</p>
    </div>""", unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        render_bubble(msg["role"], msg["content"], msg.get("error", False))

# ── Input & API call ──────────────────────────────────────────────────────────
if prompt := st.chat_input("Type your message…"):
    # Validate: skip blank messages
    prompt = prompt.strip()
    if not prompt:
        st.stop()

    # Show user bubble
    st.session_state.messages.append({"role": "user", "content": prompt})
    render_bubble("user", prompt)

    # Typing indicator while waiting
    typing_placeholder = st.empty()
    typing_placeholder.markdown("""
    <div class="bubble-row bot">
        <div class="avatar bot">✦</div>
        <div class="bubble bot">
            <div class="typing"><span></span><span></span><span></span></div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Call FastAPI backend
    try:
        resp = requests.post(API_URL, json={"message": prompt}, timeout=15)
        resp.raise_for_status()
        bot_reply = resp.json().get("response", "No response received.")
        is_error  = False
    except requests.exceptions.ConnectionError:
        bot_reply = "⚠️ Could not connect to the backend. Is your FastAPI server running?"
        is_error  = True
    except requests.exceptions.Timeout:
        bot_reply = "⚠️ The server took too long to respond. Please try again."
        is_error  = True
    except requests.exceptions.HTTPError as e:
        bot_reply = f"⚠️ Server error: {e.response.status_code}"
        is_error  = True
    except Exception as e:
        bot_reply = f"⚠️ Unexpected error: {str(e)}"
        is_error  = True

    typing_placeholder.empty()
    st.session_state.messages.append({"role": "assistant", "content": bot_reply, "error": is_error})
    render_bubble("assistant", bot_reply, is_error)

# ── Sidebar: controls ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_url_input = st.text_input("API Endpoint", value=API_URL)
    if api_url_input != API_URL:
        API_URL = api_url_input

    st.markdown("---")
    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown(f"**Messages:** {len(st.session_state.messages)}")
    st.markdown("**Status:** 🟢 Ready")
