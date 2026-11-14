# BACKUP 3-2-1 — operação, restore e evidências

**Serviço:** `backup` (profile `backup` do Docker Compose) · **Imagem:** `m2moda-masculina-backup:1.0.0`
**Cadeia:** dump lógico do MySQL → Borg criptografado (`repokey`) → `borg prune` → `rclone sync` offsite → alerta Telegram + heartbeat.

> Por que existe: até a R1 o projeto **não tinha nenhum backup**. Um incidente no MySQL ou no volume
> `media_volume` era perda total de dados (achado **D-059** em `docs/DIVIDA.md`).

---

## 1. Arquitetura

```
┌────────────────┐  dump logico (mysqldump --single-transaction)
│ db (m2-mysql)  │──────────────────────────────────────────┐
│ rede db-network│ (internal)                                ▼
└────────────────┘                    ┌──────────────────────────────────┐
                                      │ backup (m2-backup)               │
                                      │  - mysqldump -> .sql.gz          │
                                      │  - borg create (repokey)         │
                                      │  - borg prune 7d/4w/6m          │
                                      │  - rclone sync --retries 3       │
                                      │  - alerta Telegram + heartbeat   │
                                      └───────┬──────────────────────────┘
                          volume backup_data  │  rede backup-network (egress)
                                      ┌───────▼──────────┐
                                      │ /backup/repo     │  repositório Borg
                                      └───────┬──────────┘
                                              │ rclone sync
                                              ▼
                                   offsite (S3 / B2 / Drive / …)
```

**Rede:** `db-network` (internal) para o MySQL + `backup-network` (egress) para o offsite. Sem porta
publicada. `restart: unless-stopped`. `USER m2backup` (uid/gid fixos 10001) — sem root.
**Imagem:** `debian:bookworm-slim` fixado **por digest**, pacotes com versão fixada.
Debian (e não Alpine) porque o MySQL 8 usa `caching_sha2_password` e o cliente MariaDB do Alpine
não embarca esse plugin.

## 2. Comandos

| Ação | Comando |
| :-- | :-- |
| Subir o serviço | `docker compose --profile backup up -d backup` |
| Backup manual (agora) | `docker compose --profile backup run --rm backup backup` |
| Listar arquivos | `docker compose --profile backup run --rm backup list` |
| **Prova de restore** | `docker compose --profile backup run --rm backup verify` |
| Restaurar manualmente | `docker compose --profile backup run --rm backup restore --latest --target-db <db>` |
| Ver logs | `docker compose logs -f backup` |
| Estado (saúde) | `docker compose --profile backup ps backup` |

O serviço agendado roda sozinho (`command: ["schedule"]`), diariamente às `BACKUP_AT_HOUR` (padrão 02:00).

## 3. Variáveis de ambiente (todas em `.env`, nunca no código)

| Variável | Segredo | Default | Função |
| :-- | :-- | :-- | :-- |
| `BORG_PASSPHRASE` | 🔴 sim | — | Abre o repositório Borg criptografado. Sem ela, o backup aborta. |
| `RCLONE_REMOTE` | não | — | Destino offsite, ex.: `b2:m2-backups` |
| `RCLONE_CONFIG_<REMOTE>_{TYPE,ACCOUNT,KEY,...}` | 🔴 sim | — | Credenciais do remote (config do rclone via ambiente, sem arquivo de segredo em disco) |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | 🔴 sim | — | Alertas. Sem eles, o alerta é **omitido com warning** (exit 10 no helper). |
| `TELEGRAM_DRY_RUN` | não | `0` | `1` = registra o payload sem enviar (validação local) |
| `BACKUP_AT_HOUR` | não | `2` | Hora do backup agendado (TZ do container) |
| `BACKUP_KEEP_DAILY/WEEKLY/MONTHLY` | não | `7/4/6` | Política de retenção do `borg prune` |
| `BACKUP_MAX_AGE_HOURS` | não | `30` | Idade máxima do heartbeat para o healthcheckconsiderar saudável |
| `SERVER_NAME` | não | `m2moda` | Identifica o servidor no alerta |
| `MYSQL_ROOT_PASSWORD` | 🔴 sim | — | Usado pelo dump/restore (privilegios administrativos). Ver §7. |

## 4. Comportamento em falha (caminho triste)

Qualquer comando que falhar aborta o backup **e** dispara alerta **CRÍTICO** no Telegram com nome do
servidor, linha do erro, exit code do Borg e do Rclone:

| Falha | Exit code | Mensagem |
| :-- | :-- | :-- |
| Variável obrigatória ausente | 2 | "Backup abortado antes de iniciar: variaveis ausentes: …" |
| Dump vazio | 3 | "dump logico vazio" |
| Dump sem tabelas | 5 | "dump sem nenhuma tabela (banco vazio ou sem permissao)" |
| `borg init` falhou | rc do borg | "'borg init' falhou" |
| Passphrase incorreta | 6 | "repositorio ... nao pode ser aberto" — **nada é apagado** |
| `borg create` / `borg prune` falhou | rc do borg | "'borg create'/'borg prune' falhou" |
| `rclone sync` falhou | rc do rclone | "offsite 'rclone sync' falhou" (após 3 retries) |
| Verificação de restore com divergência | 1 | "N tabela(s) divergente(s)" |

O `rclone sync` roda **imediatamente** após o Borg, com `--retries 3` (AGENTS.md §4).

## 5. Runbook de restore (incidente real)

