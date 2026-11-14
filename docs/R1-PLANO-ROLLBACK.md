# R1 — plano de rollback

**Princípio:** cada item da R1 é independente e reversível. Nenhuma mudança toca schema, contrato
externo, deploy ou comportamento de produção (a única alteração em `settings.py` vale **apenas**
quando `test` está em `sys.argv`). O rollback é sempre `git revert` do commit correspondente.

## 1. Itens e reversão

| Item | O que mudou | Como reverter | Impacto se reverter |
| :-- | :-- | :-- | :-- |
| Backup 3-2-1 (`a26f1c8`, `b076539`) | serviço `backup` no profile `backup` + scripts em `scripts/backup/` | `docker compose --profile backup down` e `git revert a26f1c8 b076539` | volta a **não ter backup** (D-059) |
| Falso verde dos testes | `scripts/test.sh`, `scripts/lint.sh`, `scripts/coverage.sh`, `settings.py` (só em testes), `backend/requirements-dev.txt`, `pyproject.toml`, `backend/.coveragerc`, README | `git revert <commit>` | README volta a documentar um comando que roda 0 testes |
| Hook pre-push | `scripts/hooks/pre-push`, `scripts/install-hooks.sh`, `core.hooksPath` | `git config --unset core.hooksPath` + `git revert <commit>` | push deixa de rodar a suíte localmente |
| Caracterização D-001..D-003 | testes novos nos apps | `git revert <commit>` | perde-se a rede que prova a correção da R2 |

## 2. Backup: rollback sem perder dados

O serviço de backup **não toca** em `db`, `web` ou `nginx` e não sobe no `docker compose up -d`
normal (está no profile `backup`). Para desativar:

```bash
docker compose --profile backup stop backup
docker compose --profile backup rm -f backup
```

O volume `m2moda-masculina_backup_data` (repositório Borg) **é preservado** — só remova com
`docker volume rm` se houver outra cópia offsite válida (ver `docs/BACKUP.md` §8).

## 3. Restauração de dados (incidente)

O rollback de **código** não recupera dados. Se a R1 precisar ser usada para reverter um incidente:

1. `docker compose --profile backup run --rm backup list` — escolher o arquivo anterior ao incidente.
2. `docker compose --profile backup run --rm backup verify` — provar que o backup restaura.
3. Seguir o runbook de `docs/BACKUP.md` §5 (restore em banco scratch e depois no banco real).

## 4. Critérios de abortar a R1

- Suíte fica vermelha por causa de uma mudança da R1 (não do código legado).
- Backup falha ou a prova de restore acusa divergência.
- Qualquer item exigir mudança de schema, contrato externo ou deploy (vermelho no AGENTS.md §12).

Nesses casos: parar, registrar em `docs/LOG.md` e reverter o item — não "consertar por cima".
