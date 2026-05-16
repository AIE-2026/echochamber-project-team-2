# scripts/build_vectorstore.py
# =============================
# Builds a FAISS vector index for each agent from data/bubbles/.
# Each agent gets its own index in assets/vectorstores/<slug>/
#
# HOW TO USE:
#   python scripts/build_vectorstore.py
#
# Prerequisites:
#   - data/bubbles/<slug>.jsonl exists for each agent defined in roles.yaml
#   - Each line in the JSONL has a "text" field
#
# Output:
#   assets/vectorstores/<slug>/index.faiss
#   assets/vectorstores/<slug>/index.pkl

# Import libraries for file handling, embeddings and FAISS indexing
from pathlib import Path
import json
import pickle

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import yaml


# Define source folders and embedding model
BUBBLES_DIR = Path("data/bubbles")
VECTORSTORE_DIR = Path("assets/vectorstores")
ROLES_PATH = Path("assets/roles/roles.yaml")

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


# Load multilingual embedding model
print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)


# Load all agents from roles.yaml
with open(ROLES_PATH, "r", encoding="utf-8") as f:
    roles_data = yaml.safe_load(f)

agents = roles_data["agents"]


# Iterate through all agent bubbles
for agent_slug in agents.keys():

    print(f"\n=== Processing agent: {agent_slug} ===")

    bubble_path = BUBBLES_DIR / f"{agent_slug}.jsonl"

    if not bubble_path.exists():
        print(f"Skipping missing file: {bubble_path}")
        continue

    metadata = []
    texts = []

    # Read JSONL fragments for the current agent
    with open(bubble_path, "r", encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            item = json.loads(line)

            if "text" not in item:
                continue

            texts.append(item["text"])
            metadata.append(item)

    if not texts:
        print(f"No texts found for {agent_slug}")
        continue

    print(f"Loaded {len(texts)} fragments")

    # Generate semantic embeddings for all fragments
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    # Convert embeddings to float32 format required by FAISS
    embeddings = np.array(embeddings).astype("float32")

    dimension = embeddings.shape[1]

    # Create FAISS index using cosine similarity
    index = faiss.IndexFlatIP(dimension)

    # Add embeddings into the FAISS index
    index.add(embeddings)

    output_dir = VECTORSTORE_DIR / agent_slug
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save FAISS index to disk
    faiss.write_index(index, str(output_dir / "index.faiss"))

    # Save metadata separately using pickle
    with open(output_dir / "index.pkl", "wb") as f:
        pickle.dump(metadata, f)

    # Print progress information
    print(f"Saved vectorstore for {agent_slug}")
    print(f"Vectors: {index.ntotal}")

print("\nAll vectorstores completed.")