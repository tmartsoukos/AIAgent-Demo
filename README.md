# AI Agent με RAG

Demo project ενός AI agent που συνδυάζει function calling πάνω στο Google Gemini API με RAG (Retrieval-Augmented
Generation) πάνω σε PostgreSQL με την επέκταση pgvector. Το backend υλοποιείται σε FastAPI και το frontend σε
Next.js (chat UI), ενώ ο τελικός στόχος είναι το deployment ολόκληρου του συστήματος στο AWS. Το repository
χτίζεται σταδιακά: σε αυτό το στάδιο το backend έχει ένα health endpoint και έναν agent με δύο mock functions
(`search_docs`, `get_current_time`) πίσω από το `/chat`.

## Setup

### Προϋποθέσεις

- Python 3.11+ (δοκιμασμένο με 3.13.2)

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

5. Εκκίνηση του server:

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

### Frontend

Δεν έχει στηθεί ακόμα — θα προστεθεί σε επόμενο βήμα.
