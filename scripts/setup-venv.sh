#!/usr/bin/env bash
# Instala dependencias del API en un venv (ejecutar en el servidor como intrajis).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 no encontrado" >&2
  exit 1
fi

python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo ""
echo "Listo. Usa en systemd:"
echo "  ExecStart=${ROOT}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8097"
echo ""
echo "Probar manualmente:"
echo "  cd ${ROOT} && ./venv/bin/uvicorn main:app --host 127.0.0.1 --port 8097"
