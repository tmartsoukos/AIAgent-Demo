# AI Agent με RAG

Demo project ενός AI agent που συνδυάζει function calling πάνω στο Google Gemini API με RAG (Retrieval-Augmented
Generation) πάνω σε PostgreSQL με την επέκταση pgvector. Το backend υλοποιείται σε FastAPI και το frontend σε
Next.js (chat UI), ενώ ο τελικός στόχος είναι το deployment ολόκληρου του συστήματος στο AWS. Το repository
χτίζεται σταδιακά: σε αυτό το στάδιο ο agent εκτίθεται στο `/chat` με δύο functions — `search_docs`, που κάνει
πραγματικό semantic search στη βάση, και `get_current_time` — και υπάρχει chat UI που δείχνει ποια εργαλεία
χρησιμοποίησε ο agent σε κάθε απάντηση. Εκκρεμεί το deployment στο AWS.

## Setup

### Προϋποθέσεις

- Python 3.11+ (δοκιμασμένο με 3.13.2)
- Node.js 20+ (δοκιμασμένο με 22.14.0), για το frontend
- Docker Desktop (για τη βάση δεδομένων)

### Βάση δεδομένων

Από τη ρίζα του project, εκκίνηση της PostgreSQL με το pgvector extension:

```bash
docker compose up -d
```

Σηκώνει έναν container στο port 5432 με βάση `ragdb`. Τα δεδομένα αποθηκεύονται
σε named volume (`pgdata`), οπότε επιβιώνουν σε restart του container. Έλεγχος
ότι τρέχει:

```bash
docker compose ps
```

### Backend

Από τον φάκελο `backend/`:

1. Δημιουργία virtual environment:

   ```bash
   python -m venv .venv
   ```

2. Ενεργοποίηση (Windows / PowerShell):

   ```bash
   .venv\Scripts\Activate.ps1
   ```

   Σε Linux ή macOS:

   ```bash
   source .venv/bin/activate
   ```

3. Εγκατάσταση εξαρτήσεων:

   ```bash
   pip install -r requirements.txt
   ```

4. Αντιγραφή του template μεταβλητών περιβάλλοντος και συμπλήρωση του `GEMINI_API_KEY`
   (δωρεάν κλειδί από το [Google AI Studio](https://aistudio.google.com/apikey)):

   ```bash
   cp .env.example .env
   ```

   Το `.env` αγνοείται από το git και δεν ανεβαίνει ποτέ στο repository.
   Το `DATABASE_URL` του template δείχνει ήδη στη βάση του `docker-compose.yml`.

5. Φόρτωση των sample εγγράφων στη βάση (δημιουργεί το extension `vector`,
   τον πίνακα `documents`, και αποθηκεύει τα embeddings):

   ```bash
   python ingest.py
   ```

   Χρειάζεται μία φορά, αφού η βάση είναι σε λειτουργία. Χωρίς αυτό το βήμα
   το `search_docs` δεν έχει τίποτα να ανακτήσει.

6. Εκκίνηση του server:

   ```bash
   uvicorn main:app --reload
   ```

### Έλεγχος

Με τον server σε λειτουργία:

```bash
curl http://127.0.0.1:8000/health
```

Αναμενόμενη απάντηση:

```json
{"status": "ok"}
```

Ο agent (χρειάζεται το `GEMINI_API_KEY` στο `.env`):

```bash
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"message\": \"Τι ώρα είναι;\"}"
```

Η απάντηση περιέχει το τελικό κείμενο του agent και τη λίστα των function calls που έγιναν στη διαδρομή:

```json
{"reply": "...", "function_calls": [{"name": "get_current_time", "args": {}}]}
```

Ερώτηση που ενεργοποιεί το RAG (semantic search πάνω στα ingested κείμενα):

```bash
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"message\": \"Τι είναι το cosine similarity;\"}"
```

Εδώ το `function_calls` δείχνει την κλήση του `search_docs`, και η απάντηση
χτίζεται πάνω στα 3 πιο σχετικά έγγραφα που ανακτήθηκαν από τη βάση.

### Frontend

Next.js 16 (App Router, TypeScript, Tailwind). Από τον φάκελο `frontend/`, με
το backend ήδη σε λειτουργία:

1. Εγκατάσταση εξαρτήσεων:

   ```bash
   npm install
   ```

2. Αντιγραφή του template μεταβλητών περιβάλλοντος:

   ```bash
   cp .env.local.example .env.local
   ```

   Το `NEXT_PUBLIC_API_URL` δείχνει στο backend· αλλάζοντάς το εκεί δείχνει σε
   άλλο περιβάλλον χωρίς αλλαγή κώδικα.

3. Εκκίνηση:

   ```bash
   npm run dev
   ```

Το UI ανοίγει στο <http://localhost:3000>. Γράφοντας ένα μήνυμα και πατώντας
Enter (ή «Send»), εμφανίζεται η απάντηση του agent και, από κάτω, ένα
collapsible μπλοκ με τα function calls που έγιναν — π.χ.
`🔧 1 function call` → `search_docs {"query": "cosine similarity"}`.

Το backend επιτρέπει CORS μόνο για το `http://localhost:3000`. Αν το frontend
τρέξει σε άλλο origin, πρέπει να προστεθεί στο `allow_origins` στο
`backend/main.py`, αλλιώς ο browser μπλοκάρει τις απαντήσεις.
