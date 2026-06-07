from base64 import b64encode
from html import escape
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components


DEFAULT_API_URL = "http://localhost:8000/chat"
CSS_FILE = Path(__file__).with_name("chatbot_ui.css")
FILM_REEL_IMAGE = Path(__file__).parent / "assets" / "film_reel.svg"
CHAT_EMPTY_IMAGE = Path(__file__).parent / "assets" / "chat_empty.svg"
POSTER_URLS = [
    "https://image.tmdb.org/t/p/w342/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg",
    "https://image.tmdb.org/t/p/w342/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
    "https://image.tmdb.org/t/p/w342/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
    "https://image.tmdb.org/t/p/w342/8UlWHLMpgZm9bx6QYh0NFoq67TZ.jpg",
    "https://image.tmdb.org/t/p/w342/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg",
    "https://image.tmdb.org/t/p/w342/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
    "https://image.tmdb.org/t/p/w342/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg",
    "https://image.tmdb.org/t/p/w342/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
]
PROMPT_SUGGESTIONS = [
    ("Relaxing", "relaxing movies"),
    ("Trending", "trending movies"),
    ("90 min", "90 min movies"),
]


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


def render_movie_marquee() -> None:
    poster_items = "".join(
        f'<img src="{poster_url}" alt="Movie poster" loading="lazy" />'
        for poster_url in POSTER_URLS
    )

    st.markdown(
        f"""
        <section class="poster-marquee poster-marquee-top" aria-hidden="true">
            <div class="poster-track">{poster_items}{poster_items}</div>
        </section>
        <section class="poster-marquee poster-marquee-bottom" aria-hidden="true">
            <div class="poster-track reverse">{poster_items}{poster_items}</div>
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
    st.session_state.setdefault("pending_prompt", "")


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
                    <p>Movie recommendation assistant</p>
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


def format_bot_response(text: str) -> str:
    if "|" not in text:
        return escape(text).replace("\n", "<br>")

    parts = [part.strip() for part in text.split("|") if part.strip()]
    if not parts:
        return escape(text).replace("\n", "<br>")

    intro = ""
    first_suggestion = parts[0]
    if ":" in first_suggestion:
        intro, first_suggestion = first_suggestion.split(":", 1)
        intro = intro.strip()
        first_suggestion = first_suggestion.strip()

    suggestions = [first_suggestion, *parts[1:]]
    suggestions = [suggestion for suggestion in suggestions if suggestion]
    if len(suggestions) < 2:
        return escape(text).replace("\n", "<br>")

    intro_html = f"<p>{escape(intro)}:</p>" if intro else ""
    suggestions_html = "".join(
        f"<li>{escape(suggestion)}</li>" for suggestion in suggestions
    )
    return f'{intro_html}<ul class="suggestion-list">{suggestions_html}</ul>'


def render_bubble(role: str, text: str, is_error: bool = False) -> None:
    if role == "user":
        row_class = "user"
        avatar_class = "user"
        bubble_class = "user"
        avatar = "You"
        bubble_content = escape(text).replace("\n", "<br>")
    else:
        row_class = "bot"
        avatar_class = "bot"
        bubble_class = "error" if is_error else "bot"
        avatar = "AI"
        bubble_content = escape(text).replace("\n", "<br>") if is_error else format_bot_response(text)

    st.markdown(
        f"""
        <div class="bubble-row {row_class}">
            <div class="avatar {avatar_class}">{avatar}</div>
            <div class="bubble {bubble_class}">{bubble_content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_movie_cards(movies: list[dict]) -> None:
    if not movies:
        return

    cards_html = []
    for movie in movies:
        title = escape(str(movie.get("title", "Unknown")))
        rating = movie.get("rating", 0)
        runtime = escape(str(movie.get("runtime", "")))
        year = escape(str(movie.get("release_year", "")))
        poster_url = escape(str(movie.get("poster_url", "")))
        poster_path = escape(str(movie.get("poster_path", "")))

        meta_parts = []
        try:
            rating_value = float(rating)
        except (TypeError, ValueError):
            rating_value = 0
        if rating_value:
            meta_parts.append(f"{rating_value:.1f}/10")
        if runtime:
            meta_parts.append(runtime)
        if year:
            meta_parts.append(year)
        meta = escape(" | ".join(meta_parts))

        poster_html = (
            f'<img src="{poster_url}" alt="{title} poster" loading="lazy" />'
            if poster_url
            else '<div class="movie-poster-placeholder">No poster</div>'
        )

        cards_html.append(
            f"""
            <article class="movie-card">
                <div class="movie-poster">{poster_html}</div>
                <div class="movie-card-body">
                    <h3>{title}</h3>
                    <p>{meta}</p>
                </div>
            </article>
            """
        )

    st.markdown(
        f'<div class="movie-card-grid">{"".join(cards_html)}</div>',
        unsafe_allow_html=True,
    )


def render_typing_indicator() -> None:
    st.markdown(
        """
        <div class="bubble-row bot">
            <div class="avatar bot">AI</div>
            <div class="bubble bot typing-bubble" aria-label="Waiting for response">
                <span></span><span></span><span></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def send_suggestion(prompt: str) -> None:
    handle_prompt(prompt)


def render_empty_state() -> None:
    image_src = image_to_data_uri(CHAT_EMPTY_IMAGE)
    st.markdown(
        f"""
        <div class="empty-state">
            <img src="{image_src}" alt="" />
            <h2>Find the right movie faster</h2>
            <p>Try a mood, genre, trend, or how much time you have.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    chip_columns = st.columns(len(PROMPT_SUGGESTIONS))
    for index, (label, prompt) in enumerate(PROMPT_SUGGESTIONS):
        with chip_columns[index]:
            st.button(
                label,
                key=f"prompt_chip_{index}",
                help=f"Ask for {label.lower()} movie recommendations",
                use_container_width=True,
                on_click=send_suggestion,
                args=(prompt,),
            )


def render_messages() -> None:
    with st.container(height=360, border=False):
        if not st.session_state.messages:
            render_empty_state()
        else:
            for message in st.session_state.messages:
                render_bubble(
                    message["role"],
                    message["content"],
                    message.get("error", False),
                )
                if message["role"] == "assistant" and not message.get("error", False):
                    render_movie_cards(message.get("movies", []))

        if st.session_state.pending_prompt:
            render_typing_indicator()


def get_bot_reply(prompt: str) -> tuple[str, bool, list[dict]]:
    try:
        response = requests.post(
            st.session_state.api_url,
            json={"message": prompt},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        if "movies" not in payload:
            legacy_response = payload.get("response", "No response received.")
            return (
                legacy_response
                + "\n\nBackend returned the old response format without movie/poster data. Restart the FastAPI backend.",
                False,
                [],
            )
        return (
            payload.get("response", "No response received."),
            False,
            payload.get("movies", []),
        )
    except requests.exceptions.ConnectionError:
        return "Could not connect to the backend. Is your FastAPI server running?", True, []
    except requests.exceptions.Timeout:
        return "The server took too long to respond. Please try again.", True, []
    except requests.exceptions.HTTPError as exc:
        return f"Server error: {exc.response.status_code}", True, []
    except Exception as exc:
        return f"Unexpected error: {exc}", True, []


def handle_prompt(prompt: str) -> None:
    if not prompt:
        return

    prompt = prompt.strip()
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.pending_prompt = prompt


def submit_prompt() -> None:
    prompt = st.session_state.get("chat_prompt", "")
    handle_prompt(prompt)
    st.session_state.chat_prompt = ""


def resolve_pending_prompt() -> None:
    prompt = st.session_state.pending_prompt
    if not prompt:
        return

    bot_reply, is_error, movies = get_bot_reply(prompt)
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": bot_reply,
            "error": is_error,
            "movies": movies,
        }
    )
    st.session_state.pending_prompt = ""
    st.rerun()


def render_composer() -> None:
    is_waiting = bool(st.session_state.pending_prompt)
    input_column, button_column = st.columns([1, 0.18], vertical_alignment="bottom")

    with input_column:
        st.text_area(
            "Message",
            key="chat_prompt",
            label_visibility="collapsed",
            placeholder="Waiting for reply..." if is_waiting else "Type your message...",
            disabled=is_waiting,
            height=68,
        )

    with button_column:
        st.button(
            "Send",
            key="send_message",
            use_container_width=True,
            disabled=is_waiting,
            on_click=submit_prompt,
        )


def enable_enter_to_send() -> None:
    components.html(
        """
        <script>
        const parentDoc = window.parent.document;

        function bindEnterToSend() {
            const textarea = parentDoc.querySelector('.st-key-chat_prompt textarea');
            const sendButton = parentDoc.querySelector('.st-key-send_message button');

            if (!textarea || !sendButton || textarea.dataset.enterToSendBound === 'true') {
                return;
            }

            textarea.dataset.enterToSendBound = 'true';
            textarea.addEventListener('keydown', (event) => {
                if (event.key !== 'Enter' || event.shiftKey || event.ctrlKey || event.metaKey || event.altKey) {
                    return;
                }

                event.preventDefault();
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                textarea.dispatchEvent(new Event('change', { bubbles: true }));
                setTimeout(() => sendButton.click(), 0);
            });
        }

        bindEnterToSend();
        const observer = new MutationObserver(bindEnterToSend);
        observer.observe(parentDoc.body, { childList: true, subtree: true });
        </script>
        """,
        height=0,
        width=0,
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
            st.session_state.pending_prompt = ""
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
    render_movie_marquee()
    render_dashboard_header()

    if not st.session_state.chat_open:
        render_launcher()
        return

    render_header()
    render_messages()
    render_composer()
    enable_enter_to_send()
    resolve_pending_prompt()


if __name__ == "__main__":
    main()
