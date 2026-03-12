# Knowledge Base

## Overview

The Knowledge Base gives each agent domain-specific context via RAG (Retrieval-Augmented Generation). Users can upload files (PDF, TXT, CSV, DOCX), scrape URLs, or add raw text. Content is extracted and injected into the LLM's system prompt for every conversation.

---

## Data Model

See [database-schema.md](../database-schema.md) → `AgentKnowledge` model.

Key fields:
- `source_type`: `FILE`, `URL`, or `TEXT`
- `content`: Extracted plain text (always stored)
- `raw_content`: Original URL or raw text input
- `file_name`, `file_size`: For file uploads
- `char_count`, `chunk_count`: Content metrics

---

## Pages

### `/agents/[id]/knowledge` — Knowledge Management

- List of knowledge items: Title, Source type, Size, Date added
- Three add methods:
  - **Upload File**: Drag & drop or file picker
  - **Scrape URL**: URL input → preview extracted text
  - **Add Text**: Title + text content

- Delete action per item
- Total content summary: "X items, Y,000 characters total"

---

## Content Sources

### File Upload
| Format | Extension | Parser | Max Size |
|--------|-----------|--------|----------|
| PDF | .pdf | PyPDF2 | 10 MB |
| Plain text | .txt | Direct read | 10 MB |
| CSV | .csv | csv → formatted text | 10 MB |
| Word | .docx | python-docx | 10 MB |

### URL Scraping
```
1. Validate URL format
2. Fetch page via httpx (timeout 30s)
3. Parse HTML with BeautifulSoup
4. Extract main content (strip nav, footer, scripts)
5. Store cleaned text
6. Title: page <title> or URL hostname
```

### Raw Text
- Direct text input with title
- No processing needed

---

## Content Processing

### Document Parser (`app/services/document_parser.py`)

```python
class DocumentParser:
    async def parse_pdf(file: UploadFile) -> str:
        """Extract text from all pages of a PDF."""
    
    async def parse_txt(file: UploadFile) -> str:
        """Read text file content."""
    
    async def parse_csv(file: UploadFile) -> str:
        """Convert CSV rows to readable text format."""
    
    async def parse_docx(file: UploadFile) -> str:
        """Extract text from Word document."""
    
    async def parse(file: UploadFile) -> str:
        """Auto-detect format and parse."""
```

### Content Limits

| Limit | Value |
|-------|-------|
| Max file size | 10 MB |
| Max content per item | 100,000 characters |
| Max items per agent | Plan-dependent (5 / 20 / 50 / unlimited) |
| URL scrape timeout | 30 seconds |
| Scrape max content | 100,000 characters |

---

## Context Injection (in Chat Engine)

```python
# How knowledge is used in chat
async def get_knowledge_context(agent_id: UUID) -> str:
    items = await knowledge_repo.get_by_agent(agent_id)
    if not items:
        return ""
    
    combined = "\n\n---\n\n".join([
        f"## {item.title}\n{item.content}" 
        for item in items
    ])
    
    # Truncate to fit context window
    MAX_CHARS = 50_000  # ~12.5k tokens
    if len(combined) > MAX_CHARS:
        combined = combined[:MAX_CHARS] + "\n\n[Content truncated due to length]"
    
    return combined
```

---

## Edge Cases

| Scenario | Expected Behaviour |
|----------|-------------------|
| Empty PDF (no text) | Return error: "No text content found" |
| Scanned PDF (images only) | Return error: "OCR not supported" |
| URL returns 404 | Return error: "Could not fetch URL" |
| URL returns non-HTML | Return error: "URL must be an HTML page" |
| File exceeds 10 MB | 413 Payload Too Large |
| Content exceeds 100k chars | Truncate and warn: "Content truncated" |
| Plan limit reached | 429 "Knowledge item limit reached" |
| Delete last item | Allow — agent works without knowledge |

---

## Business Rules

1. **Plan enforcement**: Knowledge items count checked before adding
2. **Agent ownership**: Only agent owner can manage knowledge
3. **Content immutability**: Knowledge items can be added or deleted, not edited
4. **No vector search v1**: v1 uses simple concatenation; v2 will add embeddings + similarity search
5. **Cascading delete**: Deleting an agent deletes its knowledge items

---

## API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/v1/agents/{agent_id}/knowledge` | List knowledge items |
| POST | `/api/v1/agents/{agent_id}/knowledge/file` | Upload file |
| POST | `/api/v1/agents/{agent_id}/knowledge/url` | Scrape URL |
| POST | `/api/v1/agents/{agent_id}/knowledge/text` | Add raw text |
| DELETE | `/api/v1/agents/{agent_id}/knowledge/{id}` | Delete item |
