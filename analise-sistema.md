# 🌿 Análise do Sistema BM Monteiro — Menina dos Raios

> Avaliação completa do sistema de controle de vendas.  
> **Data da análise:** 27/07/2026  
> **Versão analisada:** Frontend React + Backend FastAPI v15 + Interface legada HTML

---

## 📊 Resumo Executivo

O sistema **BM Monteiro** é uma ferramenta sólida para controle de vendas da Menina dos Raios Ltda, com funcionalidades bem pensadas (importação Excel, verificação NF-e Sebrae, gráficos anuais). A **nova interface React** mostra evolução clara em UX, especialmente no mobile. Porém, há **problemas estruturais críticos** que precisam de atenção imediata para evitar dívida técnica e riscos operacionais.

---

## ✅ O que está MUITO BOM

| # | Aspecto | Por que é bom |
|---|---------|---------------|
| 1 | **Mobile-first** | FAB (botão flutuante), Drawer, cards em vez de tabela no celular. Busca colapsível. Experiência pensada para quem trabalha no campo. |
| 2 | **UX refinada** | Skeleton loaders, toast notifications (Sonner), indicador online/offline, feedback visual imediato em todas as ações. |
| 3 | **Segurança de senhas** | bcrypt com cost 12, migração transparente SHA-256 → bcrypt. Boa prática. |
| 4 | **Funcionalidades de negócio** | Importação Excel do SharePoint, verificação NF-e via PDF do Sebrae, histórico de importações, gráfico SVG leve. |
| 5 | **Identidade visual coerente** | Paleta verde alinhada à marca, badges coloridos por tipo de venda (NF, PR, Avulso, Avaria). |
| 6 | **Stack moderna (nova interface)** | React 19, TanStack Router + Query, Tailwind v4, shadcn/ui — stack atual e bem mantida. |

---

## ⚠️ Problemas Críticos (resolver primeiro)

### 1. 🔴 Duas interfaces paralelas — risco de divergência

**Problema:** Você mantém duas UIs completas:
- **Legada:** `backend/static/index.html` — 17.202 linhas de vanilla JS
- **Moderna:** `frontend/` — React + TanStack

Qualquer bug, nova funcionalidade ou ajuste de cor precisa ser feito em **dois lugares**. Isso não é sustentável.

**Solução:**
- **Curto prazo:** Escolha uma como principal. A React é superior em todos os aspectos.
- **Médio prazo:** Se precisar manter o HTML legado, transforme-o em um "thin client" que consome a mesma API REST (`/api/sales`, etc.), removendo toda a lógica de negócio do frontend.

---

### 2. 🔴 `index.html` legado tem 17.000 linhas em 1 arquivo

**Problema:** Um único arquivo HTML/CSS/JS de 17KB+ de código é impossível de debugar, revisar ou manter. Um bug pode estar em qualquer lugar.

**Solução:**
- Não invista mais tempo nele. Foque 100% na migração para o React.
- Ou, se ainda precisa dele, divida em módulos JS (mesmo vanilla) com `<script type="module">`.

---

### 3. 🔴 API hardcoded para `localhost`

**Arquivo:** `frontend/src/lib/sales.ts`  
**Código problemático:**
```ts
const API = "http://localhost:8765";
```

**Problema:** O sistema só funciona no ambiente local. Em produção (Hostinger), em outra máquina, ou no APK mobile, essa URL quebra.

**Solução:**
```ts
// .env
VITE_API_URL=http://localhost:8765

// lib/sales.ts
const API = import.meta.env.VITE_API_URL || "http://localhost:8765";
```

---

### 4. 🔴 Meta tags e SEO com dados da plataforma Lovable

**Arquivo:** `frontend/src/routes/__root.tsx`

**Problemas encontrados:**
- Título: `"Vendas jan dez 2026"` (hardcoded, sem sentido)
- Author: `"Lovable"`
- Twitter site: `"@Lovable"`
- OG Image: URL da Lovable, não da sua marca

**Impacto:** Quando alguém compartilha o link, aparece informação errada. SEO prejudicado.

**Solução:**
```tsx
{ title: "BM Monteiro — Controle de Vendas" }
{ name: "author", content: "Menina dos Raios Ltda" }
{ name: "description", content: "Sistema de controle de vendas NF, Produtor Rural, Avulso e Avaria." }
// Substitua OG image por um da sua marca
```

---

### 5. 🔴 Backend `app.py` tem 6.444 linhas em 1 arquivo

**Problema:** Todo o backend (rotas, modelos, lógica de negócio, utilitários, importação Excel, verificação PDF) está em um único arquivo. Isso dificulta:
- Testes isolados
- Code review
- Trabalho em equipe
- Manutenção

**Solução:** Modularizar em estrutura de pastas:
```
backend/
├── app.py              # Entry point (mínimo)
├── routers/
│   ├── sales.py        # /api/sales
│   ├── auth.py         # /api/auth
│   └── sebrae.py       # /api/sebrae/verify-nf
├── services/
│   ├── sales_service.py
│   └── sebrae_service.py
├── models/
│   ├── schemas.py      # Pydantic models
│   └── database.py     # SQLite connection
├── utils/
│   ├── security.py     # bcrypt, sessions
│   └── formatters.py
└── tests/
```

---

## 🟡 Problemas Importantes (resolver em seguida)

### 6. 🟡 Falta paginação na listagem

**Problema:** Todas as vendas são carregadas de uma vez (`listSales()` sem paginação). Com 1.000, 5.000 ou 10.000 registros, o navegador vai travar.

**Solução:**
- Adicionar paginação server-side: `?page=1&limit=50`
- Ou usar virtual scroll (TanStack Virtual) para grandes listas

---

### 7. 🟡 Gráfico anual só mostra o ano atual

