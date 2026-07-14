from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

print("Loading FAQ document...")

# Load FAQ
loader = TextLoader("faq.txt", encoding="utf-8")
documents = loader.load()

# Split into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50
)

docs = splitter.split_documents(documents)

# Add metadata
for doc in docs:
    text = doc.page_content.lower()

    section = "General"

    if "shipping" in text:
        section = "Shipping Policy"
    elif "return" in text or "refund" in text:
        section = "Return Policy"
    elif "business hours" in text or "customer support hours" in text:
        section = "Business Hours"
    elif "basic plan" in text or "premium plan" in text or "enterprise plan" in text:
        section = "Service Tiers"
    elif "contact information" in text or "email" in text or "phone" in text:
        section = "Contact Information"

    doc.metadata = {
        "source": "faq.txt",
        "section": section
    }

print(f"Created {len(docs)} document chunks.")

# Embedding model
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Create vector database
db = FAISS.from_documents(docs, embeddings)

# Save locally
db.save_local("vectorstore")

print("✅ FAISS vector database created successfully!")