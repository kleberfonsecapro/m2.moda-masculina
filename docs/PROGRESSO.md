# PROGRESSO — Quadro Kanban

**Fases do retrofit** (AGENTS.md §4). Colunas: Backlog → Pronto → Em andamento → Em revisão →
Aguardando humano → Feito (+ Bloqueado).

**Estado:** R0 concluído (2026-11-02) · aguardando gate humano para R1.

---

## Fases

| Fase | Status | Saída | Gate |
| :-- | :-- | :-- | :-- |
| **R0** Inventário | ✅ Feito | `docs/00-VISAO.md`, `01-ARQUITETURA.md`, `MAPA-DO-CODIGO.md`, `02-CONTRATOS.md`, `DIVIDA.md` (81 itens), `PROGRESSO.md`, `LOG.md` | ⏳ aguardando humano |
| **R1** Rede de segurança | ⬜ Backlog | `docs/BASELINE.md` | — |
| **R2** Reavaliação de segurança | ⬜ Backlog | `docs/AUDITORIA-SEGURANCA.md` | — |
| **R3** Organização de diretórios | ⬜ Backlog | `docs/ESTRUTURA-ATUAL.md`, `ESTRUTURA-ALVO.md` | — |
| **R4** Endurecimento de infra | ⬜ Backlog | `docs/ESTRUTURA-ALVO.md` + item por item | — |
| **R5** Evolução contínua | ⬜ Backlog | `docs/BACKLOG.md` | — |

## Backlog da R1 (proposto, aguardando aprovação)

| # | Tarefa | Aceitação (comando) | Sev | Risco |
| :-- | :-- | :-- | :-- | :-- |
| 1 | Backup 3-2-1 + **restore testado** | `borg list` mostra dump; restore em banco scratch confere contagem | 🔴 | 🟢 |
| 2 | Fixo do falso verde dos testes (D-030, D-030b) | `docker compose run --rm --no-deps -v "$PWD/backend:/app/backend" web sh -c "python manage.py collectstatic --noinput && python manage.py test"` → **200 testes OK** (receita já validada no R0) | 🟠 | 🟢 |
| 3 | `requirements-dev.txt` + ruff + pytest-cov (D-036, D-039) | `ruff check` verde em modo relatório | 🟠 | 🟡 (amarelo: tool nova) |
| 4 | `core.hooksPath` versionado (D-031) | `git push` executa a suíte | 🟠 | 🟢 |
| 5 | CI de baseline no GitHub Actions (sem deploy) | badge verde; gates em modo relatório | 🟠 | 🟡 |
| 6 | Testes de caracterização de D-001..D-004 | testes vermelhos que reproduzem o bug | 🟠 | 🟢 |
| 7 | `docs/BASELINE.md` | lint/tipos/cobertura/vulns registrados | 🟠 | 🟢 |
| 8 | Plano de rollback | `docs/R1-PLANO-ROLLBACK.md` | 🟡 | 🟢 |

## Bloqueado

| Item | Motivo | Destrava |
| :-- | :-- | :-- |
| D-015 rotação de segredos | **O agente detecta; o humano rotaciona** | rotação de `SECRET_KEY` + MySQL pelo humano |
| D-060 TLS na borda | Muda comportamento público (vermelho) | decisão do humano sobre o domínio/certificado |
| D-007 / D-012 / D-046 (migrations) | Migration = vermelho | aprovação explícita + plano de rollback |
| D-016 papel do PDV | Regra de negócio (quem pode vender?) | definição do humano (staff × grupo "Vendedores") |

## Handoffs

- `docs/handoffs/` — criado no fim de cada sessão com área e data (AGENTS.md §13).
