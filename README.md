# Wallet API — Capstone Self-Testing CI

## Instalação rápida
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Executar
```bash
python -m uvicorn src.main:app --reload
```
Acesse http://127.0.0.1:8000/docs

## Validar
```bash
python -m pytest -v
python -m pytest --cov=src --cov-branch --cov-report=term-missing --cov-report=json:coverage.json
python scripts/check_coverage.py
python -m ruff check src tests scripts
```

## HTTP exemplo
POST `/accounts`: `{"owner":"Maria","initial_balance":"100.00"}`
POST `/transfers`: `{"origin_id":1,"destination_id":2,"amount":"10.00"}` com header `Idempotency-Key: envio-123`.

## Submissão
Publicar no GitHub, abrir PRs nas branches curtas, configurar proteção de main, adicionar links de commits/PRs e números reais de cobertura/carga em `RELATORIO_TECNICO.md`.
