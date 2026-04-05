#!/usr/bin/env python3
"""
MAILMAN Chat - Semantic Search + RAG across all email accounts and meetings.

Fyxer parity: "Fyxer Chat" instant answers from inbox + meetings
Beyond Fyxer: Vector embeddings, cross-account search, contact context,
              meeting action items, relationship intelligence, time-aware queries

How it works:
1. Indexes emails into a local ChromaDB vector database
2. On query, finds semantically similar emails (not just keyword match)
3. Feeds retrieved context to Claude for a grounded answer
4. Supports natural language queries like:
   - "What did Brandon say about the Q4 budget?"
   - "When is the next meeting with the design team?"
   - "Find that email about the venue for the fundraiser"
   - "What action items do I have from last week?"

Usage:
  python3 mailman_chat.py --index <account>    # Index emails into vector DB
  python3 mailman_chat.py --query "<question>"  # Ask a question
  python3 mailman_chat.py --reindex             # Rebuild the full index
  python3 mailman_chat.py --stats               # Show index stats
"""

import json
import argparse
import hashlib
import sys
from datetime import datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Missing: pip install anthropic --break-system-packages")
    sys.exit(1)

MAILMAN_ROOT = Path(__file__).parent.parent
MEMORY_DIR = MAILMAN_ROOT / "_memory"
DATA_DIR = MAILMAN_ROOT / "_memory" / "vector_db"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ChromaDB is optional -- falls back to simple TF-IDF if not installed
CHROMA_AVAILABLE = False
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    pass


class MailmanChat:
    """
    RAG-powered conversational search across all email accounts.
    Uses ChromaDB for vector storage when available, falls back to
    a simple inverted index for basic keyword + semantic matching.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.index_path = MEMORY_DIR / "email_index.json"

        if CHROMA_AVAILABLE:
            self.chroma_client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(DATA_DIR),
                anonymized_telemetry=False,
            ))
            self.collection = self.chroma_client.get_or_create_collection(
                name="mailman_emails",
                metadata={"hnsw:space": "cosine"},
            )
            self.use_vectors = True
            print("Using ChromaDB vector search.")
        else:
            self.use_vectors = False
            self.index = self._load_index()
            print("ChromaDB not available. Using keyword index fallback.")

    def _load_index(self):
        if self.index_path.exists():
            with open(self.index_path) as f:
                return json.load(f)
        return {"documents": {}, "updated_at": None}

    def _save_index(self):
        self.index["updated_at"] = datetime.utcnow().isoformat()
        with open(self.index_path, "w") as f:
            json.dump(self.index, f, indent=2)

    def index_emails(self, emails, account_name="default"):
        """
        Index a batch of emails for search.

        Args:
            emails: List of email dicts from GmailClient
            account_name: Account identifier for cross-account search
        """
        indexed = 0
        skipped = 0

        for email in emails:
            email_id = email.get("id", "")
            if not email_id:
                skipped += 1
                continue

            # Build searchable document
            doc_text = self._build_document(email, account_name)
            if not doc_text or len(doc_text) < 20:
                skipped += 1
                continue

            doc_id = f"{account_name}_{email_id}"

            if self.use_vectors:
                # ChromaDB indexing
                metadata = {
                    "account": account_name,
                    "sender": email.get("sender_email", ""),
                    "sender_name": email.get("sender_name", ""),
                    "subject": (email.get("subject", "") or "")[:200],
                    "date": email.get("date", ""),
                    "thread_id": email.get("thread_id", ""),
                    "has_attachments": str(bool(email.get("attachments"))),
                    "message_id": email_id,
                }
                try:
                    self.collection.upsert(
                        ids=[doc_id],
                        documents=[doc_text[:5000]],  # ChromaDB doc size limit
                        metadatas=[metadata],
                    )
                    indexed += 1
                except Exception as e:
                    print(f"Index error for {email_id}: {e}")
                    skipped += 1
            else:
                # Fallback keyword index
                self.index["documents"][doc_id] = {
                    "text": doc_text[:5000],
                    "sender": email.get("sender_email", ""),
                    "sender_name": email.get("sender_name", ""),
                    "subject": email.get("subject", ""),
                    "date": email.get("date", ""),
                    "account": account_name,
                    "message_id": email_id,
                }
                indexed += 1

        if not self.use_vectors:
            self._save_index()

        if self.use_vectors:
            self.chroma_client.persist()

        print(f"Indexed {indexed} emails, skipped {skipped}.")
        return indexed

    def _build_document(self, email, account_name):
        """Build a searchable text document from an email."""
        parts = [
            f"Account: {account_name}",
            f"From: {email.get('sender_name', '')} <{email.get('sender_email', '')}>",
            f"To: {email.get('to', '')}",
            f"Subject: {email.get('subject', '')}",
            f"Date: {email.get('date', '')}",
        ]

        body = email.get("body_text", "") or email.get("snippet", "")
        if body:
            parts.append(f"Body: {body[:3000]}")

        attachments = email.get("attachments", [])
        if attachments:
            parts.append(f"Attachments: {', '.join(str(a) for a in attachments)}")

        return "\n".join(parts)

    def query(self, question, top_k=8, account_filter=None):
        """
        Ask a question and get an answer grounded in your email history.

        Args:
            question: Natural language question
            top_k: Number of relevant emails to retrieve
            account_filter: Optional account name to restrict search

        Returns:
            Answer dict with 'answer', 'sources', and 'confidence'
        """
        # Step 1: Retrieve relevant emails
        retrieved = self._retrieve(question, top_k, account_filter)

        if not retrieved:
            return {
                "answer": "I couldn't find any relevant emails matching your question. "
                          "Try rephrasing or check if the emails have been indexed.",
                "sources": [],
                "confidence": "low",
            }

        # Step 2: Build context from retrieved docs
        context_parts = []
        sources = []
        for i, doc in enumerate(retrieved, 1):
            context_parts.append(f"--- EMAIL {i} ---\n{doc['text'][:1500]}\n")
            sources.append({
                "sender": doc.get("sender", ""),
                "subject": doc.get("subject", ""),
                "date": doc.get("date", ""),
                "account": doc.get("account", ""),
                "message_id": doc.get("message_id", ""),
                "relevance_score": doc.get("score", 0),
            })

        context = "\n".join(context_parts)

        # Step 3: RAG generation
        prompt = f"""You are MAILMAN Chat, answering questions about the user's email inbox.
