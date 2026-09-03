# AI Agent με RAG

Demo project ενός AI agent που συνδυάζει tool use πάνω στο Anthropic API με RAG (Retrieval-Augmented Generation)
πάνω σε PostgreSQL με την επέκταση pgvector. Το backend υλοποιείται σε FastAPI και το frontend σε Next.js
(chat UI), ενώ ο τελικός στόχος είναι το deployment ολόκληρου του συστήματος στο AWS. Το repository χτίζεται
σταδιακά: σε αυτό το στάδιο περιέχει μόνο τον σκελετό των φακέλων και ένα ελάχιστο health endpoint.

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

4. Αντιγραφή του template μεταβλητών περιβάλλοντος και συμπλήρωση του κλειδιού:

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

### Frontend

Δεν έχει στηθεί ακόμα — θα προστεθεί σε επόμενο βήμα.
