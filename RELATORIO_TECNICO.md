# Relatório Técnico — Wallet API / Self-Testing CI

## 1. Objetivo e escopo

Microsserviço didático de carteira digital para criar contas, consultar saldo, transferir valores e obter extrato. Desenvolvido com Python, FastAPI e SQLite. Não integra sistemas financeiros reais.

**Repositório do projeto:** https://github.com/Niceas-Martins/projeto-self-testing-ci-

## 2. Especificação de requisitos (SRS)

### Requisitos funcionais

- **RF01:** Criar contas com nome e saldo inicial não negativo.
- **RF02:** Consultar conta e saldo pelo identificador.
- **RF03:** Transferir valor positivo entre contas diferentes, impedindo saldo insuficiente e rejeitando identificadores de contas não positivos.
- **RF04:** Garantir idempotência por cabeçalho `Idempotency-Key` (mesma chave e mesmos dados retornam o mesmo ID; chave repetida com dados diferentes gera HTTP 409).
- **RF05:** Manter extrato com lançamentos de débito e crédito, filtráveis por data e tipo.
- **RF06:** Notificar gateway fictício de antifraude após transferência concluída.

### Requisitos não funcionais

- **RNF01:** JSON sobre HTTP e documentação OpenAPI em `/docs`.
- **RNF02:** Consistência de saldo sob concorrência, com lock local por instância, `BEGIN IMMEDIATE` e operações atômicas no SQLite.
- **RNF03:** Cálculos monetários em centavos inteiros, usando `Decimal` na conversão.
- **RNF04:** Suíte PyTest com cobertura mínima de 85% de statements/linhas e 80% de branches.
- **RNF05:** CI em `push` e `pull_request`, com Ruff e relatórios como artefatos.
- **RNF06:** Teste de carga com 50 usuários virtuais simultâneos via k6.

## 3. Endpoints

| Método | Rota | Resultado |
|---|---|---|
| GET | `/health` | Saúde da API |
| POST | `/accounts` | Criar conta (`owner`, `initial_balance`) |
| GET | `/accounts/{account_id}` | Consultar saldo |
| POST | `/transfers` | Transferir (`origin_id`, `destination_id`, `amount`); exige `Idempotency-Key` |
| GET | `/accounts/{account_id}/statement` | Extrato filtrável com parâmetros opcionais `kind`, `start` e `end` |

Exemplo de extrato filtrado: `/accounts/1/statement?kind=debit&start=2026-11-01&end=2026-11-30`.

## 4. Arquitetura

- `controllers`: endpoints HTTP e validação de entrada.
- `domain`: regras puras e erros de negócio.
- `services`: lógica de criação, transferência e extrato; integração com antifraude.
- `repositories`: operações SQL, transações e banco de dados.
- `tests/unit`: regras financeiras sem banco de dados.
- `tests/integration`: banco SQLite em memória, Mock de antifraude, Stub cadastral e concorrência.
- `tests/e2e`: chamadas à aplicação por meio do FastAPI `TestClient`.

## 5. Test Doubles

**Stub:** `CadastroStub` retorna valores determinísticos para validar quem pode abrir conta.

**Mock:** `unittest.mock.Mock` verifica que `notify` foi chamado exatamente uma vez e com os argumentos esperados; repetir uma transferência idempotente não emite segunda notificação.

Os testes de integração utilizam SQLite em memória por URI compartilhada (`mode=memory&cache=shared`).

## 6. TDD e versionamento

Foi adotado **Trunk-Based Development**, com branches de curta duração, commits padronizados e integração via Pull Requests após verificações automatizadas. O histórico registra branches de documentação, uma feature de TDD e uma alteração de manutenção.

### Evidências do ciclo Red-Green-Refactor

Foi implementada uma validação que rejeita identificadores de contas menores ou iguais a zero em transferências. O ciclo foi separado em três commits:

| Etapa | Hash | Evidência |
|---|---|---|
| **RED** | `cb4fcdf` | `test: RED adiciona testes para IDs invalidos` — inclusão de quatro casos de teste para IDs inválidos antes da correção |
| **GREEN** | `78083bb` | `feat: GREEN valida IDs de contas nas transferencias` — implementação da regra de validação |
| **REFACTOR** | `b9ffe99` | `refactor: extrai validacao de IDs das contas` — extração da verificação para função dedicada |

O histórico dos três commits consta do Pull Request de TDD, que foi integrado à `main` após aprovação das verificações automatizadas. Os hashes identificam os commits reais; o relatório não substitui os logs dos testes de cada etapa.

### Evidências de Pull Requests e merges

