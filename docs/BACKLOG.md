# BACKLOG — Itens de evolução (pós-R1)

Formato: ID | Título | Descrição | Status | Origem | Prioridade | Esforço | Dependências

---

## Funcionalidades de Carrinho/Checkout

| ID | Título | Descrição | Status | Origem | Prioridade | Esforço | Dependências |
|:--|:--|:--|:--|:--|:--|:--|:--|
| B-001 | Modal de opções pós "Adicionar ao Carrinho" | Após clicar em "Adicionar ao Carrinho", exibir modal com: produtos relacionados, opção de continuar comprando, ir para carrinho, escolher mais variantes do mesmo produto (cores, tamanhos adicionais), acessórios sugeridos. Hoje vai direto para o carrinho ou fica na página. | ⬜ Backlog | Usuário (2026-11-14) | 🟠 Alta | M | Requer ajuste no `handleBuy()` (product_detail.html) + novo modal/template |
| B-002 | WhatsApp no finalização do pedido (vendedor) | Ao confirmar o pedido (checkout), enviar mensagem automática via WhatsApp para número do vendedor configurado, contendo: número do pedido, itens (nome, variante, qtd, preço), subtotal, frete, total, dados de entrega (nome, endereço, telefone), observações. Usar `wa.me` com texto pré-formatado. | ⬜ Backlog | Usuário (2026-11-14) | 🔴 Crítica | M | Requer: campo `whatsapp_seller` no settings/env, hook no `Order.save()` ou view de checkout, template de mensagem |
| B-003 | WhatsApp no PDV (vendas balcão) | No modo PDV (`mobile/sales`), ao confirmar venda, enviar WhatsApp para vendedor com resumo da venda. | ⬜ Backlog | Usuário (2026-11-14) | 🟡 Média | P | Mesmo padrão do B-002, reaproveita lógica |
| B-004 | Melhoria no seletor de variantes no carrinho | Permitir trocar variante (tamanho/cor) diretamente no carrinho sem remover e adicionar novamente. | ⬜ Backlog | Análise código | 🟡 Média | M | Requer endpoint `update_cart` aceitar `variant_id` |

---

## Itens JÁ IMPLEMENTADOS (referência)

| ID | Título | Descrição | Status | Evidência |
|:--|:--|:--|:--|:--|
| I-001 | Seletor de variantes na página do produto | Tamanhos exibidos como botões antes de adicionar ao carrinho; validação de estoque. | ✅ Implementado | `product_detail.html:58-75`, `selectVariant()` JS |
| I-002 | Botão WhatsApp na página do produto | Botão "WhatsApp" abre `wa.me` com produto e preço pré-preenchidos. | ✅ Implementado | `product_detail.html:95-97` |
| I-003 | Botão WhatsApp flutuante no site | Botão fixo no canto inferior direito abre WhatsApp genérico. | ✅ Implementado | `base.html:177-179` |
| I-004 | Checkout com formulário de entrega | Formulário completo (nome, endereço, CEP, cidade, estado, telefone) + cálculo de frete via CEP. | ✅ Implementado | `checkout.html`, `shipping:quote` view |
| I-005 | PDV (Vendas Balcão) com modal de checkout | Modo mobile PDV: carrinho, cálculo de frete, modal de checkout com telefone/WhatsApp opcional, confirmação. | ✅ Implementado | `mobile/sales/sales_page.html`, `catalog:sales_checkout` |
| I-006 | Carrinho com +/- e remover padronizados | Botões de quantidade e lixeira seguem mesmo padrão visual (desktop e mobile). | ✅ Implementado | Commit `6f37244`, `style.css`, `mobile/app.css` |
| I-007 | Cálculo de frete por CEP | Integração com API de frete no carrinho e checkout; seleção de modalidade. | ✅ Implementado | `cart.html`, `checkout.html`, `shipping` app |
| I-008 | Admin Django funcional | Painel admin em `/admin/` com superusuário `admin` / `123456`. | ✅ Implementado | `seed.py`, reset de senha executado |

---

## Dívidas Técnicas Relacionadas (de `docs/DIVIDA.md`)

| ID | Título | Status | Notas |
|:--|:--|:--|:--|
| D-004 | `ExportOrdersView` erro 500 | ⬜ Backlog | `get_queryset` sem `self.request` |
| D-016 | Papel do PDV (quem pode vender?) | ⬜ Backlog | Definir: staff × grupo "Vendedores" |
| D-060 | TLS na borda (nginx redirect) | ✅ Resolvido | ADR-001, commit `25a8ce3` |
| D-080 | Home 500 (produto sem imagem) | ⬜ Backlog | Template não trata imagem nula |

---

## Critérios de Aceite (DoD) para novos itens

- [ ] Testes de regressão passam (`scripts/test.sh` → 200+ testes OK)
- [ ] Lint limpo (`scripts/lint.sh` → 0 erros)
- [ ] Cobertura não cai abaixo do baseline (84%)
- [ ] Documentação atualizada (`LOG.md`, `PROGRESSO.md`, `CHANGELOG.md`)
- [ ] Commit convencional (`fix:`, `feat:`, `docs:`) com "porquê"
- [ ] PR pequeno (< 400 linhas) se for código novo

---

## Próximos Passos Sugeridos

1. **B-001** (Modal pós add-to-cart) — MVP: modal simples com "Continuar comprando" / "Ver carrinho" / "Escolher mais opções"
2. **B-002** (WhatsApp no checkout) — Definir `WHATSAPP_SELLER_NUMBER` no `.env`, criar template de mensagem, integrar no `Order` model ou view de checkout
3. Revisar D-016 (papel PDV) — necessário para B-003