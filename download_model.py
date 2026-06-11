from sentence_transformers import SentenceTransformer
import os

cache = os.path.expanduser("~/.cache/huggingface")
print(f"[ML] baixando modelo para {cache}...")
SentenceTransformer("paraphrase-MiniLM-L3-v2")
print("[ML] modelo salvo com sucesso.")