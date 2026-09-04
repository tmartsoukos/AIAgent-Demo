import os

import psycopg2
from google.genai import types
from pgvector.psycopg2 import register_vector

# Το ίδιο embedding model και η ίδια διάσταση χρησιμοποιούνται και στο
# ingest.py (όταν αποθηκεύονται τα έγγραφα) και στο main.py (όταν γίνεται
# αναζήτηση) — αν διαφέρουν, το cosine similarity δεν βγάζει νόημα.
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 768


def get_connection():
    """Ανοίγει σύνδεση και κάνει register τον τύπο vector του psycopg2.

    Το register_vector χρειάζεται το extension να υπάρχει ήδη στη βάση —
    στο ingest.py, που δημιουργεί το extension με CREATE EXTENSION, γίνεται
    πρώτα η σύνδεση χωρίς register (μέσω raw_connection) και μετά καλείται
    το register_vector ξεχωριστά.
    """
    conn = raw_connection()
    register_vector(conn)
    return conn


def raw_connection():
    """Σύνδεση χωρίς register_vector, για χρήση πριν υπάρχει το extension."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Λείπει το DATABASE_URL. Συμπλήρωσέ το στο backend/.env")
    return psycopg2.connect(database_url)


def embed_text(client, text: str, task_type: str) -> list[float]:
    """Παράγει embedding μέσω Gemini.

    task_type διαφοροποιεί πώς κωδικοποιείται το κείμενο: τα ίδια τα έγγραφα
    χρησιμοποιούν RETRIEVAL_DOCUMENT, ενώ τα queries χρησιμοποιούν
    RETRIEVAL_QUERY — το μοντέλο εκπαιδεύεται να τα τοποθετεί κοντά στον
    χώρο των embeddings όταν ταιριάζουν σημασιολογικά.
    """
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=EMBEDDING_DIM,
        ),
    )
    return response.embeddings[0].values
