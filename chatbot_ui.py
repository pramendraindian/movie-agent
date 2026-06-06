from base64 import b64encode
from html import escape
from pathlib import Path

import requests
import streamlit as st


DEFAULT_API_URL = "http://localhost:8000/chat"
CSS_FILE = Path(__file__).with_name("chatbot_ui.css")
FILM_REEL_IMAGE = Path(__file__).parent / "assets" / "film_reel.svg"
CHAT_EMPTY_IMAGE = Path(__file__).parent / "assets" / "chat_empty.svg"


def configure_page() -> None:
    st.set_page_config(
        page_title="ChatBot",
        page_icon=":speech_balloon:",
        layout="centered",
    )


def load_css() -> None:
    if not CSS_FILE.exists():
        st.warning(f"Missing stylesheet: {CSS_FILE.name}")
        return

    css = CSS_FILE.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_dashboard_header() -> None:
    image_src = image_to_data_uri(FILM_REEL_IMAGE)

    st.markdown(
        f"""
        <section class="dashboard-hero">
            <img src="{image_src}" alt="Film reel" />
            <div>
                <h1>MoodFlix Movie Recommender</h1>
                <p>Discover films by mood, trending picks, available time, and your watch preferences.</p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def image_to_data_uri(path: Path) -> str:
    if path.exists():
        image_data = b64encode(path.read_bytes()).decode("ascii")
        image_src = f"data:image/svg+xml;base64,{image_data}"
    else:
        image_src = ""

    return image_src


def initialize_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("api_url", DEFAULT_API_URL)
    st.session_state.setdefault("chat_open", True)
    st.session_state.setdefault("chat_prompt", "")


def open_chat() -> None:
    st.session_state.chat_open = True


def minimize_chat() -> None:
    st.session_state.chat_open = False


def render_launcher() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] > .main,
        [data-testid="stMain"] {
            width: auto;
            height: auto;
            right: 0;
            bottom: 0;
            overflow: visible;
            background: transparent;
            border: 0;
            box-shadow: none;
        }

        [data-testid="stAppViewContainer"] > .main .block-container,
        [data-testid="stMainBlockContainer"] {
            padding: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.button(
        "Chat",
        key="open_chat",
        help="Open chat",
        on_click=open_chat,
    )


def render_header() -> None:
    title_column, action_column = st.columns([1, 0.16], vertical_alignment="center")

    with title_column:
        st.markdown(
            """
            <div class="chat-header">
                <div class="chat-avatar">AI</div>
                <div>
                    <h1>ChatBot</h1>
                    <p>FastAPI intent service</p>
                </div>
                <div class="chat-header-strip" aria-hidden="true">
                    <span></span><span></span><span></span><span></span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with action_column:
        st.button(
            "-",
            key="minimize_chat",
            help="Minimize chat",
            on_click=minimize_chat,
        )


def render_bubble(role: str, text: str, is_error: bool = False) -> None:
    safe_text = escape(text).replace("\n", "<br>")

    if role == "user":
        row_class = "user"
        avatar_class = "user"
        bubble_class = "user"
        avatar = "You"
    else:
        row_class = "bot"
        avatar_class = "bot"
        bubble_class = "error" if is_error else "bot"
        avatar = "AI"

    st.markdown(
        f"""
        <div class="bubble-row {row_class}">
            <div class="avatar {avatar_class}">{avatar}</div>
            <div class="bubble {bubble_class}">{safe_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    image_src = image_to_data_uri(CHAT_EMPTY_IMAGE)
    st.markdown(
        f"""
        <div class="empty-state">
            <img src="{image_src}" alt="" />
            <h2>Find the right movie faster</h2>
            <p>Try a mood, genre, trend, or how much time you have.</p>
            <div class="prompt-chips">
                <span>Relaxing</span>
                <span>Trending</span>
                <span>90 min</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_messages() -> None:
    with st.container(height=360, border=False):
        if not st.session_state.messages:
            render_empty_state()
            return

        for message in st.session_state.messages:
            render_bubble(
                message["role"],
                message["content"],
                message.get("error", False),
            )


def get_bot_reply(prompt: str) -> tuple[str, bool]:
    try:
        response = requests.post(
            st.session_state.api_url,
            json={"message": prompt},
            timeout=15,
        )
        response.raise_for_status()
        return response.json().get("response", "No response received."), False
    except requests.exceptions.ConnectionError:
        return "Could not connect to the backend. Is your FastAPI server running?", True
    except requests.exceptions.Timeout:
        return "The server took too long to respond. Please try again.", True
    except requests.exceptions.HTTPError as exc:
        return f"Server error: {exc.response.status_code}", True
    except Exception as exc:
        return f"Unexpected error: {exc}", True


def handle_prompt(prompt: str) -> None:
    if not prompt:
        return

    prompt = prompt.strip()
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    bot_reply, is_error = get_bot_reply(prompt)
    st.session_state.messages.append(
        {"role": "assistant", "content": bot_reply, "error": is_error}
    )


def submit_prompt() -> None:
    prompt = st.session_state.get("chat_prompt", "")
    handle_prompt(prompt)
    st.session_state.chat_prompt = ""


def render_composer() -> None:
    input_column, button_column = st.columns([1, 0.18], vertical_alignment="bottom")

    with input_column:
        st.text_input(
            "Message",
            key="chat_prompt",
            label_visibility="collapsed",
            placeholder="Type your message...",
            on_change=submit_prompt,
        )

    with button_column:
        st.button(
            "Send",
            key="send_message",
            use_container_width=True,
            on_click=submit_prompt,
        )


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Settings")
        st.session_state.api_url = st.text_input(
            "API Endpoint",
            value=st.session_state.api_url,
        )

        st.markdown("---")
        if st.button("Clear conversation"):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.markdown(f"**Messages:** {len(st.session_state.messages)}")
        status = "Open" if st.session_state.chat_open else "Minimized"
        st.markdown(f"**Status:** {status}")


def main() -> None:
    configure_page()
    load_css()
    initialize_state()
    render_sidebar()
    render_dashboard_header()

    if not st.session_state.chat_open:
        render_launcher()
        return

    render_header()
    render_messages()
    render_composer()


if __name__ == "__main__":
    main()
