import os
import time
import json
import base64
import datetime
import streamlit as st
from rag import ask_question_stream, RAGResult

# ----------------- PAGE CONFIGURATION ----------------- #
st.set_page_config(
    page_title="GigaCorp Customer Support Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- BASE64 BACKGROUND LOADER ----------------- #
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

bg_base64 = get_base64_of_bin_file("ai_background.png")

# ----------------- PREMIUM GLASSMORPHISM STYLE INJECTION ----------------- #
# Using a darker overlay (0.88 to 0.94) to ensure absolute WCAG AA readability contrast
if bg_base64:
    background_css = f"""
    .stApp {{
        background: linear-gradient(rgba(15, 23, 42, 0.88), rgba(15, 23, 42, 0.94)), url("data:image/png;base64,{bg_base64}") no-repeat center center fixed;
        background-size: cover;
    }}
    """
else:
    background_css = """
    .stApp {{
        background: radial-gradient(circle at top left, #1e1b4b 0%, #0f172a 60%, #311042 100%) no-repeat center center fixed;
        background-size: cover;
    }}
    """

st.markdown(f"""
<style>
{background_css}

/* Base fonts and overall theme typography */
html, body, [class*="css"] {{
    font-family: 'Outfit', 'Inter', -apple-system, sans-serif;
}}

/* Keyframes for futuristic page fade-in */
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(12px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

/* Force crisp, readable headings (WCAG AA Compliance) */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{
    color: #ffffff !important;
    font-weight: 700 !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4) !important;
}}

/* Force bright off-white color for body text to prevent blending */
.stApp p, .stApp li, .stApp span:not(.confidence-badge), .stApp label {{
    color: #f1f5f9 !important;
    font-weight: 400 !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
}}

/* Explicit Streamlit markdown container text overrides */
div[data-testid="stMarkdownContainer"] p {{
    color: #f1f5f9 !important;
    line-height: 1.6 !important;
}}
div[data-testid="stMarkdownContainer"] li {{
    color: #cbd5e1 !important;
}}
div[data-testid="stMarkdownContainer"] strong {{
    color: #ffffff !important;
    font-weight: 700 !important;
}}

/* Glassmorphism containers with higher opacity for text readability */
.welcome-card {{
    background: rgba(30, 41, 59, 0.65) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    margin-bottom: 1.25rem !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease !important;
    animation: fadeIn 0.5s ease-out forwards;
}}
.welcome-card:hover {{
    transform: translateY(-3px) !important;
    border-color: rgba(139, 92, 246, 0.5) !important;
    box-shadow: 0 12px 40px 0 rgba(139, 92, 246, 0.25) !important;
}}

/* Chat message bubbles styled as premium glass cards */
div[data-testid="stChatMessage"] {{
    background: rgba(30, 41, 59, 0.5) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 18px !important;
    padding: 1.25rem !important;
    margin-bottom: 1.1rem !important;
    box-shadow: 0 8px 24px 0 rgba(0, 0, 0, 0.22) !important;
    animation: fadeIn 0.4s ease-out forwards;
}}

/* Role-based selectors for chat bubbles */
div[data-testid="stChatMessage"][data-chat-message-role="user"] {{
    border-left: 3px solid #6366f1 !important;
    background: rgba(30, 41, 59, 0.4) !important;
}}
div[data-testid="stChatMessage"][data-chat-message-role="assistant"] {{
    border-left: 3px solid #d946ef !important;
    background: rgba(30, 41, 59, 0.6) !important;
}}

/* Timestamps for chat alignment */
.chat-timestamp {{
    font-size: 0.76rem;
    color: #cbd5e1 !important;
    opacity: 0.85;
    margin-top: 0.4rem;
    text-align: right;
    font-style: italic;
}}

/* Glowing confidence scores badges */
.confidence-badge {{
    padding: 0.3rem 0.8rem;
    border-radius: 50px;
    font-weight: 700 !important;
    font-size: 0.8rem;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
    letter-spacing: 0.5px;
}}
.confidence-high {{
    background-color: rgba(34, 197, 94, 0.18);
    color: #4ade80 !important;
    border: 1px solid rgba(34, 197, 94, 0.4);
}}
.confidence-medium {{
    background-color: rgba(234, 179, 8, 0.18);
    color: #facc15 !important;
    border: 1px solid rgba(234, 179, 8, 0.4);
}}
.confidence-low {{
    background-color: rgba(239, 68, 68, 0.18);
    color: #f87171 !important;
    border: 1px solid rgba(239, 68, 68, 0.4);
}}

/* Sidebar frosted overlay details */
section[data-testid="stSidebar"] {{
    background: rgba(15, 23, 42, 0.94) !important;
    backdrop-filter: blur(25px) !important;
    -webkit-backdrop-filter: blur(25px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}}

/* Sidebar text colors contrast adjustments */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] h5,
section[data-testid="stSidebar"] h6 {{
    color: #ffffff !important;
}}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] li,
section[data-testid="stSidebar"] span:not(.confidence-badge) {{
    color: #e2e8f0 !important;
}}
section[data-testid="stSidebar"] label {{
    color: #f8fafc !important;
    font-weight: 600 !important;
}}

/* Sidebar stat cards */
.stat-card {{
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px;
    padding: 0.8rem;
    margin-bottom: 0.65rem;
    font-size: 0.85rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
}}

/* Premium gradient action buttons with strong white text */
div.stButton > button {{
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    padding: 0.55rem 1.1rem !important;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.25) !important;
    transition: all 0.25s ease !important;
    width: 100%;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4) !important;
}}
div.stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(168, 85, 247, 0.5) !important;
    border-color: rgba(255, 255, 255, 0.35) !important;
}}

/* Glassmorphism expanders styled for source cards */
div[data-testid="stExpander"] {{
    background: rgba(30, 41, 59, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
    margin-bottom: 0.75rem !important;
}}

/* Textarea input configuration */
textarea[aria-label="Type your question here..."] {{
    background: rgba(30, 41, 59, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    color: #ffffff !important;
    border-radius: 12px !important;
}}

/* Ensure context extraction code displays clearly */
div[data-testid="stExpander"] code {{
    color: #e2e8f0 !important;
    background-color: rgba(15, 23, 42, 0.75) !important;
}}

/* Custom styles to make HTML / Markdown tables readable */
.stApp table {{
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 1.2rem 0 !important;
    background: rgba(30, 41, 59, 0.5) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
}}
.stApp th {{
    background: rgba(99, 102, 241, 0.35) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    padding: 0.8rem 1rem !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    text-align: left !important;
}}
.stApp td {{
    padding: 0.8rem 1rem !important;
    color: #f1f5f9 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
}}
.stApp tr:nth-child(even) {{
    background: rgba(255, 255, 255, 0.03) !important;
}}

/* Professional footer layout */
.custom-footer {{
    text-align: center;
    padding-top: 3rem;
    padding-bottom: 1.5rem;
    font-size: 0.82rem;
    color: #cbd5e1;
    opacity: 0.8;
    border-top: 1px solid rgba(128, 128, 128, 0.15);
    margin-top: 5rem;
}}
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE INITIALIZATION ----------------- #
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "suggested_question" not in st.session_state:
    st.session_state.suggested_question = None

# ----------------- HELPER EXPORT LOGS FUNCTIONS ----------------- #
def export_chat_txt():
    output = []
    output.append("GigaCorp Customer Support Assistant - Conversation Log")
    output.append("===================================================\n")
    for m in st.session_state.messages:
        timestamp = m.get("timestamp", "")
        role = m["role"].upper()
        content = m["content"]
        output.append(f"[{timestamp}] {role}:")
        output.append(content)
        if role == "ASSISTANT":
            confidence = m.get("confidence", 0)
            output.append(f"Confidence Level: {confidence}%")
            sources = m.get("sources", [])
            if sources:
                output.append("Sources Retrieved:")
                for s in sources:
                    output.append(f" - {s['file']} | Section: {s['section']}")
        output.append("-" * 40 + "\n")
    return "\n".join(output)

def export_chat_json():
    return json.dumps(st.session_state.messages, indent=2)

# ----------------- SIDEBAR INTERFACE ----------------- #
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding-bottom: 1.5rem;">
        <h1 style="font-size: 2.2rem; margin: 0; font-weight: 800; background: linear-gradient(135deg, #a5b4fc 0%, #c084fc 50%, #f472b6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">🤖 GigaCorp</h1>
        <span style="font-size: 0.8rem; opacity: 0.95; font-weight: 600; letter-spacing: 1px; color: #cbd5e1; text-shadow: 0 1px 2px rgba(0,0,0,0.5);">SAAS SUPPORT CONSOLE</span>
    </div>
    """, unsafe_allow_html=True)

    # API key controller
    api_key_set = bool(os.getenv("GROQ_API_KEY"))
    if not api_key_set:
        st.warning("⚠️ GROQ_API_KEY environment variable is not configured.")
        user_key = st.text_input("Provide Groq API Key:", type="password", key="sidebar_key_input")
        if user_key:
            os.environ["GROQ_API_KEY"] = user_key
            st.success("API key loaded temporarily!")
            st.rerun()
    
    st.divider()

    # Session stats compilation
    user_queries = sum(1 for m in st.session_state.messages if m["role"] == "user")
    res_times = [m["response_time"] for m in st.session_state.messages if "response_time" in m]
    conf_scores = [m["confidence"] for m in st.session_state.messages if "confidence" in m]
    
    avg_res_time = round(sum(res_times) / len(res_times), 2) if res_times else 0.0
    avg_conf = round(sum(conf_scores) / len(conf_scores), 1) if conf_scores else 0.0

    st.markdown("### 📊 Dashboard Metrics")
    st.markdown(f"""
    <div class="stat-card">
        <strong>Total Queries:</strong> {user_queries}<br/>
        <strong>Memory History:</strong> {len(st.session_state.chat_history)} turns<br/>
        <strong>Avg Response Time:</strong> {avg_res_time}s<br/>
        <strong>Avg Confidence:</strong> {avg_conf}%<br/>
        <strong>Buffer Status:</strong> <span style="color: #4ade80; font-weight: bold;">{'Active' if len(st.session_state.chat_history) > 0 else 'Idle'}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚙️ System Specifications")
    st.markdown("""
    <div class="stat-card" style="font-size: 0.8rem; line-height: 1.45;">
        <strong>LLM model:</strong> <code>llama-3.3-70b-versatile</code><br/>
        <strong>Vector database:</strong> <code>FAISS (Local Store)</code><br/>
        <strong>Embeddings:</strong> <code>all-MiniLM-L6-v2</code><br/>
        <strong>Retrieved Chunks:</strong> <code>3</code>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🛠 Technology Stack")
    st.markdown("""
    - **Language:** Python
    - **UI Engine:** Streamlit 1.x
    - **Orchestration:** LangChain 1.3.13
    - **Vector store:** FAISS
    - **Vector models:** Sentence Transformers
    """)

    st.markdown("### 🎛 Controls")
    col_clear, col_reset = st.columns(2)
    with col_clear:
        if st.button("🗑 Clear Chat", use_container_width=True, help="Clear message history and conversation memory"):
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.toast("Chat history cleared!", icon="🧹")
            st.rerun()
    with col_reset:
        if st.button("🔄 Reset App", use_container_width=True, help="Reset session state variables"):
            st.session_state.clear()
            st.toast("Session reset successfully!", icon="🔄")
            st.rerun()

    # Chat exporter controls
    if len(st.session_state.messages) > 0:
        st.markdown("### 📥 Export Conversations")
        txt_output = export_chat_txt()
        st.download_button(
            label="📄 Download Logs (.txt)",
            data=txt_output,
            file_name=f"gigacorp_chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        json_output = export_chat_json()
        st.download_button(
            label="⚙️ Download Logs (.json)",
            data=json_output,
            file_name=f"gigacorp_chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

    st.divider()
    st.markdown("""
    <div style="font-size: 0.76rem; opacity: 0.85; text-align: center; line-height: 1.45; color: #cbd5e1;">
        <strong>GigaCorp Support Portal v1.0.0</strong><br/>
        Internship Portfolio Assignment<br/>
        <a href="#" style="text-decoration:none; color:#c084fc;">🔗 GitHub Project</a> | <a href="#" style="text-decoration:none; color:#c084fc;">🔗 LinkedIn Profile</a>
    </div>
    """, unsafe_allow_html=True)

# ----------------- MAIN TITLE HEADER ----------------- #
st.markdown("""
<div style="padding-bottom: 2rem; text-align: left; animation: fadeIn 0.6s ease-out;">
    <h1 style="font-size: 2.8rem; font-weight: 800; margin: 0; line-height: 1.2; background: linear-gradient(135deg, #a5b4fc 0%, #c084fc 50%, #f472b6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 2px 8px rgba(0,0,0,0.5);">
        GigaCorp Customer Support Portal
    </h1>
    <p style="font-size: 1.15rem; color: #e2e8f0; margin-top: 0.35rem; margin-bottom: 0; text-shadow: 0 1px 2px rgba(0,0,0,0.5);">Enterprise AI assistant for business policies, shipping matrices, and custom SLAs.</p>
</div>
""", unsafe_allow_html=True)

# ----------------- WELCOME SCREEN (When chat is empty) ----------------- #
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-card">
        <h3 style="color: #c084fc; font-weight: 700; margin-bottom: 0.5rem;">👋 Welcome to our Support Assistant</h3>
        <p style="margin: 0; line-height: 1.6; color: #f1f5f9;">
            I retrieve and answer questions directly from GigaCorp's verified Operating and FAQ indexes. 
            Use the input console below or launch one of our suggestions to view the retrieval system in action.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🗂 Browse FAQ Directories")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="welcome-card">
            <h4 style="color: #818cf8; font-weight: 600; margin-bottom: 0.5rem;">📦 Shipping & Logistics</h4>
            <p style="font-size: 0.92rem; color: #e2e8f0; line-height: 1.5; margin: 0;">
                Details international shipping matrices (India, USA, UK, Germany, Singapore, etc.). 
                Compare base shipping rates (e.g. $10 - $25) and shipping transit periods.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="welcome-card">
            <h4 style="color: #818cf8; font-weight: 600; margin-bottom: 0.5rem;">🕒 Operating Availability</h4>
            <p style="font-size: 0.92rem; color: #e2e8f0; line-height: 1.5; margin: 0;">
                Support hours run Monday to Friday (9:00 AM to 6:00 PM IST) 
                and Saturday (10:00 AM to 2:00 PM IST). Sunday closed.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="welcome-card">
            <h4 style="color: #818cf8; font-weight: 600; margin-bottom: 0.5rem;">🔄 Returns & Refund Terms</h4>
            <p style="font-size: 0.92rem; color: #e2e8f0; line-height: 1.5; margin: 0;">
                Items can be returned within 30 days of delivery. 
                Products must remain unused, fully packaged in original boxes, and include all accessories.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="welcome-card">
            <h4 style="color: #818cf8; font-weight: 600; margin-bottom: 0.5rem;">⭐ Service Tier Benefits</h4>
            <p style="font-size: 0.92rem; color: #e2e8f0; line-height: 1.5; margin: 0;">
                Details features across Basic (FAQ and email support), Premium (live chat, faster delivery), 
                and Enterprise (24/7 dedicated support, SLA contracts) plans.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 💡 Quick Launch Suggestions")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("📦 Do you ship to India?", key="p1_btn_new", use_container_width=True):
            st.session_state.suggested_question = "Do you ship to India?"
            st.rerun()
        if st.button("⭐ Compare GigaCorp service plans", key="p2_btn_new", use_container_width=True):
            st.session_state.suggested_question = "Compare GigaCorp service plans"
            st.rerun()
    with col_p2:
        if st.button("🔄 What is the return policy?", key="p3_btn_new", use_container_width=True):
            st.session_state.suggested_question = "What is the return policy?"
            st.rerun()
        if st.button("🕒 What are GigaCorp support hours?", key="p4_btn_new", use_container_width=True):
            st.session_state.suggested_question = "What are GigaCorp support hours?"
            st.rerun()

# ----------------- DISPLAY PREVIOUS CONVERSATION MESSAGES ----------------- #
for message in st.session_state.messages:
    is_user = message["role"] == "user"
    avatar_char = "👤" if is_user else "🤖"
    with st.chat_message(message["role"], avatar=avatar_char):
        st.markdown(message["content"])
        st.markdown(f'<div class="chat-timestamp">{message.get("timestamp", "")}</div>', unsafe_allow_html=True)
        
        # Display meta details if assistant message
        if not is_user:
            confidence = message.get("confidence", 0)
            if confidence >= 75:
                st.markdown(f'<span class="confidence-badge confidence-high">🟢 High Confidence ({confidence}%)</span>', unsafe_allow_html=True)
            elif confidence >= 50:
                st.markdown(f'<span class="confidence-badge confidence-medium">🟡 Medium Confidence ({confidence}%)</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="confidence-badge confidence-low">🔴 Low Confidence ({confidence}%)</span>', unsafe_allow_html=True)
            
            sources = message.get("sources", [])
            if sources:
                st.markdown("<div style='margin-top:0.75rem; font-weight:600; color:#c084fc; font-size:0.9rem;'>📚 Retrieved Source Cards</div>", unsafe_allow_html=True)
                for idx, src in enumerate(sources, start=1):
                    src_score = src.get("score", 0)
                    if src_score >= 75:
                        src_badge = f'<span class="confidence-badge confidence-high">🟢 High ({src_score}%)</span>'
                    elif src_score >= 50:
                        src_badge = f'<span class="confidence-badge confidence-medium">🟡 Medium ({src_score}%)</span>'
                    else:
                        src_badge = f'<span class="confidence-badge confidence-low">🔴 Low ({src_score}%)</span>'

                    with st.expander(f"📄 {src['file']} — Section: {src['section']}"):
                        st.markdown(f"**📌 Section:** *{src['section']}*")
                        st.markdown(f"**🎯 Matching Confidence:** {src_badge}", unsafe_allow_html=True)
                        st.markdown(f"**📖 Context Extract:**")
                        st.code(src['content'], language="text")

# ----------------- USER INPUT FIELD ----------------- #
chat_input_val = st.chat_input("Type your question here...")

# Handle suggested prompt click
active_query = None
if chat_input_val:
    active_query = chat_input_val
elif st.session_state.suggested_question:
    active_query = st.session_state.suggested_question
    st.session_state.suggested_question = None  # Clear prompt trigger

# ----------------- INCOMING QUERY PROCESSING ----------------- #
if active_query:
    # 1. Render & save user question
    user_time = datetime.datetime.now().strftime("%I:%M %p")
    st.session_state.messages.append({
        "role": "user",
        "content": active_query,
        "timestamp": user_time
    })
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(active_query)
        st.markdown(f'<div class="chat-timestamp">{user_time}</div>', unsafe_allow_html=True)

    # Check key configuration
    if not os.getenv("GROQ_API_KEY"):
        with st.chat_message("assistant", avatar="🤖"):
            st.error("❌ Groq API Key is not configured. Please supply an API key in the sidebar configuration.")
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Groq API Key is not configured. Please supply an API key in the sidebar configuration.",
                "timestamp": datetime.datetime.now().strftime("%I:%M %p"),
                "confidence": 0,
                "sources": [],
                "response_time": 0.0
            })
        st.rerun()

    # 2. RAG retrieval visualization using st.status()
    try:
        t_start = time.time()
        
        with st.status("🔍 Querying GigaCorp Knowledge Base...", expanded=True) as search_status:
            search_status.write("🧠 Rephrasing question for pronoun/contextual resolution...")
            # Prepare generation stream
            stream_gen, sources, confidence = ask_question_stream(active_query, st.session_state.chat_history)
            
            search_status.write("📚 Retrieving corresponding documents from FAISS indices...")
            search_status.write("📊 Calculating relevance scores and filtering duplicates...")
            search_status.update(label="✅ Retrieval and optimization complete!", state="complete", expanded=False)

        # 3. Stream assistant reply
        with st.chat_message("assistant", avatar="🤖"):
            response_container = st.empty()
            accumulated_response = ""
            for text_chunk in stream_gen:
                accumulated_response += text_chunk
                response_container.markdown(accumulated_response + "▌")
            response_container.markdown(accumulated_response)

            t_end = time.time()
            elapsed_time = round(t_end - t_start, 2)

            # If response fallback occurs, force confidence level to 0
            if "couldn't find that information" in accumulated_response.lower():
                confidence = 0

            # Render confidence score badge
            if confidence >= 75:
                st.markdown(f'<span class="confidence-badge confidence-high">🟢 High Confidence ({confidence}%)</span>', unsafe_allow_html=True)
            elif confidence >= 50:
                st.markdown(f'<span class="confidence-badge confidence-medium">🟡 Medium Confidence ({confidence}%)</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="confidence-badge confidence-low">🔴 Low Confidence ({confidence}%)</span>', unsafe_allow_html=True)

            # Render expandable sources list
            if sources:
                st.markdown("<div style='margin-top:0.75rem; font-weight:600; color:#c084fc; font-size:0.9rem;'>📚 Retrieved Source Cards</div>", unsafe_allow_html=True)
                for idx, src in enumerate(sources, start=1):
                    src_score = src.get("score", 0)
                    if src_score >= 75:
                        src_badge = f'<span class="confidence-badge confidence-high">🟢 High ({src_score}%)</span>'
                    elif src_score >= 50:
                        src_badge = f'<span class="confidence-badge confidence-medium">🟡 Medium ({src_score}%)</span>'
                    else:
                        src_badge = f'<span class="confidence-badge confidence-low">🔴 Low ({src_score}%)</span>'

                    with st.expander(f"📄 {src['file']} — Section: {src['section']}"):
                        st.markdown(f"**📌 Section:** *{src['section']}*")
                        st.markdown(f"**🎯 Matching Confidence:** {src_badge}", unsafe_allow_html=True)
                        st.markdown(f"**📖 Context Extract:**")
                        st.code(src['content'], language="text")

            assistant_time = datetime.datetime.now().strftime("%I:%M %p")
            st.markdown(f'<div class="chat-timestamp">{assistant_time}</div>', unsafe_allow_html=True)

        # 4. Save response to session state & history
        st.session_state.messages.append({
            "role": "assistant",
            "content": accumulated_response,
            "timestamp": assistant_time,
            "confidence": confidence,
            "sources": sources,
            "response_time": elapsed_time
        })
        st.session_state.chat_history.append((active_query, accumulated_response))

        # Show feedback toast
        st.toast(f"Answer generated in {elapsed_time}s! 🚀", icon="✅")
        
        # Rerun to cleanly draw session metrics in sidebar
        st.rerun()

    except Exception as e:
        error_time = datetime.datetime.now().strftime("%I:%M %p")
        with st.chat_message("assistant", avatar="🤖"):
            st.error(f"❌ Core processing error encountered: {e}")
            st.markdown(f'<div class="chat-timestamp">{error_time}</div>', unsafe_allow_html=True)
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Core processing error encountered: {e}",
                "timestamp": error_time,
                "confidence": 0,
                "sources": [],
                "response_time": 0.0
            })
        st.toast("Failed to generate response.", icon="❌")

# ----------------- FOOTER ----------------- #
st.markdown("""
<div class="custom-footer">
    🤖 Powered by LangChain, Groq (llama-3.3-70b-versatile) & FAISS local database.<br/>
    Developed for GigaCorp Internship Showcase • Version 1.0.0
</div>
""", unsafe_allow_html=True)