import os
os.environ["HF_HOME"] = "/app/.cache/huggingface"

from sentence_transformers import SentenceTransformer
print("[ML] baixando modelo multilingual...")
SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print("[ML] modelo salvo.")