**Problema:** O `ConsolidadoChart` recebe `year = new Date().getFullYear()` fixo. Não dá pra ver 2025, 2024, etc.

**Solução:** Adicionar um `<Select>` para escolher o ano no header do card do gráfico.

---

### 8. 🟡 Tabela sem ordenação nem filtros avançados

**Problema:** Não dá pra ordenar por data, valor, cliente. Nem filtrar por período ("mostrar só de julho").

**Solução:**
- Ordenação clicando no header da coluna
- Filtros rápidos: "Este mês", "Mês passado", "Últimos 30 dias"

---

### 9. 🟡 Inconsistência de autenticação

**Problema:**
- Interface React usa **Supabase auth** (OAuth Google + email/senha)
- Backend FastAPI tem **próprio sistema de auth** (sessões + bcrypt + SQLite)

Isso cria duas fontes de verdade para usuários. Se um usuário é criado no Supabase, o backend FastAPI não sabe dele.

**Solução:** Escolha UMA fonte de verdade:
- **Opção A (recomendada):** Use o auth do FastAPI para tudo. Remova Supabase da nova interface.
- **Opção B:** Use Supabase como fonte de verdade e faça o FastAPI validar tokens JWT do Supabase.

---

### 10. 🟡 Busca limitada

**Problema:** A busca só procura em `client`, `product`, `nf_number`. Não busca por data, valor ou tipo.

**Solução:** Adicionar filtros combinados: busca + tipo + intervalo de datas.

---

### 11. 🟡 Sem exportação de dados

**Problema:** Dá pra importar Excel, mas não dá pra exportar. Isso é fundamental para:
- Relatórios para contador
- Backup portátil
- Análise externa

**Solução:** Adicionar botão "Exportar Excel/CSV/PDF" que gera arquivo com os dados filtrados.

---

### 12. 🟡 Sem validação de schema no formulário

**Problema:** Embora use `react-hook-form`, não há validação com Zod ou similar. Campos numéricos aceitam texto livre. `parseBR` pode falhar silenciosamente.

**Solução:**
```ts
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

const schema = z.object({
  client: z.string().min(1, "Informe o cliente"),
  quantity: z.number().positive("Quantidade deve ser maior que zero"),
  unit_price: z.number().positive("Preço deve ser maior que zero"),
  sale_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Data inválida"),
});
```

---

### 13. 🟡 Offline detectado, mas sem funcionalidade real

**Problema:** O `ConnectivityPill` mostra "Online/Offline", mas quando fica offline:
- Não dá pra cadastrar vendas
- Não há fila de ações para sincronizar depois

**Impacto:** Em áreas rurais (relevante para "Produtor Rural"), a conectividade é instável.

**Solução:** Implementar fila offline com localStorage/IndexedDB:
1. Usuário cadastra venda offline → salva na fila
2. Quando voltar online → sincroniza automaticamente
3. Mostra badge "X vendas pendentes"

---

### 14. 🟡 Repositório poluído com backups

**Problema:** Dezenas de arquivos `.backup-*`, `.bak-*` espalhados em `backend/`, raiz, etc. Isso:
- Aumenta o tamanho do repositório
- Cria confusão sobre qual arquivo é o "oficial"
- Pode vazar dados antigos

**Solução:**
```gitignore
# Adicionar ao .gitignore
*.backup-*
*.bak-*
*.db
backups/
```
Mover backups para fora do repo ou usar `git-lfs`.

---

## 🟢 Oportunidades de Melhoria (diferenciais)

| # | Oportunidade | Impacto |
|---|--------------|---------|
| 15 | **Dashboard com KPIs avançados** | Ticket médio, vendas por cliente top, produtos mais vendidos, comparativo ano a ano |
| 16 | **Notificações de lembrete** | Alerta quando uma NF do Sebrae ainda não foi lançada após X dias |
| 17 | **Modo escuro** | O legado já tem `data-theme`, mas a nova interface não implementou |
| 18 | **Autocompletar cliente/produto** | Baseado em vendas anteriores, evita digitação repetida |
| 19 | **Multi-empresa/multi-conta** | Se houver outras marcas (Menina da Estrada?), estruturar para múltiplas entidades |
| 20 | **Testes automatizados** | Unitários para `parseBR`, `formatBRL`, e2e para fluxo de cadastro de venda |

---

## 📋 Plano de Ação Priorizado

### Semana 1 — Crítico
- [ ] Definir a interface React como principal; congelar desenvolvimento no HTML legado
- [ ] Extrair API URL para variável de ambiente (`VITE_API_URL`)
- [ ] Corrigir meta tags (título, author, OG image)

### Semana 2 — Estrutural
- [ ] Modularizar `app.py` em routers/services
- [ ] Unificar autenticação (escolher FastAPI ou Supabase)
- [ ] Adicionar `.gitignore` para backups e banco de dados

### Semana 3 — UX
- [ ] Adicionar paginação na listagem
- [ ] Permitir seleção de ano no gráfico
- [ ] Adicionar ordenação na tabela
- [ ] Implementar filtros por período

### Semana 4 — Funcional
- [ ] Exportar Excel/CSV/PDF
- [ ] Validar formulário com Zod
- [ ] Iniciar fila offline (localStorage)

---

## 🏁 Conclusão

O sistema tem uma **base sólida** e funcionalidades que realmente resolvem problemas do negócio. A nova interface React demonstra preocupação genuína com UX mobile, o que é raro em sistemas B2B/agrícola.

O maior risco atual é a **fragmentação entre as duas interfaces** e a **monolitação do backend** em um único arquivo. Resolver esses pontos estruturais vai permitir que o sistema escale sem dor.

**Nota geral:** 7/10 — Bom sistema, com potencial para ser excelente após ajustes estruturais.