Use ONLY the retrieved emails below to answer. If the answer isn't in the emails, say so.
Be specific, cite senders and dates when relevant.

RETRIEVED EMAILS:
{context}

QUESTION: {question}

RULES:
- Ground your answer in the actual email content
- Cite specific senders, dates, and subjects
- If you're not sure, say so rather than guessing
- Be concise and direct
- Never use em dashes or AI-speak
- If multiple emails are relevant, synthesize the information

Answer:"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}],
            )
            answer = response.content[0].text.strip()

            return {
                "answer": answer,
                "sources": sources,
                "confidence": "high" if len(retrieved) >= 3 else "medium" if retrieved else "low",
                "emails_searched": self._get_index_size(),
            }

        except Exception as e:
            return {
                "answer": f"Error generating answer: {e}",
                "sources": sources,
                "confidence": "error",
            }

    def _retrieve(self, question, top_k=8, account_filter=None):
        """Retrieve the most relevant emails for a question."""
        if self.use_vectors:
            return self._retrieve_vector(question, top_k, account_filter)
        else:
            return self._retrieve_keyword(question, top_k, account_filter)

    def _retrieve_vector(self, question, top_k, account_filter):
        """ChromaDB vector similarity search."""
        where_filter = None
        if account_filter:
            where_filter = {"account": account_filter}

        try:
            results = self.collection.query(
                query_texts=[question],
                n_results=top_k,
                where=where_filter,
            )

            docs = []
            if results and results["documents"] and results["documents"][0]:
                for i, doc_text in enumerate(results["documents"][0]):
                    meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                    distance = results["distances"][0][i] if results.get("distances") else 0
                    docs.append({
                        "text": doc_text,
                        "sender": meta.get("sender", ""),
                        "sender_name": meta.get("sender_name", ""),
                        "subject": meta.get("subject", ""),
                        "date": meta.get("date", ""),
                        "account": meta.get("account", ""),
                        "message_id": meta.get("message_id", ""),
                        "score": round(1 - distance, 3),  # Convert distance to similarity
                    })
            return docs

        except Exception as e:
            print(f"Vector retrieval error: {e}")
            return []

    def _retrieve_keyword(self, question, top_k, account_filter):
        """Fallback keyword-based search with basic scoring."""
        query_words = set(question.lower().split())
        scored = []

        for doc_id, doc in self.index.get("documents", {}).items():
            if account_filter and doc.get("account") != account_filter:
                continue

            text = doc.get("text", "").lower()

            # Simple TF scoring
            score = 0
            for word in query_words:
                if len(word) > 2:  # Skip tiny words
                    count = text.count(word)
                    if count > 0:
                        score += count

            # Boost for matches in subject
            subject = (doc.get("subject", "") or "").lower()
            for word in query_words:
                if word in subject:
                    score += 5

            # Boost for matches in sender
            sender = (doc.get("sender_name", "") or "").lower()
            for word in query_words:
                if word in sender:
                    score += 3

            if score > 0:
                scored.append({
                    "text": doc["text"],
                    "sender": doc.get("sender", ""),
                    "sender_name": doc.get("sender_name", ""),
                    "subject": doc.get("subject", ""),
                    "date": doc.get("date", ""),
                    "account": doc.get("account", ""),
                    "message_id": doc.get("message_id", ""),
                    "score": score,
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def _get_index_size(self):
        """Return the number of indexed documents."""
        if self.use_vectors:
            try:
                return self.collection.count()
            except Exception:
                return 0
        else:
            return len(self.index.get("documents", {}))

    def get_stats(self):
        """Return index statistics."""
        size = self._get_index_size()
        stats = {
            "total_indexed": size,
            "backend": "ChromaDB" if self.use_vectors else "Keyword Index",
            "index_location": str(DATA_DIR if self.use_vectors else self.index_path),
        }

        if not self.use_vectors and self.index.get("documents"):
            accounts = set()
            for doc in self.index["documents"].values():
                accounts.add(doc.get("account", "unknown"))
            stats["accounts"] = list(accounts)
            stats["last_updated"] = self.index.get("updated_at")

        return stats


def main():
    parser = argparse.ArgumentParser(description="MAILMAN Chat - Semantic Email Search")
    parser.add_argument("--index", type=str, help="Index emails from <account>")
    parser.add_argument("--query", type=str, help="Ask a question about your emails")
    parser.add_argument("--reindex", action="store_true", help="Rebuild the full index")
    parser.add_argument("--stats", action="store_true", help="Show index statistics")
    parser.add_argument("--account-filter", type=str, help="Restrict search to account")
    parser.add_argument("--top-k", type=int, default=8, help="Number of results to retrieve")
    args = parser.parse_args()

    chat = MailmanChat()

    if args.stats:
        stats = chat.get_stats()
        print(f"\nMAILMAN Chat Index Stats:")
        for k, v in stats.items():
            print(f"  {k}: {v}")

    elif args.index:
        from gmail_client import GmailClient
        client = GmailClient(args.index)
        print(f"Fetching emails from '{args.index}' for indexing...")
        emails = client.fetch_since(hours=720, max_results=500)
        chat.index_emails(emails, args.index)

    elif args.query:
        print(f"\nSearching for: {args.query}")
        result = chat.query(args.query, top_k=args.top_k, account_filter=args.account_filter)
        print(f"\n{result['answer']}")
        if result.get("sources"):
            print(f"\nSources ({len(result['sources'])} emails found):")
            for s in result["sources"][:5]:
                print(f"  - {s['sender']}: {s['subject']} ({s['date']})")
        print(f"\nConfidence: {result['confidence']} | Emails searched: {result.get('emails_searched', 'N/A')}")


if __name__ == "__main__":
    main()
