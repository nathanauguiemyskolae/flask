#!/bin/sh
# Génère la paire de clés RSA utilisée pour signer (clé privée) et vérifier (clé publique) les JWT.
# Les clés ne sont jamais dans le dépôt : elles vivent dans un volume Docker (jwt-keys) en développement,
# et dans un gestionnaire de secrets en production.
set -e

if [ -f /keys/privateKey.pem ] && [ -f /keys/publicKey.pem ]; then
  echo "Clés JWT déjà présentes."
  exit 0
fi

apk add --no-cache openssl >/dev/null
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out /keys/privateKey.pem
openssl pkey -in /keys/privateKey.pem -pubout -out /keys/publicKey.pem
# Lisibles par le processus Java du conteneur ; en production, la clé privée est en 600
chmod 644 /keys/privateKey.pem /keys/publicKey.pem
echo "Clés JWT générées."
