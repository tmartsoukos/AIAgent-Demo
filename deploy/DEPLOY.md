# Deployment σε EC2

Οδηγίες για deployment του project σε ένα EC2 instance με Ubuntu 24.04.

Στα παραδείγματα χρησιμοποιείται η διεύθυνση `<EC2_PUBLIC_IP>` και το κλειδί
`~/.ssh/<your-key>.pem`. Αντικατέστησέ τα αν αλλάξουν.

> Η public IP ενός instance **αλλάζει** σε κάθε stop/start, εκτός αν του έχει
> ανατεθεί Elastic IP. Μετά από αλλαγή IP χρειάζεται ενημέρωση του `.env` και
> rebuild (βλ. βήμα 8).

---

## 0. Προϋποθέσεις: άνοιγμα θυρών στο Security Group

Πριν από οτιδήποτε άλλο, το Security Group του instance πρέπει να επιτρέπει
εισερχόμενη κίνηση στις εξής θύρες:

| Θύρα | Χρήση                          |
| ---- | ------------------------------ |
| 22   | SSH                            |
| 3000 | Frontend (chat UI)             |
| 8000 | Backend API                    |

Η θύρα **5432 δεν πρέπει να ανοίξει** — η βάση είναι προσβάσιμη μόνο από τα
υπόλοιπα containers μέσα στο δίκτυο του compose, και δεν υπάρχει λόγος να
εκτεθεί στο internet.

Αν το βήμα 7 δείξει ότι το backend απαντά τοπικά μέσα στο instance αλλά όχι
από τον υπολογιστή σου, σχεδόν πάντα φταίει το Security Group.

---

## 1. Σύνδεση με SSH

Το ιδιωτικό κλειδί πρέπει να μην είναι αναγνώσιμο από άλλους χρήστες, αλλιώς
το OpenSSH αρνείται να το χρησιμοποιήσει:

```bash
chmod 400 ~/.ssh/<your-key>.pem
```

Σύνδεση (το προεπιλεγμένο όνομα χρήστη στα Ubuntu AMI είναι `ubuntu`):

```bash
ssh -i ~/.ssh/<your-key>.pem ubuntu@<EC2_PUBLIC_IP>
```

---

## 2. Μεταφορά και εκτέλεση του setup script

Από τον **υπολογιστή σου**, στη ρίζα του project:

```bash
scp -i ~/.ssh/<your-key>.pem deploy/setup.sh ubuntu@<EC2_PUBLIC_IP>:~/
```

Μετά, **μέσα στο instance**:

```bash
chmod +x ~/setup.sh
```

```bash
~/setup.sh https://github.com/tmartsoukos/AIAgent-Demo.git
```

Το script ενημερώνει το σύστημα, εγκαθιστά Docker με το compose plugin και
git, και κάνει clone το repo στο `~/AIAgent`. Διαρκεί μερικά λεπτά.

Μόλις τελειώσει, **αποσυνδέσου και ξανασυνδέσου**:

```bash
exit
```

```bash
ssh -i ~/.ssh/<your-key>.pem ubuntu@<EC2_PUBLIC_IP>
```

Αυτό χρειάζεται ώστε να ενεργοποιηθεί η συμμετοχή στην ομάδα `docker` —
διαφορετικά κάθε εντολή `docker` θα ζητά `sudo`. Έλεγχος:

```bash
docker compose version
```

---

## 3. Μεταφορά των μυστικών με scp

Τα αρχεία `.env` **δεν βρίσκονται ποτέ στο git** (τα αποκλείει το
`.gitignore`), οπότε το `git clone` δεν τα έφερε. Μεταφέρονται χειροκίνητα.

Χρειάζονται δύο αρχεία:

| Αρχείο         | Περιεχόμενο                                       |
| -------------- | ------------------------------------------------- |
| `backend/.env` | `GEMINI_API_KEY` (και `DATABASE_URL`)             |
| `.env` (ρίζα)  | `NEXT_PUBLIC_API_URL`, `CORS_ORIGINS`             |

### 3α. Το κλειδί του backend

Από τον **υπολογιστή σου**:

```bash
scp -i ~/.ssh/<your-key>.pem backend/.env ubuntu@<EC2_PUBLIC_IP>:~/AIAgent/backend/.env
```

Το `DATABASE_URL` μέσα σε αυτό το αρχείο αγνοείται όταν τρέχει μέσω Docker —
το `docker-compose.yml` το αντικαθιστά με τη διεύθυνση της βάσης μέσα στο
δίκτυο του compose. Σημασία έχει μόνο το `GEMINI_API_KEY`.

### 3β. Οι διευθύνσεις του deployment

Αυτό το αρχείο περιέχει διευθύνσεις, όχι μυστικά, αλλά διαφέρει ανά
περιβάλλον — γι' αυτό δεν είναι στο git. Φτιάξ' το **μέσα στο instance**:

