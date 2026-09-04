import os
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel

# Φόρτωση του GEMINI_API_KEY από το backend/.env
load_dotenv()

MODEL = "gemini-3.6-flash"
# Όριο ασφαλείας ώστε το loop να μην τρέχει επ' άπειρον αν ο agent κολλήσει
MAX_ITERATIONS = 10

app = FastAPI(title="AI Agent RAG API")

# Ο client φτιάχνεται με το πρώτο αίτημα, ώστε ο server να ξεκινάει
# κανονικά (και το /health να δουλεύει) ακόμα κι αν λείπει το κλειδί.
_client = None


def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="Λείπει το GEMINI_API_KEY. Συμπλήρωσέ το στο backend/.env",
            )
        _client = genai.Client(api_key=api_key)
    return _client


# --------------------------------------------------------------------------
# Mock functions
# --------------------------------------------------------------------------

# Ψεύτικη "βάση" εγγράφων. Σε επόμενο βήμα θα αντικατασταθεί από
# πραγματικό RAG πάνω σε PostgreSQL + pgvector.
FAKE_DOCS = [
    {
        "title": "Αρχιτεκτονική του agent",
        "content": (
            "Ο agent τρέχει σε FastAPI backend και καλεί το Gemini API με function calling. "
            "Κάθε function call εκτελείται τοπικά και το αποτέλεσμα επιστρέφει στο μοντέλο."
        ),
    },
    {
        "title": "RAG με pgvector",
        "content": (
            "Τα έγγραφα τεμαχίζονται σε chunks, μετατρέπονται σε embeddings και "
            "αποθηκεύονται σε PostgreSQL με την επέκταση pgvector για αναζήτηση ομοιότητας."
        ),
    },
    {
        "title": "Deployment στο AWS",
        "content": (
            "Το backend θα τρέξει σε container, η βάση σε managed PostgreSQL, "
            "και το frontend θα σερβίρεται ξεχωριστά."
        ),
    },
]


def search_docs(query: str) -> str:
    """Ψεύτικη αναζήτηση: επιστρέφει hardcoded αποτελέσματα μαζί με το query."""
    lines = [f'Αποτελέσματα αναζήτησης για "{query}":']
    for i, doc in enumerate(FAKE_DOCS, start=1):
        lines.append(f"{i}. {doc['title']}: {doc['content']}")
    return "\n".join(lines)


def get_current_time() -> str:
    """Επιστρέφει την τρέχουσα ημερομηνία και ώρα του server."""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


# Declarations όπως τα περιμένει το Gemini API
SEARCH_DOCS_DECLARATION = types.FunctionDeclaration(
    name="search_docs",
    description=(
        "Αναζητά σχετικά έγγραφα στη βάση γνώσης του project. "
        "Χρησιμοποίησέ το όταν ο χρήστης ρωτάει για την αρχιτεκτονική, "
        "το RAG ή το deployment του συστήματος."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "query": types.Schema(
                type=types.Type.STRING,
                description="Οι όροι αναζήτησης.",
            )
        },
        required=["query"],
    ),
)

# Χωρίς parameters, γιατί η συνάρτηση δεν δέχεται ορίσματα
GET_CURRENT_TIME_DECLARATION = types.FunctionDeclaration(
    name="get_current_time",
    description=(
        "Επιστρέφει την τρέχουσα ημερομηνία και ώρα. "
        "Χρησιμοποίησέ το όταν ο χρήστης ρωτάει τι ώρα είναι."
    ),
)

TOOLS = [
    types.Tool(
        function_declarations=[
            SEARCH_DOCS_DECLARATION,
            GET_CURRENT_TIME_DECLARATION,
        ]
    )
]

# Αντιστοίχιση ονόματος function -> Python συνάρτηση
FUNCTIONS = {
    "search_docs": search_docs,
    "get_current_time": get_current_time,
}


def run_function(name: str, args: dict) -> str:
    """Εκτελεί την ζητούμενη function και επιστρέφει το αποτέλεσμα ως κείμενο."""
    function = FUNCTIONS.get(name)
    if function is None:
        return f"Άγνωστη function: {name}"
    return function(**args)


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest):
    contents = [
        types.Content(role="user", parts=[types.Part(text=request.message)])
    ]
    # Το automatic function calling κλείνει, γιατί το loop το τρέχουμε εμείς
    config = types.GenerateContentConfig(
        tools=TOOLS,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    function_calls = []

    for _ in range(MAX_ITERATIONS):
        try:
            response = get_client().models.generate_content(
                model=MODEL,
                contents=contents,
                config=config,
            )
        except genai_errors.APIError as error:
            raise HTTPException(status_code=502, detail=str(error))

        calls = response.function_calls

        # Ο agent δεν ζήτησε άλλη function -> έχουμε την τελική απάντηση
        if not calls:
            return {
                "reply": response.text or "",
                "function_calls": function_calls,
            }

        # Το μήνυμα του μοντέλου (με τα function_call parts) μπαίνει στο ιστορικό
        contents.append(response.candidates[0].content)

        # Εκτέλεση όλων των function calls αυτού του γύρου
        result_parts = []
        for call in calls:
            args = call.args or {}
            function_calls.append({"name": call.name, "args": args})
            result_parts.append(
                types.Part.from_function_response(
                    name=call.name,
                    response={"result": run_function(call.name, args)},
                )
            )

        # Όλα τα αποτελέσματα επιστρέφουν μαζί σε ΕΝΑ μήνυμα
        contents.append(types.Content(role="user", parts=result_parts))

    raise HTTPException(
        status_code=500,
        detail=f"Ο agent δεν ολοκλήρωσε μέσα σε {MAX_ITERATIONS} γύρους.",
    )
