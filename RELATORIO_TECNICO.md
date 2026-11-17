# Relatório Técnico — Wallet API / Self-Testing CI

## 1. Objetivo e escopo
Microsserviço didático de carteira digital para criar contas, consultar saldo, transferir valores e obter extrato. Usa Python, FastAPI e SQLite. Não integra sistemas financeiros reais.

## 2. Especificação de requisitos (SRS)
### Requisitos funcionais
- **RF01:** Criar contas com nome e saldo inicial não negativo.
- **RF02:** Consultar conta e saldo pelo identificador.
- **RF03:** Transferir valor positivo entre contas diferentes, impedindo saldo insuficiente.
- **RF04:** Garantir idempotência por cabeçalho `Idempotency-Key` (mesma chave + mesmos dados retornam mesmo ID; chave + dados diferentes gera HTTP 409).
- **RF05:** Manter extrato com lançamentos de débito e crédito, filtráveis por data e tipo.
- **RF06:** Notificar gateway fictício de antifraude após transferência concluída.

### Requisitos não funcionais
- **RNF01:** JSON sobre HTTP e documentação OpenAPI em `/docs`.
- **RNF02:** Consistência de saldo sob concorrência, com lock local por instância, `BEGIN IMMEDIATE` e operações atômicas no SQLite.
- **RNF03:** Cálculos monetários em centavos inteiros, usando `Decimal` na conversão.
- **RNF04:** Suíte PyTest com cobertura >=85% de linhas e >=80% de branches.
- **RNF05:** CI em `push` e `pull_request`, com Ruff e relatórios como artefatos.
- **RNF06:** Teste de carga com no mínimo 50 usuários virtuais simultâneos via k6.

## 3. Endpoints
| Método | Rota | Resultado |
|---|---|---|
| GET | `/health` | Saúde da API |
| POST | `/accounts` | Criar conta (`owner`, `initial_balance`) |
| GET | `/accounts/{id}` | Consultar saldo |
| POST | `/transfers` | Transferir (`origin_id`, `destination_id`, `amount`); exige `Idempotency-Key` |
| GET | `/accounts/{id}/statement?kind=debit&start=2026-11-01&end=2026-11-30` | Extrato filtrado |

## 4. Arquitetura
- `controllers`: endpoints HTTP e validação de entrada.
- `domain`: regras puras e erros de negócio.
- `services`: lógica de criação, transferência e extrato, integração com antifraude.
- `repositories`: operações SQL, transações e banco de dados.
- `tests/unit`: regra financeira sem banco de dados.
- `tests/integration`: banco SQLite em memória, Mock de antifraude, Stub cadastral, concorrência.
- `tests/e2e`: chamadas HTTP pelo FastAPI TestClient.

## 5. Test Doubles
**Stub:** `CadastroStub` retorna valores determinísticos para validar quem pode abrir conta. **Mock:** `unittest.mock.Mock` verifica que `notify` foi chamado exatamente uma vez com os argumentos certos; replay não emite segunda chamada. Banco de integração usa URI SQLite compartilhada `mode=memory&cache=shared`.

## 6. TDD e versionamento
Modelo escolhido: **Trunk-Based Development**: branches `feature/*` e `hotfix/*` curtas; pull requests revisados e sem commits diretos na `main` depois de configurar proteção de branch. Commits sugeridos: `test: cria caso de saldo insuficiente` (RED), `feat: bloqueia transferência sem fundos` (GREEN), `refactor: extrai regra de transferência` (REFACTOR). **Registrar aqui hashes reais de três commits e links de dois PRs/merges de correção antes da entrega. Não declarar evidências inexistentes.**

| Evidência | Commit / link a preencher |
|---|---|
| RED | PENDENTE |
| GREEN | PENDENTE |
| REFACTOR | PENDENTE |
| Merge ou hotfix 1 | https://github.com/Niceas-Martins/projeto-self-testing-ci-/pull/1|
| Merge ou hotfix 2 | PENDENTE |

