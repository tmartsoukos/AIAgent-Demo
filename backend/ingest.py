"""Γεμίζει τον πίνακα documents με sample κείμενα και τα embeddings τους.

Τρέξιμο (από τον φάκελο backend/, με ενεργό venv):
    python ingest.py
"""

import os

from dotenv import load_dotenv
from google import genai

from pgvector.psycopg2 import register_vector

from db import EMBEDDING_DIM, embed_text, raw_connection

load_dotenv()

DOCUMENTS = [
    (
        "Τι είναι ένας AI agent",
        "Ένας AI agent είναι ένα σύστημα που χρησιμοποιεί ένα γλωσσικό μοντέλο "
        "για να αποφασίζει αυτόνομα ποιες ενέργειες θα εκτελέσει προκειμένου να "
        "πετύχει έναν στόχο, αντί απλά να απαντάει σε μία ερώτηση. Συνήθως τρέχει "
        "σε βρόχο: παρατηρεί την κατάσταση, αποφασίζει την επόμενη ενέργεια, την "
        "εκτελεί, και επαναλαμβάνει μέχρι να ολοκληρωθεί ο στόχος.",
    ),
    (
        "Tool use / function calling",
        "Το tool use (ή function calling) επιτρέπει σε ένα γλωσσικό μοντέλο να "
        "καλεί εξωτερικές συναρτήσεις αντί να απαντάει μόνο με κείμενο. Το μοντέλο "
        "δεν εκτελεί τον κώδικα το ίδιο· επιστρέφει ποιο tool θέλει να καλέσει και "
        "με ποια ορίσματα, ο client τρέχει τη συνάρτηση, και το αποτέλεσμα "
        "επιστρέφει πίσω στο μοντέλο για να συνεχίσει τη σκέψη του.",
    ),
    (
        "Τι είναι το RAG",
        "Το Retrieval-Augmented Generation (RAG) είναι μια τεχνική όπου, πριν το "
        "μοντέλο απαντήσει, ανακτώνται σχετικά αποσπάσματα κειμένου από μια "
        "εξωτερική βάση γνώσης και προστίθενται στο context. Έτσι το μοντέλο "
        "μπορεί να απαντήσει με βάση συγκεκριμένα, ενημερωμένα δεδομένα αντί να "
        "βασίζεται μόνο σε ό,τι έμαθε κατά την εκπαίδευσή του.",
    ),
    (
        "Embeddings και semantic search",
        "Ένα embedding είναι μια αριθμητική αναπαράσταση ενός κειμένου ως "
        "διάνυσμα σε πολυδιάστατο χώρο, όπου κείμενα με παρόμοιο νόημα "
        "αντιστοιχούν σε κοντινά διανύσματα. Το semantic search εκμεταλλεύεται "
        "αυτή την ιδιότητα: αντί να ψάχνει για ακριβή λέξεις-κλειδιά, βρίσκει "
        "τα κείμενα των οποίων το embedding είναι πιο κοντά σε αυτό του query.",
    ),
    (
        "pgvector",
        "Το pgvector είναι μια επέκταση της PostgreSQL που προσθέτει έναν τύπο "
        "δεδομένων vector και τελεστές απόστασης, ώστε embeddings να "
        "αποθηκεύονται και να αναζητούνται απευθείας μέσα στη βάση με απλό SQL, "
        "χωρίς να χρειάζεται ξεχωριστό, εξειδικευμένο vector database.",
    ),
    (
        "Cosine similarity",
        "Το cosine similarity μετράει πόσο κοντά είναι δύο διανύσματα "
        "συγκρίνοντας τη γωνία μεταξύ τους, όχι το μέγεθός τους — δύο embeddings "
        "που δείχνουν προς την ίδια κατεύθυνση θεωρούνται σημασιολογικά κοντά "
        "ακόμα κι αν έχουν διαφορετικό μήκος. Είναι η πιο συνηθισμένη μετρική "
        "για embeddings κειμένου, γι' αυτό το pgvector προσφέρει τον τελεστή "
        "<=> (cosine distance) ειδικά για αυτή τη χρήση.",
    ),
]


def main():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    conn = raw_connection()
    cur = conn.cursor()

    # Το CREATE EXTENSION είναι αυτό που ενεργοποιεί το pgvector μέσα στη
    # βάση: χωρίς αυτό, ο τύπος "vector" και ο τελεστής "<=>" δεν υπάρχουν.
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn.commit()
    # Μόλις υπάρχει το extension, ο psycopg2 μπορεί να registράρει τον
    # τύπο vector ώστε τα Python lists να περνάνε απευθείας ως embeddings.
    register_vector(conn)

    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding VECTOR({EMBEDDING_DIM}) NOT NULL
        )
        """
    )
    cur.execute("TRUNCATE documents RESTART IDENTITY")

    for title, content in DOCUMENTS:
        embedding = embed_text(client, content, task_type="RETRIEVAL_DOCUMENT")
        cur.execute(
            "INSERT INTO documents (title, content, embedding) VALUES (%s, %s, %s)",
            (title, content, embedding),
        )
        print(f"Καταχωρήθηκε: {title}")

    conn.commit()
    cur.execute("SELECT count(*) FROM documents")
    print(f"Σύνολο εγγράφων στη βάση: {cur.fetchone()[0]}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
