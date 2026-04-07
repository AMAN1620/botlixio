"""Text chunker — splits text into overlapping token-bounded chunks."""

import tiktoken

CHUNK_SIZE = 512   # tokens
OVERLAP = 50       # tokens
ENCODING = "cl100k_base"  # used by text-embedding-3-small and gpt-4o


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """
    Split text into chunks of ~chunk_size tokens with overlap tokens of context.
    Returns list of text strings. Empty or whitespace-only input returns [].
    """
    text = text.strip()
    if not text:
        return []

    enc = tiktoken.get_encoding(ENCODING)
    tokens = enc.encode(text)

    if len(tokens) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_str = enc.decode(chunk_tokens)
        chunks.append(chunk_text_str)
        if end == len(tokens):
            break
        start += chunk_size - overlap

    return chunks