## 7. CI e cobertura
`ci.yml` executa linter, testes unitários, integração e E2E. Depois, coleta cobertura JSON e roda `scripts/check_coverage.py`, que falha quando linhas <85% ou branches <80%. Artefatos: `coverage.json` e `test-results.xml`. No GitHub, configurar proteção de `main` exigindo PR e o status check `quality-and-tests` antes do merge. 

**Resultados da execução local**

Testes automatizados: 25 aprovados, 0 falhas.

Cobertura de statements: 99,49% (196 de 197).

Cobertura de branches: 96,88% (31 de 32).

Análise estática: Ruff aprovado, sem erros.

Pipeline GitHub Actions: execução inicial concluída com sucesso.

Job: quality-and-tests.

Status: Success.

O pipeline executou as etapas de instalação de dependências, análise estática, testes unitários, testes de integração, testes E2E, verificação de cobertura e armazenamento de relatórios.

Link da execução: https://github.com/Niceas-Martins/projeto-self-testing-ci-/actions/runs/43939050010

## 8. Concorrência e idempotência
Transferências são processadas com lock local entre threads e transações SQLite `BEGIN IMMEDIATE`, serializando escritores. A chave única da transferência é gravada na mesma transação do débito, crédito e extrato. Requisições repetidas com mesma chave não descontam saldo novamente. O teste com ThreadPoolExecutor envia 50 chamadas concorrentes a um saldo finito e verifica saldo conservado.

## 9. Carga
Iniciar API: `python -m uvicorn src.main:app`. Executar (k6 instalado): `k6 run load_tests/transfer.js`. Script usa 50 VUs simultâneos por 15 s, contabiliza `transfer_errors`, mede `transfer_latency_ms` e k6 produz `http_req_duration`, `http_req_failed`. **Preencher após executar**, sem inventar resultados:

| Indicador | Valor observado |
|---|---|
| VUs simultâneos | 50 |
| Total de requisições | 125 |
| Taxa de erro (`http_req_failed`) | 0,00% |
| Latência média (`http_req_duration avg`) | 7,89 s |
| Latência p95 | 10,19 s |

## 10. Limitações e próximos passos
Projeto didático, não apto a uso financeiro real: não há autenticação, autorização, criptografia de dados sensíveis, reconciliação com bancos reais nem retentativas persistentes de webhooks. Antifraude é uma interface fictícia sem HTTP real; para enviar um webhook verdadeiro, implementar cliente HTTP injetável, autenticação do evento, outbox e retentativas. SQLite serializa escritores e não deve ser tratado como solução escalável para produção. `TestClient` executa a API internamente sobre HTTP simulado (ASGI), não por porta TCP de rede; para E2E externo pode-se usar HTTPX contra servidor Uvicorn real.

## 11. Referências
- FastAPI: https://fastapi.tiangolo.com/
- PyTest: https://docs.pytest.org/
- GitHub Actions: https://docs.github.com/en/actions
- k6: https://grafana.com/docs/k6/latest/

## Evidências de Integração Contínua

O projeto utiliza GitHub Actions para executar
automaticamente verificações de qualidade e testes.

Na primeira execução do workflow Wallet CI,
foram concluídas as seguintes etapas:

- Instalação das dependências.
- Análise estática com Ruff.
- Testes unitários com PyTest.
- Testes de integração.
- Testes End-to-End.
- Verificação de cobertura de código.
- Armazenamento de relatórios e logs.

A execução inicial foi concluída com sucesso.

### Cobertura verificada localmente

- Testes aprovados: 25 de 25.
- Cobertura de statements: 196/197 (99,49%).
- Cobertura de branches: 31/32 (96,88%).
- Linter: aprovado.

### Evidência prática de TDD

Foi realizado um ciclo Red-Green-Refactor para implementar a validação de identificadores de contas em transferências financeiras.

**RED:** foram criados quatro casos de teste para IDs inválidos, inicialmente sem implementação correspondente, demonstrando as falhas.

**GREEN:** foi implementada a validação dos identificadores, permitindo que os novos testes fossem aprovados.

**REFACTOR:** a validação foi extraída para uma função independente, preservando o comportamento e a aprovação dos testes.

As três etapas foram registradas em commits separados na branch `feature/validacao-ids-tdd`.