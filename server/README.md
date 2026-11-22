# Knowledge Assistant

![Python](https://img.shields.io/badge/language-Python-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A Django REST Framework backend for an AI-powered **Knowledge Assistant** — combining retrieval-augmented generation (RAG) over your own documents, chat with an LLM, notes, auto-generated flashcards, and long-term memory, all behind a JWT-secured API.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Features

The project is organized as a set of focused Django apps:

| App          | Responsibility |
|--------------|---|
| `accounts` | User model, registration, and authentication |
| `chat` | Conversational endpoints — routes user messages to an LLM agent, with tool-calling support |
| `documents` | Document upload and storage, feeding the retrieval pipeline |
| `retrieval` | RAG pipeline — chunking, embedding, vector indexing, and semantic search over documents |
| `notes` | User-authored notes |
| `flashcards` | Automatic flashcard generation from indexed content |
| `memory` | Long-term memory storage for the assistant |
| `tasks` | Celery background jobs (indexing, flashcard generation, etc.) |
| `search` | Cross-source workspace search |
| `agents` | Agent/tool registry powering the chat assistant |
| `core` | Middleware and structured JSON logging, implemented in `core/middleware.py` and `core/logging.py` |

## Architecture

```mermaid
flowchart TD

subgraph group_runtime["Django Runtime"]
  node_entrypoints{{"Process Entry Points<br/>Django entry<br/>[manage.py]"}}
  node_settings["Settings, Middleware & Celery<br/>application configuration<br/>[settings.py]"]
  node_root_routes["Root URL Routing<br/>request dispatcher<br/>[urls.py]"]
end

subgraph group_api["HTTP API Layer"]
  node_api_routes["API Route Composition<br/>URL router<br/>[api/urls.py]"]
  node_content["Accounts, Documents,<br/>Notes & Memory APIs<br/>[views.py]"]
  node_chat["Chat API (SSE)<br/>streaming responses<br/>[chat/views.py]"]
  node_flashcards["Flashcard API<br/>[flashcards/views.py]"]
  node_search["Search API<br/>[search/views.py]"]
end

subgraph group_storage["Persistent Storage"]
  node_postgres[("PostgreSQL<br/>Accounts, Documents,<br/>Notes, Memories,<br/>Chats, Flashcards")]
  node_contentindex[("ContentIndex<br/>Index Status")]
end

subgraph group_async["Background Processing"]
  node_signals["Django Signals<br/>post_save / post_delete"]
  node_celery["Celery Workers"]
  node_tasks["Retrieval Tasks"]
end

subgraph group_retrieval["Retrieval Pipeline"]
  node_loader["Load & Normalize"]
  node_chunk["Chunk Text"]
  node_embed["Gemini Embeddings<br/>768 dimensions"]
  node_vector[("Chroma / Pinecone / Qdrant")]
  node_retriever["Retriever<br/>Cosine Similarity<br/>Top-K Search"]
end

subgraph group_ai["AI Layer"]
  node_agent["LangChain Agent"]
  node_llm["Gemini / Groq LLM"]

  node_tools["Agent Tools<br/>search_my_knowledge<br/>remember_fact<br/>tavily_search<br/>calculator<br/>current_time"]

  node_flashgen["Flashcard Generator"]
end

node_entrypoints --> node_settings
node_entrypoints --> node_root_routes
node_root_routes --> node_api_routes

node_api_routes --> node_content
node_api_routes --> node_chat
node_api_routes --> node_flashcards
node_api_routes --> node_search

node_content -->|"CRUD"| node_postgres
node_chat -->|"Conversation History"| node_postgres
node_flashcards -->|"Stores Cards"| node_postgres

node_content --> node_signals
node_signals --> node_celery
node_celery --> node_tasks

node_tasks --> node_loader
node_loader --> node_chunk
node_chunk --> node_embed
node_embed -->|"Store Embeddings"| node_vector
node_tasks -->|"Update Status"| node_contentindex

node_chat -->|"Invoke"| node_agent
node_agent --> node_llm
node_agent --> node_tools

node_tools -->|"Retrieve"| node_retriever
node_retriever -->|"Query"| node_vector

node_tools -->|"Create Memory"| node_postgres
node_postgres --> node_signals

node_search -->|"Semantic Search"| node_retriever

node_flashcards -->|"Queue"| node_celery
node_celery --> node_flashgen
node_flashgen --> node_llm
node_flashgen --> node_postgres

classDef toneNeutral fill:#f8fafc,stroke:#334155,stroke-width:1.5px,color:#0f172a
classDef toneBlue fill:#dbeafe,stroke:#2563eb,stroke-width:1.5px,color:#172554
classDef toneAmber fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
classDef toneMint fill:#dcfce7,stroke:#16a34a,stroke-width:1.5px,color:#14532d
classDef toneRose fill:#ffe4e6,stroke:#e11d48,stroke-width:1.5px,color:#881337
classDef toneIndigo fill:#e0e7ff,stroke:#4f46e5,stroke-width:1.5px,color:#312e81

class node_entrypoints,node_settings,node_root_routes toneBlue
class node_api_routes,node_content,node_chat,node_flashcards,node_search toneAmber
class node_postgres,node_contentindex toneNeutral
class node_signals,node_celery,node_tasks toneIndigo
class node_loader,node_chunk,node_embed,node_vector,node_retriever toneMint
class node_agent,node_llm,node_tools,node_flashgen toneRose
```

## Tech Stack

- **Framework:** Django + Django REST Framework
- **Auth:** `djangorestframework-simplejwt` (JWT access/refresh tokens)
- **API docs:** `drf-spectacular` (OpenAPI schema)
- **LLM:** Google Gemini or Groq (default model: `gemini-3.5-flash-lite`)
- **Vector store:** Chroma locally, or Pinecone/Qdrant when configured
- **Embeddings:** Gemini `gemini-embedding-001` (768 dimensions); Hugging Face can be selected for local use
- **Background tasks:** Celery, backed by Redis
- **CORS:** `django-cors-headers`

## Installation

### Prerequisites

- Python 3.10+
- Redis (for Celery broker/result backend)
- A PostgreSQL (or other `DATABASE_URL`-compatible) database
- A [Groq API key](https://console.groq.com/) for LLM access

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/AshrayaBashyal/knowledge_assistant.git
cd knowledge_assistant

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env   # .env.example is included in the repo — see Configuration below
# then edit .env with your own values

# 5. Apply database migrations
python manage.py migrate

# 6. Run the development server
python manage.py runserver
```

### Running background workers

Flashcard generation and document indexing run as Celery tasks and require a worker process alongside the server:

```bash
celery -A config worker --loglevel=info
```

Make sure Redis is running and reachable at the URL configured in `CELERY_REDIS_URL`.

## Configuration

All configuration is read from environment variables (see `config/settings.py`). A `.env.example` file is included in the repo — copy it to `.env` in the project root and fill in your own values:

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `insecure-dev-key` | Django secret key — set a strong value in production |
| `DEBUG` | `True` | Django debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `DATABASE_URL` | — | Database connection string (e.g. Postgres URL) |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:8501` | Comma-separated origins allowed to call the API |
| `GROQ_API_KEY` | — | API key for the Groq LLM provider |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Groq model used for chat |
| `GROQ_TEMPERATURE` | `0.7` | Sampling temperature for the chat model |
| `CHROMA_PERSIST_DIR` | `<project>/chroma_data` | Directory for the Chroma vector store |
| `RETRIEVAL_TOP_K` | `4` | Number of chunks retrieved per query |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model for indexing/retrieval |
| `EMBEDDING_PROVIDER` | `gemini` | `gemini` or local `huggingface` embeddings |
| `GEMINI_EMBEDDING_MODEL` | `models/gemini-embedding-001` | Gemini embedding model (768-dimensional output) |
| `CHUNK_SIZE` | `1000` | Document chunk size (characters) for indexing |
| `CHUNK_OVERLAP` | `200` | Overlap between consecutive chunks |
| `RESULTS_PER_SOURCE` | `10` | Max results per source for workspace search |
| `CELERY_REDIS_URL` | `redis://localhost:6379/0` | Redis URL used as both Celery broker and result backend |
| `CHAT_HISTORY_MAX_MESSAGES` | `20` | Max past chat messages replayed to the model per turn |
| `DOCUMENT_MAX_UPLOAD_SIZE_MB` | `60` | Max allowed upload size for documents |
| `LOG_LEVEL` | `INFO` | Root logging level |

### Render and Vercel deployment notes

- The frontend defaults to the configured Render API URL in production; set
  `VITE_API_BASE_URL` in Vercel if the backend URL changes. Vite reads this at
  build time, so changing it requires a new frontend deployment.
- Render's free web service can sleep while idle, causing a slow first request.
  The `/api/health/` endpoint is used as its readiness check.
- Render Free has a very small shared web instance and no separate free
  background-worker service. Keep `CELERY_TASK_ALWAYS_EAGER=True` (the default)
  for the least memory pressure and simplest operation. Indexing and flashcard
  generation then run inside the request and can take longer. Setting it to
  `False` starts one Celery `solo` worker beside Gunicorn; this is supported by
  the startup script but shares the same CPU and memory and can make the service
  slower or unstable. Upstash Redis supplies the broker, not extra compute.
- Render's local filesystem is ephemeral. Use Neon for `DATABASE_URL`, Pinecone
  or Qdrant for vectors, and configure all three `CLOUDINARY_*` values if
  uploaded documents must survive restarts. Local SQLite, media files, and
  Chroma data are not durable across instance replacement.
- This project does not configure Cloudflare R2. Cloudflare DNS in front of
  Vercel does not require an application code change; use Cloudinary for the
  current document-upload storage integration.
- Gemini/Groq model availability, free quotas, and rate limits depend on the
  provider account and can change. Existing indexed content should be re-indexed
  after changing the embedding model; use the refresh icon beside an indexed
  document or note.

#### Existing Render deployment checklist

1. In the Render web service, keep the Free plan and verify the build command
   installs `server/requirements.txt` and runs `collectstatic`; the start command
   should be `bash start.sh`.
2. In **Environment**, verify `DATABASE_URL` is Neon’s pooled connection URL,
   `SECRET_KEY` is a private generated value, and `DEBUG=False`. Set
   `CORS_ALLOWED_ORIGINS` to the exact Vercel site origin.
3. Configure `GEMINI_API_KEY` for the default chat model and embeddings. For
   durable document indexing, configure `VECTOR_STORE_PROVIDER=pinecone`,
   `PINECONE_API_KEY`, and `PINECONE_INDEX_NAME`; configure
   `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and
   `CLOUDINARY_API_SECRET` together for uploaded files. These are separate
   provider services and their free-tier availability/quotas can change. A
   user's Groq BYOK key only covers chat; embeddings still require the server's
   Gemini API key. Pinecone index creation currently targets Serverless AWS
   `us-east-1`, cosine distance, and 768 dimensions; use these settings if you
   create the index manually.
4. Leave `CELERY_TASK_ALWAYS_EAGER` unset or set it to `True` on Render Free.
   Do not add a separate Render worker on Free. Upstash is optional in this
   mode; background jobs do not use it.
5. In Vercel, ensure the project root is `client` and set
   `VITE_API_BASE_URL=https://reading-room-emvk.onrender.com` if you want to
   override the built-in production default. Redeploy Vercel after changing
   this build-time variable.
6. Deploy the branch. Render runs `manage.py migrate` on service startup; check
   its deploy logs for migration completion and confirm
   `https://reading-room-emvk.onrender.com/api/health/` returns HTTP 200 after
   the service wakes. No restart or schema edit in Neon is needed.

## Usage

The API is documented via `drf-spectacular` — once the server is running, the OpenAPI schema is available through the configured docs route.

### 1. Authenticate

Obtain a JWT access/refresh token pair:

```bash
curl -X POST http://localhost:8000/api/accounts/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'
```

Include the access token on subsequent requests:

```bash
curl http://localhost:8000/api/documents/ \
  -H "Authorization: Bearer <access_token>"
```

### 2. Upload a document

```bash
curl -X POST http://localhost:8000/api/documents/ \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@/path/to/your/file.pdf"
```

Uploaded documents are chunked, embedded, and indexed into Chroma automatically via a background task.

### 3. Chat with the assistant

```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Summarize the key points from the document I just uploaded."}'
```

The chat agent draws on indexed documents (retrieval), stored notes, and long-term memory to answer.

### 4. Generate flashcards

```bash
curl -X POST http://localhost:8000/api/flashcards/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "<document-id>"}'
```

Flashcard sets are generated asynchronously — poll the returned set's status until it completes.

> Exact route prefixes depend on `api/urls.py` and each app's `urls.py` — check those for the authoritative path list.

## Contributing

Contributions are welcome. To propose a change:

1. **Fork** the repository and create a feature branch off `main`:
   ```bash
   git checkout -b feature/short-description
   ```
2. **Follow existing conventions** — keep app boundaries intact (models/serializers/views per app), and match the structured logging and middleware patterns already implemented in `core/logging.py` and `core/middleware.py`.
3. **Write clear commits** — imperative, present-tense subject lines (e.g. `Add flashcard retry endpoint`), with a short body explaining *why* when the change isn't self-evident.
4. **Test before opening a PR** — run migrations and the local server to confirm nothing's broken:
   ```bash
   python manage.py migrate --check
   python manage.py test
   ```
5. **Open a pull request** against `main` with a description of the change, its motivation, and any manual testing performed. Link related issues where relevant.
6. Be responsive to review feedback — small, focused PRs are easiest to review and merge quickly.

If you're planning a larger change (new app, schema change, provider swap), open an issue first to discuss the approach.

## License

This project is licensed under the [MIT License](https://choosealicense.com/licenses/mit/) — see the [LICENSE](LICENSE) file in the repository root for the full text.
