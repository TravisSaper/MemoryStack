import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import json
import os
import argparse
import uuid
from datetime import datetime
file_path = os.path.dirname(os.path.abspath(__file__))
ind = file_path + "/memory_index.faiss"
mmp = file_path + "/memories.json"

@dataclass
class Memory:
    id: str
    content: str
    category: str
    importance: float
    timestamp: str
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict] = None

class VectorStore:
    def __init__(self, index_path=ind, memories_path=mmp):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
        self.index_path = index_path
        self.memories_path = memories_path
        self.index = faiss.IndexFlatIP(self.dimension)  
        self.memories = []
        self.load()
    
    def add_memory(self, memory:Memory):
        vector = self.model.encode(memory.content, normalize_embeddings=True) 
        vector = np.asarray(vector, dtype=np.float32).reshape(1, -1)
        memory.embedding = vector[0].tolist()
        self.index.add(vector)
        self.memories.append(memory)
        self.save()
        
    def search_similar(self, query: str, k: int = 5):
        if self.index.ntotal == 0:
            return []
        k = min(k, self.index.ntotal)
        vector = self.model.encode(query, normalize_embeddings=True)
        vector = np.asarray(vector, dtype=np.float32).reshape(1, -1)
        scores, indices = self.index.search(vector, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(self.memories):
                continue
            results.append({"memory": self.memories[idx], "score": float(score)})
    
        return results

    def delete_memory(self, memory_id: str):
        remaining = [memory for memory in self.memories if memory.id != memory_id]
        if len(remaining) == len(self.memories):
            return False
        self.memories = remaining
        self.index = faiss.IndexFlatIP(self.dimension)
        if self.memories:
            vectors = np.asarray([memory.embedding for memory in self.memories], dtype=np.float32)
            self.index.add(vectors)
        self.save()
        return True

    def save(self):
        faiss.write_index(self.index, self.index_path)
        data = [asdict(memory) for memory in self.memories]
        with open(self.memories_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            
        if os.path.exists(self.memories_path):
            with open(self.memories_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.memories = [Memory(**item) for item in data]


def importance_value(value):
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise argparse.ArgumentTypeError("importance must be between 0.0 and 1.0")
    return value


def format_memory(memory: Memory, score: Optional[float] = None):
    prefix = f"[{score:.3f}] " if score is not None else ""
    return (
        f"{prefix}{memory.id} | {memory.category} | "
        f"importance={memory.importance:.2f} | {memory.content}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["add", "search", "list", "delete"], required=True, help="Memory operation")
    parser.add_argument("--text", help="Memory text")
    parser.add_argument("--id", help="Memory ID")
    parser.add_argument("--category", help="Memory category, e.g. preference, personal, project, skill")
    parser.add_argument("--importance", type=importance_value, default=0.5, help="Importance from 0.0 to 1.0")
    parser.add_argument("-k", type=int, default=5, help="Number of search results")
    args = parser.parse_args()
    store = VectorStore()

    if args.mode == "add":
        if not args.text:
            parser.error("--text is required for add")

        memory = Memory(
            id=str(uuid.uuid4()),
            content=args.text,
            category=(args.category or "general").strip().lower(),
            importance=args.importance,
            timestamp=datetime.now().isoformat()
        )

        store.add_memory(memory)
        print(f"done {memory.id}")

    elif args.mode == "search":
        if not args.text:
            parser.error("--text is required for search")

        results = store.search_similar(args.text, k=args.k)

        for result in results:
            print(format_memory(result["memory"], result["score"]))

    elif args.mode == "list":
        memories = store.memories
        if args.category:
            memories = [memory for memory in memories if memory.category == args.category.strip().lower()]

        for memory in memories:
            print(format_memory(memory))

    elif args.mode == "delete":
        if not args.id:
            parser.error("--id must be there for delete")

        if store.delete_memory(args.id):
            print("Memory deleted.")
        else:
            print(f"No memory found with id {args.id}")


if __name__ == "__main__":
    main()
