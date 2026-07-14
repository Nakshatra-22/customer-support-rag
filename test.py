from rag import ask_question

history = []

answer, sources = ask_question(
    "Do you ship to India?",
    history
)

print(answer)
print(sources)