# Guia de execução e entrega rápida

## 1. Instalar e iniciar (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn src.main:app --reload
```
Acesse http://127.0.0.1:8000/docs para experimentar as rotas.

## 2. Testar (outro terminal, na pasta do projeto)
```powershell
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m pytest --cov=src --cov-branch --cov-report=json:coverage.json --cov-report=term-missing
.\.venv\Scripts\python.exe scripts/check_coverage.py
.\.venv\Scripts\python.exe -m ruff check src tests scripts
```
Linux/macOS: troque `.\.venv\Scripts\python.exe` por `.venv/bin/python`.

## 3. Simular carga
Instale o k6 conforme https://grafana.com/docs/k6/latest/set-up/install-k6/
Execute com servidor ativo: `k6 run load_tests/transfer.js`. Registre as métricas REAIS no relatório.

## 4. Publicar e criar evidência real de Git
```bash
git init
git checkout -b main
git add .
git commit -m "chore: estrutura inicial da wallet api"
git remote add origin URL_DO_SEU_REPOSITORIO
git push -u origin main
```
Depois crie uma branch curta para uma melhoria real (ex.: testar uma validação adicional) e faça PR para `main`.
Para demonstrar RED/GREEN/REFACTOR genuinamente, crie um **novo** teste que falhe, registre o commit `test: ...`, implemente a regra no commit `feat: ...`, e melhore o código no commit `refactor: ...`. Faça uma segunda branch curta com outra correção real e abra um segundo PR. Não invente histórico de commits.

No GitHub: Settings > Branches ou Rules > Rulesets > proteja main exigindo PR e o status check da CI. Dependendo do plano/permissões do repositório, algumas regras podem não estar disponíveis.

## 5. Antes de enviar
- Atualize RELATORIO_TECNICO.md com links reais dos PRs, hashes de commits e resultados medidos.
- Verifique se Actions mostra execução verde.
- Confirme se `/docs` permite registrar conta, transferir e consultar extrato.
- Não inclua `.venv`, `wallet.db` nem senhas no repositório.

**Escopo didático:** antifraude é uma porta fictícia chamada pela camada de serviço e testada com Mock, não um webhook HTTP real. Os testes TestClient são via transporte ASGI interno.
