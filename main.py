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
from filelock import FileLock

file_path = os.path.dirname(os.path.abspath(__file__))
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
    def __init__(self, memories_path=mmp):
        self.model = SentenceTransformer("all-mpnet-base-v2")
        self.dimension = 768
        self.memories_path = memories_path
        self.lock = FileLock(memories_path + ".lock")
        self.index = faiss.IndexFlatIP(self.dimension)
        self.memories = []
        self.loaded_version = None
        with self.lock:
            self.load()

    def add_memory(self, memory):
        vector = self.model.encode(memory.content, normalize_embeddings=True)
        vector = np.asarray(vector, dtype=np.float32).reshape(1, -1)
        memory.embedding = vector[0].tolist()
        with self.lock:
            self.load()
            self.index.add(vector)
            self.memories.append(memory)
            self.save()

    def search_similar(self, query, k=5):
        self.refresh()
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

    def list_memories(self):
        self.refresh()
        return self.memories

    def delete_memory(self, memory_id):
        with self.lock:
            self.load()
            remaining = [m for m in self.memories if m.id != memory_id]
            if len(remaining) == len(self.memories):
                return False
            self.memories = remaining
            self.build_index()
            self.save()
        return True

    def build_index(self):
        self.index = faiss.IndexFlatIP(self.dimension)
        if self.memories:
            self.index.add(np.asarray([m.embedding for m in self.memories], dtype=np.float32))

    def file_version(self):
        try:
            st = os.stat(self.memories_path)
        except FileNotFoundError:
            return None
        return (st.st_ino, st.st_mtime_ns, st.st_size)

    def save(self):
        data = [asdict(memory) for memory in self.memories]
        tmp_path = self.memories_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, self.memories_path)
        self.loaded_version = self.file_version()

    def load(self):
        version = self.file_version()
        if version is None:
            self.memories = []
        else:
            with open(self.memories_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.memories = [Memory(**item) for item in data]
        self.build_index()
        self.loaded_version = version

    def refresh(self):
        if self.file_version() != self.loaded_version:
            with self.lock:
                self.load()

def importance_value(value):
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise argparse.ArgumentTypeError("importance must be between 0.0 and 1.0")
    return value

def format_memory(memory, score=None):
    prefix = f"[{score:.3f}] " if score is not None else ""
    return f"{prefix}{memory.id} | {memory.category} | importance={memory.importance:.2f} | {memory.content}"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["add", "search", "list", "delete"], required=True, help="Memory operation")
    parser.add_argument("--text", help="Memory text")
    parser.add_argument("--id", help="Memory ID")
    parser.add_argument("--category", help="Memory category")
    parser.add_argument("--importance", type=importance_value, default=0.5, help="Importance 0.0 to 1.0")
    parser.add_argument("-k", type=int, default=5, help="Number of results")
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

        for result in store.search_similar(args.text, k=args.k):
            print(format_memory(result["memory"], result["score"]))

    elif args.mode == "list":
        mems = store.list_memories()
        if args.category:
            mems = [m for m in mems if m.category == args.category.strip().lower()]
        for m in mems:
            print(format_memory(m))

    elif args.mode == "delete":
        if not args.id:
            parser.error("--id must be there for delete")
        if store.delete_memory(args.id):
            print("Memory deleted.")
        else:
            print(f"No memory found with id {args.id}")

if __name__ == "__main__":
    main()