```bash
# 1. Ver o que existe no repositorio
docker compose --profile backup run --rm backup list

# 2. (opcional) Restaurar em um banco de teste antes de mexer em producao
docker compose --profile backup run --rm backup restore --latest --target-db m2shop_restore_teste

# 3. Restore real: cria o banco destino vazio e aplica o dump
docker compose exec -T db mariadb -uroot -p"$MYSQL_ROOT_PASSWORD" \
  -e "CREATE DATABASE IF NOT EXISTS m2shop CHARACTER SET utf8mb4;"
docker compose --profile backup run --rm backup restore --latest --target-db m2shop

# 4. Conferir
docker compose --profile backup run --rm backup verify
```

> O dump é gerado **sem** `CREATE DATABASE` (para poder ser aplicado em qualquer banco destino).
> O banco destino precisa existir e estar vazio.

## 6. Evidências da R1 (2026-11-02) — restore **testado**

Ambiente de validação local (containers efêmeros, banco recriado com o schema real das 27 tabelas
do Django + dados de teste).

| # | Teste | Resultado |
| :-- | :-- | :-- |
| 1 | `backup backup` | ✅ dump com **27 tabelas** (7.303 B) → `borg init` (repokey) → `borg create` → `borg prune` → `rclone sync` → heartbeat `status=ok` → alerta Telegram (dry-run). Todos os exit codes = 0 |
| 2 | `borg info` | ✅ `Encrypted: Yes (repokey)` · `Original size 8.29 kB` · `Compressed 8.37 kB` · `Deduplicated 9.32 kB` |
| 3 | `rclone sync` | ✅ repositório Borg completo no offsite (`config`, `data/`, `index.5`, `nonce`, `integrity.5`, `README`) — 108 KB |
| 4 | **`verify` (restore real)** | ✅ extraiu do Borg, restaurou no banco `m2shop_restore_verify` e comparou tabela a tabela: **27 tabelas, 199 linhas, 0 divergências** → exit 0 |
| 5 | **Teste negativo** | ✅ após inserir 1 produto no banco *pós-backup*, o `verify` detectou `Divergencia em catalog_product: origem=2 scratch=1` → **exit 1** + alerta crítico. O detector realmente funciona |
| 6 | `healthcheck` | ✅ `Backup saudavel: … status=ok archive=m2-20261102-204431 duration=1s` |
| 7 | Falha de rclone (permissão) | ✅ capturou `rclone_rc=1`, abortou e enviou alerta crítico (sem mascarar a falha) |

Bugs encontrados **e corrigidos** durante a validação (todos com teste de regressão na execução):

| Bug | Correção |
| :-- | :-- |
| Cliente Alpine sem `caching_sha2_password` → falha de conexão no MySQL 8 | Base trocada para Debian bookworm-slim (o plugin existe em `/usr/lib/x86_64-linux-gnu/libmariadb3/plugin/`) |
| `borg init` falhava por `HOME` inexistente | `HOME=/backup/home` (dentro do volume, com ownership do usuário do serviço) |
| Volume nomeado ficava sem permissão após mudança de imagem | uid/gid **fixos** (10001) no Dockerfile |
| Repositório Borg **parcial** (init interrompido) quebrava o `create` | Detecção de repo válido (`config` + `manifest`); repo parcial é **movido** (não apagado) e reinicializado; passphrase errada **nunca** destrói o repo |
| `borg list \| cut -f2` pegava a data, não o nome do arquivo | `awk '{print $1}'` |
| `borg extract` usava o path como filtro, não como destino | Extração no CWD (`cd $RESTORE_DIR && borg extract …`) |
| `if ! cmd; then rc=$?` devolvia 0 (o `!` inverte o status) | Padrão `cmd || rc=$?` em todos os scripts |
| Dump de banco vazio passava como "sucesso" | Guarda que aborta (exit 5) se o dump não tiver nenhuma `CREATE TABLE` |

## 7. Pendências (nenhum segredo é gerado pelo agente)

1. **Rotacionar `BORG_PASSPHRASE`** — a senha usada na validação é de teste e **não** serve para produção.
2. **Configurar o remote real** (`RCLONE_REMOTE` + `RCLONE_CONFIG_*`) apontando para S3/B2/Drive **com versionamento**.
3. **Token do Telegram** (`TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`) e `TELEGRAM_DRY_RUN=0`.
4. **Usuário de backup dedicado** — hoje o dump usa o `root` do MySQL (necessário para rotinas/triggers e para
   criar o banco scratch da prova). Recomendado: `MYSQL_BACKUP_USER` com `SELECT` em `m2shop` e `ALL` apenas
   no banco scratch. O código já aceita `MYSQL_BACKUP_USER`/`MYSQL_BACKUP_PASSWORD`.
5. **Alerta externo** — o heartbeat (`/backup/heartbeat/last`) é o ponto de integração para um monitor
   (Uptime Kuma, cron de watchdog, etc.).

## 8. Rollback

O serviço de backup **não toca** em `db`, `web` ou `nginx` e está isolado no profile `backup`:
não sobe em `docker compose up -d` normal.

```bash
# Parar e remover o serviço (o volume com o repositorio Borg pode ser preservado)
docker compose --profile backup stop backup
docker compose --profile backup rm -f backup
```

Rollback do código: `git revert <commit>` (o serviço novo não interfere no deploy existente).
Para remover também os dados do backup: `docker volume rm m2moda-masculina_backup_data` — **apenas** se
houver outra copia offsite valida.