| Evidência | Referência | Resultado |
|---|---|---|
| Merge 1 — documentação de CI | [PR #1](https://github.com/Niceas-Martins/projeto-self-testing-ci-/pull/1) | Concluído |
| Merge 2 — documentação de branching | [PR #2](https://github.com/Niceas-Martins/projeto-self-testing-ci-/pull/2) | Concluído |
| Merge 3 — validação de IDs via TDD | [PR #3](https://github.com/Niceas-Martins/projeto-self-testing-ci-/pull/3) | Concluído; verificações aprovadas |
| Merge 4 — remoção de guia temporário | [PR #4](https://github.com/Niceas-Martins/projeto-self-testing-ci-/pull/4) | Concluído; verificações aprovadas |

**Nota de conferência:** os números #2 e #3 seguem a sequência dos Pull Requests realizados e devem ser conferidos na aba *Pull requests* do repositório antes da entrega. As evidências dos merges #1 e #4 e da integração do TDD foram exibidas no GitHub durante o desenvolvimento.

## 7. Integração contínua, qualidade e cobertura

O arquivo `.github/workflows/ci.yml` configura a execução automática do pipeline em eventos de `push` e `pull_request`. O workflow instala dependências, executa o linter Ruff, separa suítes unitárias, de integração e E2E, verifica limites de cobertura com `scripts/check_coverage.py` e armazena relatórios de testes e cobertura como artefatos (`test-results.xml` e `coverage.json`). O gate exige pelo menos 85% de statements/linhas e 80% de branches.

### Resultados verificados localmente (antes da melhoria TDD)

| Indicador | Resultado |
|---|---|
| Testes automatizados | 25 aprovados; 0 falhas |
| Cobertura de statements | 196/197 — **99,49%** |
| Cobertura de branches | 31/32 — **96,88%** |
| Análise estática | Ruff: `All checks passed!` |
| Job do GitHub Actions | `quality-and-tests` — sucesso |

Essas métricas correspondem à execução local registrada **antes** dos quatro novos casos de TDD; não devem ser apresentadas como medição posterior sem nova execução.

**Link da execução inicial do GitHub Actions:** https://github.com/Niceas-Martins/projeto-self-testing-ci-/actions/runs/43939050010

### Proteção da branch principal

Foi configurada uma regra de proteção da branch `main` no GitHub, com exigência de Pull Request e status checks antes do merge, selecionando o job `quality-and-tests`. Os merges realizados por Pull Request evidenciam o fluxo de integração. A aplicação efetiva das restrições depende das permissões e condições do repositório no GitHub.

## 8. Concorrência e idempotência

Transferências são processadas com lock local entre threads e transações SQLite `BEGIN IMMEDIATE`, serializando escritores. A chave única de idempotência é gravada na mesma transação do débito, crédito e extrato. Requisições repetidas com a mesma chave e os mesmos dados não descontam saldo novamente.

O teste de integração com `ThreadPoolExecutor` envia 50 chamadas concorrentes a um saldo finito e verifica a conservação dos saldos. Esse teste de consistência é distinto do teste de carga realizado com k6.

## 9. Teste de carga e desempenho

O teste foi executado localmente utilizando `k6 run load_tests/transfer.js`, com a API iniciada via Uvicorn. O cenário configurou **50 usuários virtuais simultâneos durante 15 segundos**, com encerramento gracioso das iterações em andamento.

### Resultados observados

| Indicador | Valor observado |
|---|---:|
| Usuários virtuais simultâneos (`vus_max`) | **50** |
| Duração da fase de carga | **15 s** |
| Duração total observada | **26,1 s** |
| Total de requisições HTTP (`http_reqs`) | **125** |
| Transferências verificadas (`checks_total`) | **123** |
| Verificações aprovadas | **123/123 (100%)** |
| Taxa de erro HTTP (`http_req_failed`) | **0,00% (0/125)** |
| Latência média HTTP (`http_req_duration avg`) | **7,89 s** |
| Latência HTTP p95 | **10,19 s** |
| Latência média de transferência (`transfer_latency_ms avg`) | **8.014,61 ms** |
| Latência p95 de transferência | **10.193,61 ms** |
| Iterações interrompidas | **0** |

**Análise:** O servidor respondeu às 125 requisições HTTP sem falhas, e as 123 verificações de transferência foram aprovadas. Entretanto, a latência sob concorrência foi elevada: cerca de 7,89 segundos em média e 10,19 segundos no percentil 95. A serialização de gravações do SQLite é uma possível limitação de desempenho. Portanto, os resultados indicam estabilidade funcional no cenário executado, mas não comprovam desempenho adequado para produção.

## 10. Limitações e próximos passos

Projeto didático, não apto a uso financeiro real: não há autenticação, autorização, criptografia de dados sensíveis, reconciliação com bancos reais nem retentativas persistentes de webhooks. Antifraude é uma interface fictícia sem HTTP real; para enviar um webhook verdadeiro, seria necessário implementar cliente HTTP injetável, autenticação do evento, outbox e retentativas.

SQLite serializa escritores e não deve ser considerado solução escalável para produção. `TestClient` executa a API internamente sobre HTTP simulado (ASGI), não via porta TCP de rede; testes de ponta a ponta contra serviço externo poderiam utilizar HTTPX e um servidor Uvicorn real.

## 11. Referências

- [FastAPI](https://fastapi.tiangolo.com/)
- [PyTest](https://docs.pytest.org/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [k6](https://grafana.com/docs/k6/latest/)
