# BASELINE — R1 (rede de segurança)

**Medido em:** 2026-11-14 · **Branch:** `feat/r1-rede-de-seguranca` (merge de `origin/main` em `168c364`)
**Ambiente:** containers Docker (Python 3.12 · Django 5.2 · SQLite em memória nos testes)

> Regra da catraca (AGENTS.md §7): **estes números nunca pioram**. O gate bloqueante não
> pode piorar; os números advisory viram metas que sobem a cada ciclo.

## 1. Números

| Métrica | Baseline | Comando | Gate |
| :-- | :-- | :-- | :-- |
| Testes | **206 OK** (15 s) | `scripts/test.sh` | 🔴 bloqueante (e falha se rodar 0) |
| Cobertura de linhas | **84%** (1492 stmts, 236 não cobertas) | `scripts/coverage.sh` | 🟡 relatório |
| Ruff — erros reais (`E9,F63,F7,F82`) | **0** | `scripts/lint.sh --select E9,F63,F7,F82` | 🔴 bloqueante |
| Ruff — regras completas | **166 achados** (56 auto-fixáveis) | `scripts/lint.sh --statistics` | 🟡 advisory |
| Black — formatação | **49 de 62 arquivos** seriam reformatados | `docker run … black --check backend` | 🟡 advisory |
| Gitleaks — árvore atual | **0** (o cert local `nginx/certs/` é gitignored) | `gitleaks dir .` | 🔴 bloqueante |
| Gitleaks — histórico | **2** (`.env` de `57fd19a`: `SECRET_KEY`, `MYSQL_PASSWORD`) | `gitleaks git .` | 🟡 advisory — **D-015, rotação humana** |

### Ruff — distribuição dos 166 achados (advisory)

| Regra | Ocorrências | Regra | Ocorrências |
| :-- | --: | :-- | --: |
| `RUF012` mutable-class-default | 88 | `RUF046` unnecessary-cast-to-int | 2 |
| `I001` unsorted-imports | 33 | `RUF059` unused-unpacked-variable | 2 |
| `F401` unused-import | 16 | `UP031` printf-string-formatting | 1 |
| `FURB157` verbose-decimal-constructor | 7 | `EXE001/EXE002` shebang/executável | 2 |
| `B017` assert-raises-exception | 4 | `S110` try-except-pass | 1 |
| `F841` unused-variable | 4 | `SIM103` needless-bool | 3 |
| `BLE001` blind-except | 3 | | |

Os 56 auto-fixáveis (`--fix`) são a primeira meta: **um commit isolado**, sem mudança de lógica
(AGENTS.md §6.3). `RUF012` (mutable class default) e `B017` exigem análise manual.

## 2. O que mudou nesta etapa

| Item | Antes (R0) | Agora |
| :-- | :-- | :-- |
| Comando de testes do README | `Ran 0 tests ... OK` (falso verde, D-030) | `scripts/test.sh` roda 206 e **falha se 0** |
| Testes sem `collectstatic` | 50 erros de manifesto (D-030b) | verdes: settings usa storage simples durante testes |
| Hook pre-push | documentado, inexistente (D-031) | versionado em `scripts/hooks/pre-push` + `core.hooksPath` |
| Lint local | inexistente | `scripts/lint.sh` com as versões do CI |
| Cobertura local | inexistente | `scripts/coverage.sh` (mesmo relatório do CI) |
| Testes de caracterização | nenhum | 3 (D-001, D-002, D-003) |

## 3. Testes de caracterização (golden master)

Congelam o comportamento **atual** — inclusive quando ele é um bug — para que a R2 prove a mudança
com um diff test-only. Hoje eles passam **porque o bug existe**:

| Teste | Dívida | Comportamento congelado |
| :-- | :-- | :-- |
| `catalog.tests.SalesCheckoutCharacterizationTest` | D-001 | HTTP 400 de estoque **persiste** o pedido vazio (transação commitada) |
| `shipping.tests.ShippingQuoteSubtotalCharacterizationTest` | D-002 | `subtotal` escolhido pelo cliente zera o frete grátis |
| `management.tests.DashboardAggregationCharacterizationTest` | D-003 | frete somado **uma vez por item** no faturamento (R$ 60 em vez de R$ 40) |

> `D-004` (export CSV 500) foi corrigido no upstream (`d37f102`) durante o intervalo R0→R1: ganhou
> teste de regressão em `management/tests.py` e não precisa de caracterização.

## 4. Metas do próximo ciclo

1. Cobertura **≥ 84%** e subindo; nunca abaixo.
2. Ruff full **≤ 166**; zerar os 56 auto-fixáveis em commit isolado.
3. Black **≤ 49** arquivos pendentes (formatação em massa só em commit isolado + `.git-blame-ignore-revs`).
4. Adicionar type-checker (mypy/pyright) em modo relatório — ferramenta nova de dev = amarelo.
5. Lockfile com hashes para builds reproduzíveis (D-039).
