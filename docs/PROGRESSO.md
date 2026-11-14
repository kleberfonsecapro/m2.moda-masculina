# PROGRESSO — Quadro Kanban

**Fases do retrofit** (AGENTS.md §4). Colunas: Backlog → Pronto → Em andamento → Em revisão →
Aguardando humano → Feito (+ Bloqueado).

**Estado:** R0 concluído (2026-11-02, gate aprovado) · **R1 em andamento** (2026-11-14).

---

## Fases

| Fase | Status | Saída | Gate |
| :-- | :-- | :-- | :-- |
| **R0** Inventário | ✅ Feito | `docs/00-VISAO.md`, `01-ARQUITETURA.md`, `MAPA-DO-CODIGO.md`, `02-CONTRATOS.md`, `DIVIDA.md` (81 itens), `PROGRESSO.md`, `LOG.md` | ✅ aprovado |
| **R1** Rede de segurança | 🟨 Em andamento | `docs/BASELINE.md`, `R1-PLANO-ROLLBACK.md`, `BACKUP.md` | — |
| **R2** Reavaliação de segurança | ⬜ Backlog | `docs/AUDITORIA-SEGURANCA.md` | — |
| **R3** Organização de diretórios | ⬜ Backlog | `docs/ESTRUTURA-ATUAL.md`, `ESTRUTURA-ALVO.md` | — |
| **R4** Endurecimento de infra | ⬜ Backlog | `docs/ESTRUTURA-ALVO.md` + item por item | — |
| **R5** Evolução contínua | ⬜ Backlog | `docs/BACKLOG.md` | — |

## R1 — andamento (2026-11-14)

| # | Tarefa | Status | Evidência |
| :-- | :-- | :-- | :-- |
| 1 | Backup 3-2-1 + **restore testado** | ✅ | 27 tabelas / 199 linhas / 0 divergências + teste negativo (exit 1) — `docs/BACKUP.md` |
| 2 | Fixo do falso verde (D-030, D-030b) | ✅ | `scripts/test.sh` → **206 testes OK** sem `collectstatic`; falha se 0 |
| 3 | `requirements-dev.txt` + ruff + coverage (D-036, D-039) | 🟡 parcial | `scripts/lint.sh`, `scripts/coverage.sh`, baseline 84%; falta type-checker/lockfile |
| 4 | `core.hooksPath` versionado (D-031) | ✅ | `scripts/install-hooks.sh` + `scripts/hooks/pre-push` (executado: suíte verde) |
| 5 | CI/CD | ✅ | `.github/workflows/ci.yml`: gates + deploy por forced command (`scripts/vps/deploy-m2.sh`) |
| 6 | Testes de caracterização D-001..D-003 | ✅ | 3 testes passam congelando os bugs; D-004 já corrigido upstream |
| 7 | `docs/BASELINE.md` | ✅ | 206 testes · 84% · ruff gate 0 · 166 advisory · black 49 |
| 8 | Plano de rollback | ✅ | `docs/R1-PLANO-ROLLBACK.md` |

### Próximos passos da R1

- Type-checker (mypy/pyright) em modo relatório (amarelo: ferramenta nova de dev).
- Lockfile com hashes (D-039).
- Fechar o gate da R1 com revisão humana.

## Bloqueado

| Item | Motivo | Destrava |
| :-- | :-- | :-- |
| D-015 rotação de segredos | **O agente detecta; o humano rotaciona** | rotação de `SECRET_KEY` + MySQL pelo humano |
| D-060 TLS na borda | correção proposta na branch `infra/traefik-global` (fora desta) | merge do PR correspondente |
| D-007 / D-012 / D-046 (migrations) | Migration = vermelho | aprovação explícita + plano de rollback |
| D-016 papel do PDV | Regra de negócio (quem pode vender?) | definição do humano (staff × grupo "Vendedores") |
| D-080 home 500 (produto sem imagem) | Nenhum dado de produção deve ser tocado pelo agente | decisão de dados + correção de template (R2) |

## Handoffs

- `docs/handoffs/` — criado no fim de cada sessão com área e data (AGENTS.md §13).
