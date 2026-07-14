import os
import time
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

# Custom result class that behaves as a 2-tuple (answer, sources) for compatibility,
# but also exposes a .confidence attribute.
class RAGResult(tuple):
    def __new__(cls, answer, sources, confidence):
        return tuple.__new__(cls, (answer, sources))

    def __init__(self, answer, sources, confidence):
        self.confidence = confidence

# Conditional cache decorator to ensure safety when run from raw python scripts like test.py
def conditional_cache_resource(func):
    try:
        import streamlit as st
        if st.runtime.exists():
            return st.cache_resource(func)
    except Exception:
        pass
    return func

@conditional_cache_resource
def get_embeddings():
    """Initializes and caches the Hugging Face embeddings model."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

@conditional_cache_resource
def get_vectorstore():
    """Initializes and caches the local FAISS vector store database."""
    if not os.path.exists("vectorstore"):
        raise FileNotFoundError(
            "Vector store 'vectorstore' directory not found. Please run ingest.py first."
        )
    embeddings = get_embeddings()
    return FAISS.load_local(
        "vectorstore",
        embeddings,
        allow_dangerous_deserialization=True
    )

@conditional_cache_resource
def get_llm():
    """Initializes and caches the ChatGroq model."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing. Please add it to your .env file.")
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        groq_api_key=api_key
    )

def get_standalone_question(question, chat_history):
    """
    Uses the ChatGroq model to rephrase the current follow-up question
    into a standalone question, using the conversational history.
    """
    if not chat_history:
        return question

    history_str = ""
    for human, ai in chat_history:
        history_str += f"User: {human}\nAssistant: {ai}\n"

    rephrase_prompt = f"""Given the following conversation history and a follow-up question, rephrase the follow-up question to be a standalone question (in English) that can be understood without context. Do NOT answer the question. If it does not refer to the conversation history, return the follow-up question exactly as is.

Conversation History:
{history_str}

Follow-up Question: {question}
Standalone Question:"""

    try:
        llm = get_llm()
        response = llm.invoke(rephrase_prompt)
        standalone = response.content.strip()
        # Strip outer quotes if returned by the model
        if standalone.startswith('"') and standalone.endswith('"'):
            standalone = standalone[1:-1]
        return standalone
    except Exception:
        # Fallback to simple concatenation if the rephrasing request fails
        return f"{chat_history[-1][0]} {question}"

def ask_question_stream(question, chat_history):
    """
    Main RAG logic: Rephrases query, retrieves context from FAISS,
    deduplicates sources, calculates similarity distance confidence,
    and returns a streaming generator along with sources and confidence.
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    # 1. Get stand-alone search query
    standalone_query = get_standalone_question(question, chat_history)

    # 2. Load vectorstore & perform search
    vectorstore = get_vectorstore()
    
    # Retrieve top 3 documents with scores
    docs_and_scores = vectorstore.similarity_search_with_score(standalone_query, k=3)

    # 3. Deduplicate docs based on content
    seen_content = set()
    unique_docs_and_scores = []
    for doc, score in docs_and_scores:
        content = doc.page_content.strip()
        if content not in seen_content:
            seen_content.add(content)
            unique_docs_and_scores.append((doc, score))

    # Format sources for return with individual chunk similarity scores
    sources = []
    for doc, score in unique_docs_and_scores:
        similarity = 1.0 - (score / 2.0)
        chunk_conf = int(max(0.0, min(1.0, similarity)) * 100)
        sources.append({
            "file": doc.metadata.get("source", "faq.txt"),
            "section": doc.metadata.get("section", "General"),
            "content": doc.page_content,
            "score": chunk_conf
        })

    # 4. Calculate confidence percentage based on best matching score
    # Cosine Similarity is approximated as 1 - (L2_distance / 2.0)
    if unique_docs_and_scores:
        best_score = unique_docs_and_scores[0][1]
        similarity = 1.0 - (best_score / 2.0)
        confidence_pct = int(max(0.0, min(1.0, similarity)) * 100)
    else:
        confidence_pct = 0

    # 5. Build prompt with retrieved context
    history_str = ""
    for human, ai in chat_history:
        history_str += f"User: {human}\nAssistant: {ai}\n"

    context = "\n\n".join(doc.page_content for doc, _ in unique_docs_and_scores)

    system_prompt = f"""You are GigaCorp's expert customer support assistant.

Answer the user's question professionally, concisely, and clearly. Follow these instructions:
1. Answer ONLY using the information in the provided Context. Do NOT use any external knowledge.
2. If the answer is not present in the Context, reply exactly: "I couldn't find that information in the knowledge base."
3. Keep the response short, direct, and well-structured.
4. Use bullet points or numbered lists where appropriate for readability.
5. Highlight key information (like prices, hours, or names) in bold.
6. Maintain a helpful and polite tone.

Conversation History:
{history_str}

Context:
{context}

Current Question: {question}
Answer:"""

    # 6. Stream generator
    llm = get_llm()
    
    def response_generator():
        try:
            stream = llm.stream(system_prompt)
            for chunk in stream:
                yield chunk.content
        except Exception as e:
            yield f"\n[Generation Error: {e}]"

    return response_generator(), sources, confidence_pct

def ask_question(question, chat_history):
    """
    Main compatibility wrapper function. Iterates the stream generator
    into a string and returns a backwards-compatible RAGResult tuple.
    """
    try:
        generator, sources, confidence = ask_question_stream(question, chat_history)
        answer = "".join(list(generator))
        
        # If model outputs the fallback reply, force confidence level to 0
        if "couldn't find that information" in answer.lower():
            confidence = 0
            
        return RAGResult(answer, sources, confidence)
    except Exception as e:
        error_msg = f"I couldn't find that information in the knowledge base. (Error: {e})"
        return RAGResult(error_msg, [], 0)