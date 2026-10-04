#!/usr/bin/env bash
# Sube spike-hu01 a la instancia GPU con rsync. El .env NO se sube: se copia aparte con scp.
# Uso: scripts/subir-gpu.sh <ip-de-la-instancia>
# Opcionales: GPU_LLAVE (ruta a la .pem), GPU_USUARIO (por defecto ubuntu), GPU_DESTINO (por defecto spike-hu01)
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Uso: $0 <ip-de-la-instancia>" >&2
  exit 1
fi

IP="$1"
USUARIO="${GPU_USUARIO:-ubuntu}"
DESTINO="${GPU_DESTINO:-spike-hu01}"
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
SSH_CMD="ssh"
if [ -n "${GPU_LLAVE:-}" ]; then
  SSH_CMD="ssh -i ${GPU_LLAVE}"
fi

rsync -az -e "$SSH_CMD" \
  --exclude '/client/' \
  --exclude 'node_modules/' \
  --exclude '.angular/' \
  --exclude 'dist/' \
  --exclude '/metrics/' \
  --exclude '/recordings/' \
  --exclude '.env' \
  --exclude '__pycache__/' \
  --exclude '.DS_Store' \
  "$RAIZ/" "$USUARIO@$IP:$DESTINO/"

echo "Subido a $USUARIO@$IP:$DESTINO"
echo "El .env no se sube. Cópialo aparte (y revisa WHISPER_MODEL y WHISPER_BASE_URL=http://whisper:8000/v1):"
echo "  scp ${GPU_LLAVE:+-i $GPU_LLAVE }$RAIZ/.env $USUARIO@$IP:$DESTINO/.env"