```bash
cat > ~/AIAgent/.env <<'EOF'
NEXT_PUBLIC_API_URL=http://<EC2_PUBLIC_IP>:8000
CORS_ORIGINS=http://<EC2_PUBLIC_IP>:3000
EOF
```

Και τα δύο πρέπει να δείχνουν στην **public IP**, όχι στο `localhost`:

- `NEXT_PUBLIC_API_URL` είναι η διεύθυνση που θα καλέσει ο **browser σου**.
  Μέσα στο bundle του frontend το `localhost` θα σήμαινε τον υπολογιστή σου,
  όχι τον server.
- `CORS_ORIGINS` είναι το origin απ' όπου φορτώνει η σελίδα. Πρέπει να
  ταιριάζει ακριβώς (scheme, host, port), αλλιώς ο browser μπλοκάρει κάθε
  απάντηση του backend.

---

## 4. Εκκίνηση

**Μέσα στο instance:**

```bash
cd ~/AIAgent && docker compose up -d --build
```

Το πρώτο build διαρκεί αρκετά (κατέβασμα base images, `pip install`,
`npm ci`, build του Next). Έλεγχος κατάστασης:

```bash
docker compose ps
```

Και τα τρία services πρέπει να είναι `Up`, με το `db` σε κατάσταση
`(healthy)`.

---

## 5. Φόρτωση των εγγράφων στη βάση

Η βάση στο instance ξεκινά **άδεια** — ο πίνακας `documents` δεν υπάρχει
ακόμα. Χωρίς αυτό το βήμα ο agent απαντά ότι δεν βρήκε σχετικά έγγραφα:

```bash
docker compose exec backend python ingest.py
```

Αναμενόμενη έξοδος: έξι γραμμές «Καταχωρήθηκε: …» και «Σύνολο εγγράφων στη
βάση: 6».

Χρειάζεται μία μόνο φορά — τα δεδομένα παραμένουν στο named volume `pgdata`
και επιβιώνουν σε restart.

---

## 6. Επιβεβαίωση μέσα από το instance

```bash
curl http://localhost:8000/health
```

Αναμενόμενη απάντηση: `{"status":"ok"}`

Αν αυτό αποτύχει, το πρόβλημα είναι στα containers — δες τα logs:

```bash
docker compose logs backend --tail 50
```

---

## 7. Επιβεβαίωση απ' έξω

Από τον **υπολογιστή σου**:

```bash
curl http://<EC2_PUBLIC_IP>:8000/health
```

Αν το βήμα 6 πέτυχε αλλά αυτό κολλάει, φταίει το Security Group (βήμα 0).

Μετά άνοιξε στον browser:

```
http://<EC2_PUBLIC_IP>:3000
```

Γράψε «Τι είναι το pgvector;» και πάτα Enter. Πρέπει να δεις την απάντηση του
agent και από κάτω ένα μπλοκ `🔧 1 function call` με `search_docs`.

> Είναι `http://`, όχι `https://`. Ο browser θα το σημειώσει ως «Not secure»,
> κάτι αναμενόμενο για demo χωρίς πιστοποιητικό.

Αν η σελίδα φορτώνει αλλά τα μηνύματα αποτυγχάνουν, άνοιξε το DevTools
console. Σφάλμα CORS σημαίνει ότι το `CORS_ORIGINS` δεν ταιριάζει με τη
διεύθυνση της γραμμής διευθύνσεων.

---

## 8. Ενημέρωση του deployment

Μετά από νέα commits:

```bash
cd ~/AIAgent && git pull && docker compose up -d --build
```

**Αν άλλαξε η public IP** (π.χ. μετά από stop/start), ενημέρωσε το `~/AIAgent/.env`
με τη νέα διεύθυνση και **οπωσδήποτε ξανακάνε build**:

```bash
docker compose up -d --build
```

Σκέτο `restart` δεν αρκεί: το `NEXT_PUBLIC_API_URL` ενσωματώνεται στο bundle
του frontend τη στιγμή του build, οπότε το frontend θα συνέχιζε να καλεί την
παλιά διεύθυνση.

---

## Χρήσιμες εντολές

| Σκοπός                     | Εντολή                                  |
| -------------------------- | --------------------------------------- |
| Κατάσταση services         | `docker compose ps`                     |
| Logs (ζωντανά)             | `docker compose logs -f`                |
| Logs ενός service          | `docker compose logs backend --tail 50` |
| Τερματισμός                | `docker compose down`                   |
| Τερματισμός + σβήσιμο βάσης| `docker compose down -v`                |
| Χώρος στον δίσκο           | `df -h`                                 |

> Το `down -v` διαγράφει το volume της βάσης. Μετά από αυτό χρειάζεται ξανά
> το βήμα 5.
