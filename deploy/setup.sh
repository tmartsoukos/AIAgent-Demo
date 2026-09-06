#!/usr/bin/env bash
#
# Προετοιμασία ενός καθαρού Ubuntu 24.04 instance για να τρέξει το project.
# Εγκαθιστά Docker, το compose plugin και git, και κατεβάζει το repo.
#
# Χρήση, ΜΕΣΑ στο EC2 instance:
#     ./setup.sh https://github.com/<user>/<repo>.git
#
# Δεν χρειάζεται sudo μπροστά — το script καλεί sudo όπου χρειάζεται.

# -e: σταμάτα στο πρώτο σφάλμα αντί να συνεχίσεις με μισοτελειωμένο setup.
# -u: θεώρησε σφάλμα κάθε αναφορά σε μη ορισμένη μεταβλητή.
# -o pipefail: ένα pipeline αποτυγχάνει αν αποτύχει οποιοδήποτε στάδιό του.
set -euo pipefail

REPO_URL="${1:-}"
CLONE_DIR="${2:-$HOME/AIAgent}"

if [ -z "$REPO_URL" ]; then
    echo "Σφάλμα: λείπει το URL του repository." >&2
    echo "Χρήση: $0 <repo-url> [φάκελος-προορισμού]" >&2
    exit 1
fi

echo "==> 1/5 Ενημέρωση λίστας πακέτων και του συστήματος"
# update: ανανεώνει τον κατάλογο διαθέσιμων πακέτων (δεν εγκαθιστά τίποτα).
sudo apt-get update
# DEBIAN_FRONTEND=noninteractive: αποτρέπει διαλόγους που θα κόλλαγαν το
# script περιμένοντας πλήκτρο. upgrade -y: εφαρμόζει τις ενημερώσεις.
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

echo "==> 2/5 Εγκατάσταση βασικών εργαλείων"
# ca-certificates + curl: χρειάζονται για να κατεβεί με ασφάλεια το κλειδί
# υπογραφής του Docker repository. git: για το clone του repo.
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ca-certificates \
    curl \
    git

echo "==> 3/5 Προσθήκη του επίσημου Docker repository"
# Το Docker που έρχεται με τα Ubuntu repos είναι παλιό και ΔΕΝ περιλαμβάνει
# το compose plugin. Γι' αυτό προστίθεται το επίσημο repository της Docker.

# Φάκελος όπου το apt αναζητά κλειδιά υπογραφής πακέτων.
# -m 0755: αναγνώσιμος από όλους, εγγράψιμος μόνο από τον owner.
sudo install -m 0755 -d /etc/apt/keyrings

# Κατέβασμα του δημόσιου κλειδιού της Docker. Με αυτό το apt επαληθεύει ότι
# τα πακέτα προέρχονται όντως από τη Docker και δεν έχουν πειραχθεί.
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    -o /etc/apt/keyrings/docker.asc
# Το κλειδί πρέπει να είναι αναγνώσιμο από τον χρήστη _apt.
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Καταχώρηση του repository, δεμένου με το παραπάνω κλειδί (signed-by).
# dpkg --print-architecture: amd64 ή arm64, ανάλογα με τον τύπο του instance.
# VERSION_CODENAME: το codename της διανομής (στο 24.04 είναι "noble").
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Ξανά update, ώστε να διαβαστεί ο κατάλογος του νέου repository.
sudo apt-get update

echo "==> 4/5 Εγκατάσταση Docker και του compose plugin"
# docker-ce: ο Docker daemon. docker-ce-cli: η εντολή "docker".
# containerd.io: το runtime που εκτελεί τα containers.
# docker-compose-plugin: δίνει το "docker compose" (με κενό, όχι παύλα).
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

# Ο Docker daemon να ξεκινά αυτόματα σε κάθε reboot του instance.
sudo systemctl enable --now docker

# Χωρίς αυτό, κάθε εντολή docker θα απαιτούσε sudo. Η ομάδα "docker" δίνει
# πρόσβαση στο socket του daemon.
# ΠΡΟΣΟΧΗ: ισχύει από το ΕΠΟΜΕΝΟ login — χρειάζεται αποσύνδεση/επανασύνδεση.
sudo usermod -aG docker "$USER"

echo "==> 5/5 Λήψη του repository"
if [ -d "$CLONE_DIR/.git" ]; then
    # Αν το script ξανατρέξει, δεν αποτυγχάνει: απλά τραβάει τις αλλαγές.
    echo "Το repo υπάρχει ήδη στο $CLONE_DIR — γίνεται pull."
    git -C "$CLONE_DIR" pull --ff-only
else
    git clone "$REPO_URL" "$CLONE_DIR"
fi

echo
echo "Η εγκατάσταση ολοκληρώθηκε."
echo
echo "Επόμενα βήματα:"
echo "  1. Αποσυνδέσου και ξανασυνδέσου (exit, μετά ξανά ssh), ώστε να"
echo "     ενεργοποιηθεί η ιδιότητα μέλους στην ομάδα docker."
echo "  2. Αντίγραψε τα αρχεία .env από τον υπολογιστή σου με scp."
echo "  3. cd $CLONE_DIR && docker compose up -d --build"
echo
echo "Λεπτομέρειες: deploy/DEPLOY.md"
