# Menina dos Raios ERP

Aplicacao de gestao operacional para vendas, entregas, boletos, notas, orcamentos, pagamentos, calendario e integracoes de comunicacao.

Versao atual do servidor: `2.0.0`

Este repositorio contem a versao estavel da aplicacao, mantida no checkpoint `88fef18` e implantada como versao de servidor `2.0.0`. O foco desta versao e manter os modulos atuais operando com seguranca, preservando contratos existentes, dados persistentes e integracoes em producao.

## Estado da Versao Estavel

Dominios finalizados no ciclo atual:

- Notas APP;
- Calendario APP;
- WhatsApp;
- Boletos e Pagamentos;
- remocao da funcionalidade de Import Excel.

A funcionalidade de upload/importacao Excel foi removida por nao fazer mais parte do uso atual. Dados historicos, tabelas, compatibilidades e rotas auxiliares necessarias para registros antigos foram preservados quando aplicavel.

Deploy controlado por pacote `.zip`, preservando configuracoes locais, bancos, uploads, logs, backups e sessoes de integracao. O componente WhatsApp/Baileys permanece no ciclo de producao validado com Baileys 6.7.x; Baileys 7 RC segue bloqueado para producao ate novo ciclo especifico.

## Qualidade e Validacao

A linha de base validada antes deste ciclo registra:

- `327 passed` na suite completa de testes;
- duas execucoes consecutivas bem-sucedidas;
- validacao de sintaxe dos modulos Python relevantes;
- verificacao de integridade com `git diff --check`.

Os testes usam ambiente temporario e bloqueiam chamadas externas reais quando aplicavel.

As correcoes locais dos bloqueios do ciclo 5 elevaram a cobertura para `331 passed`, novamente em duas execucoes completas consecutivas. Essa validacao continuou exclusivamente local, sem staging, deploy ou envio real.

## Arquitetura Geral

O backend principal e baseado em FastAPI com persistencia SQLite. O frontend principal servido pela aplicacao fica em `backend/static/index.html`.

Modulos internos da aplicacao incluem:

- `backend/app_notes_domain.py`;
- `backend/app_notes_service.py`;
- `backend/backup_admin.py`;
- `backend/company_config.py`;
- `backend/monteiro_periods.py`;
- `backend/monteiro_permissions.py`;
- `backend/orcamentos.py`;
- `backend/permissions_tabs.py`;
- `backend/security_auth.py`;
- `backend/security_request.py`;
- `backend/schemas.py`;
- `backend/utils.py`.

Rotas, infraestrutura de banco, autenticacao, autorizacao, migracoes e regras de negocio que dependem do contexto da aplicacao permanecem no backend principal.

## APK Android

Este repositorio tambem contempla o aplicativo Android interno **Menina dos Raios Vendas**. O app complementa o sistema web e e usado em operacoes de campo e rotinas moveis.

Em alto nivel, o aplicativo permite:

- montar pedidos no celular;
- enviar pedidos pelo fluxo integrado do sistema;
- consultar e informar entregas;
- usar o mesmo login e senha do sistema web;
- desbloquear o app com PIN local de 4 digitos apos o login inicial.

### Estrutura do app

O codigo-fonte do aplicativo Android fica no projeto `VendasWhatsApp/`.

O APK oficial compilado usa o nome padrao:

```text
Menina-dos-Raios-Vendas-OFICIAL.apk
```

O arquivo APK pode ou nao estar versionado no Git, conforme a politica operacional do ambiente. O item mais importante para manutencao e auditoria e o projeto Android fonte, pois o APK deve ser gerado a partir dele.

### Build e publicacao do APK

O APK deve ser compilado localmente com Android Studio ou Gradle, em uma maquina autorizada. A assinatura do aplicativo usa uma chave privada mantida apenas nas maquinas dos desenvolvedores autorizados.

Depois da compilacao e assinatura, o APK e publicado em um servidor de atualizacoes usado pelo proprio app. O projeto possui um script de publicacao, por exemplo `PUBLICAR_APK.bat`, que executa o fluxo operacional de alto nivel:

1. localiza o APK oficial gerado;
2. extrai `versionName`, `versionCode` e identificador do pacote;
3. calcula o hash SHA-256 do APK;
4. atualiza o catalogo de versao usado pelo app;
5. envia o APK e os metadados para o servidor de atualizacoes via SSH/SCP.

Detalhes de infraestrutura, como servidor, usuario, portas, caminhos remotos, provedor, senhas e chaves, nao devem aparecer no README nem ser versionados.

### Seguranca do APK

Nunca commitar:

- keystores ou certificados privados de assinatura;
- senhas de servidor;
- arquivos `.env`;
- configuracoes locais com dados de infraestrutura;
- scripts locais contendo segredos;
- tokens, chaves de API ou credenciais.

O `.gitignore` deve excluir arquivos sensiveis, como keystore, configuracoes locais privadas, bancos de dados, logs, backups, ambientes virtuais e artefatos temporarios. Caso um novo arquivo sensivel seja criado durante manutencao, ele deve ser incluido no `.gitignore` antes de qualquer commit.

### Uso pelo usuario final

O usuario final deve instalar o app apenas a partir de fonte confiavel, como o canal oficial interno da empresa ou link disponibilizado pela equipe responsavel.

Fluxo basico de uso:

1. baixar o APK oficial de fonte confiavel;
2. instalar no Android;
3. abrir o app;
4. fazer login com usuario e senha do sistema;
5. criar um PIN local de 4 digitos;
6. usar as funcionalidades disponiveis, como pedidos e entregas.

O PIN de 4 digitos e local do aparelho e nao substitui a senha do sistema web. Ele serve apenas para desbloquear o app apos o login inicial.

## Pacote de Atualizacao

A distribuicao empacotada da versao estavel deve usar o nome:

```text
bm_app_refatorado_88fef18.zip
```

O pacote publicado nao deve conter:

- credenciais, tokens, chaves privadas ou arquivos `.env`;
- bancos de dados locais ou dados persistentes;
- uploads, logs, caches, backups ou artefatos temporarios;
- ambientes virtuais ou `node_modules`;
- metadados Git.

O checksum SHA-256 deve ser publicado junto ao pacote quando o arquivo for disponibilizado.

## Atualizador Seguro

O arquivo `atualizarrefatorado.bat` e fornecido como modelo operacional
bloqueado por padrao. Ele deve iniciar em modo de simulacao e exigir
configuracao explicita antes de qualquer conexao externa.

O script nao deve conter credenciais, caminhos privados ou comandos de servico
na versao publica. Detalhes de infraestrutura devem ser preenchidos apenas por
operador autorizado em copia operacional local.

## Instalacao e Atualizacao

A implantacao deve ser feita somente por operador autorizado.

Fluxo generico recomendado:

1. Fazer backup consistente dos dados persistentes existentes.
2. Validar variaveis de ambiente e configuracoes fora do repositorio.
3. Conferir o checksum do pacote recebido.
4. Substituir apenas arquivos de aplicacao, preservando bancos, uploads, logs e configuracoes locais.
5. Executar validacoes de sintaxe e testes cabiveis antes de liberar uso.
6. Executar migracoes somente quando houver instrucao explicita e janela de manutencao aprovada.

Credenciais e configuracoes de producao devem ser fornecidas fora do repositorio e nunca devem ser versionadas.

## Uso Local

Requisitos gerais:

- Python 3.10 ou superior;
- dependencias Python listadas em `backend/requirements.txt`;
- ambiente com suporte a FastAPI e SQLite.

Comandos locais uteis:

```bat
python -m py_compile backend\app.py
python -X faulthandler -m pytest -q tests
```

Scripts operacionais incluidos no repositorio devem ser revisados antes de uso e executados apenas em ambiente autorizado.

## Clientes: WhatsApp e Pedidos

Esta branch prepara duas sub-abas dentro de **Clientes**: **WhatsApp** e **Pedidos**. O desenvolvimento e validado somente em ambiente local. Nao existe envio automatico, conversao automatica de pedidos, alteracao de estoque ou mudanca de vendas.

Nao existe ambiente de staging configurado para este ciclo. Nenhum envio real, deploy, acesso remoto ou alteracao de sessao Baileys foi executado durante o desenvolvimento e os testes locais.

### Arquitetura inicial

- `backend/domains/whatsapp_states.py`: contratos e estados previstos para mensagens, conversas, consentimento e pedidos;
- `backend/domains/whatsapp_policies.py`: normalizacao de telefone, comandos de controle, idempotencia, elegibilidade de campanha e bloqueios de duplicidade;
- `backend/services/whatsapp_calculation_service.py`: simulacao pura de consumo, avaria, estoque, limite e quantidade sugerida;
- `backend/static/js/client_whatsapp.js`: apresentacao local de clientes e telefones na sub-aba WhatsApp;
- `backend/static/js/client_orders.js`: estados, filtros e estado vazio da sub-aba Pedidos;
- `backend/static/css/client_whatsapp.css` e `backend/static/css/client_orders.css`: layout responsivo das novas sub-abas.

O servico Baileys existente em `baileys-api/server.js` continua sendo a unica conexao WhatsApp. O listener `messages.upsert` e instalado no mesmo `sock`; nenhuma segunda instancia, sessao ou rotina de QR Code e criada.

## Vendedores e Produtividade

O sistema diferencia **quem vendeu** de motorista, entregador ou usuario que digitou a venda. O vendedor fica cadastrado na entidade `sellers`, separado por empresa, com nome normalizado para evitar duplicidades por acento, maiusculas, espacos extras ou pontuacao simples.

Vendas novas exigem um vendedor ativo:

- Menina dos Raios grava `seller_id` e `seller_name_snapshot` em `sales`;
- Menina da Estrada usa o mesmo modelo em seu banco da empresa;
- Monteiro grava `seller_id` e `seller_name_snapshot` em `paladar_sales`;
- registros antigos sem vendedor permanecem validos e aparecem como `Nao informado`;
- orcamentos continuam fora deste escopo.

O snapshot preserva o nome usado no momento da venda mesmo se o cadastro do vendedor for renomeado depois. O historico de nomes fica em `seller_history`. Entregador, motorista e veiculo continuam campos logisticos independentes e nao sao usados para inferir produtividade de venda.

A produtividade principal pode ser filtrada por vendedor sem alterar os totais quando o filtro estiver em **Todos os vendedores**. As formulas atuais foram preservadas: receita soma vendas que nao sao avaria, avarias somam `sale_type = AVARIA`, liquido e projecao usam receita menos avarias, e dias produtivos continuam baseados nos dias com venda. No Monteiro, a produtividade por vendedor usa a mesma base do painel: receita `SUM(total)`, vendas `COUNT(DISTINCT sale_group)`, ticket medio por grupo e dias produtivos por data.

Permissoes seguem o RBAC existente pelo modulo `vendedores`. Cargos gerenciados continuam em negacao padrao ate receberem permissao explicita; administradores mantem acesso integral. O escopo e validado por area e empresa: permissao de Monteiro nao libera automaticamente a tela principal, permissao de Menina dos Raios nao libera Menina da Estrada, e Monteiro usa vendedores apenas quando o request declara o contexto Monteiro/Raios. Atribuir vendedor em vendas novas ou edicoes exige pelo menos `vendedores.view` no contexto correto, alem das permissoes ja existentes de venda/produto.

A migracao incremental cria `sellers`, `seller_history` e adiciona as colunas de vendedor em `sales` e `paladar_sales` por meio do runner oficial `apply_sellers_schema()` em `backend/repositories/sellers_repository.py`. O runner inspeciona tabelas, colunas e indices, adiciona somente o que falta, bloqueia schema parcial com erro claro e usa savepoint para reverter falhas durante a tentativa. O arquivo SQL `20260916_sellers_up.sql` documenta as estruturas auxiliares e deve ser tratado como migração de aplicação única; para reaplicacao segura, inclusive apos `20260916_sellers_down.sql`, use o runner oficial.

Limitação SQLite: `ALTER TABLE ADD COLUMN IF NOT EXISTS` e rollback fisico de colunas nao sao portaveis em todas as versoes suportadas. Por isso, o rollback `20260916_sellers_down.sql` remove indices e tabelas auxiliares, mas preserva `seller_id` e `seller_name_snapshot` em `sales` e `paladar_sales`. Rollback fisico completo dessas colunas exige restauracao de backup validado ou rebuild controlado em ciclo separado. Vendas antigas nao recebem preenchimento automatico e continuam aparecendo como `Nao informado`.

### Fluxos previstos

Uma mensagem recebida devera ser identificada por empresa, ID externo, JID, horario e hash do evento. A chave de idempotencia e deterministica e inclui a empresa, impedindo que o mesmo evento seja tratado como novo em repeticoes do Baileys. Antes de criar um pedido, o servico futuro devera verificar mensagem processada, pedido aberto na conversa, chave repetida, confirmacao anterior e pedido recente do cliente. Uma ocorrencia suspeita deve ficar em `duplicado_suspeito` para revisao humana.

Estados de conversa preparados:

```text
nova, aguardando_resposta, identificando_produto, coletando_quantidade,
coletando_avaria, calculando_reposicao, aguardando_confirmacao,
pedido_rascunho, aguardando_aprovacao, concluida, cancelada,
atendimento_humano, opt_out
```

Estados de pedido preparados:

```text
rascunho, aguardando_confirmacao, aguardando_aprovacao, aprovado,
cancelado, convertido_em_venda, erro, duplicado_suspeito
```

Permissoes propostas para endpoints futuros:

```text
whatsapp.view, whatsapp.view_messages, whatsapp.view_suggestions,
whatsapp.create_manual_batch, whatsapp.send_manual, whatsapp.manage_connection,
whatsapp.manage_consent, whatsapp.manage_consumption,
whatsapp.manage_damage, whatsapp.view_orders, whatsapp.approve_order,
whatsapp.convert_order, whatsapp.view_audit
```

Ocultar controles no navegador nao substitui autorizacao. Cada rota valida no backend a permissao e a empresa da sessao. Os modulos sensiveis `clientes_whatsapp_sugestoes`, `clientes_whatsapp_lotes` e `clientes_whatsapp_envio` nao sao concedidos automaticamente a cargos existentes.

### Consumo e avarias

O simulador calcula reposicao de avaria, necessidade e quantidade sugerida com `Decimal`. Valores negativos sao rejeitados, a sugestao nunca fica abaixo de zero e somente aplica teto quando o consumo maximo estiver configurado. A memoria textual do calculo e devolvida junto do resultado para futura auditoria. Nenhuma venda ou movimentacao de estoque e criada.

### Execucao e testes

```bat
python -m py_compile backend\domains\whatsapp_states.py backend\domains\whatsapp_policies.py backend\services\whatsapp_calculation_service.py
python -X faulthandler -m pytest -q tests\test_client_whatsapp_foundation.py
node tests\js\test_client_whatsapp_foundation.js
python -X faulthandler -m pytest -q tests
```

### Backup e rollback desta etapa

O backup anterior as alteracoes esta em `backups/client_whatsapp_orders_20260914_215124/`, acompanhado de `MANIFESTO.txt` e hashes SHA-256. Para rollback manual, restaure apenas os arquivos listados no manifesto e remova somente os arquivos novos desta etapa. Nao use comandos que descartem outras alteracoes locais.

Limitacoes da primeira etapa: nao havia persistencia de conversa/pedido ou endpoints dedicados. O ciclo seguinte, descrito abaixo, prepara essas estruturas somente no ambiente local.

### Ciclo persistente local

O segundo ciclo adiciona uma camada persistente local e endpoints protegidos. A migracao `backend/migrations/20260914_whatsapp_orders_up.sql` cria conversas, mensagens, eventos, consentimento, rascunhos de pedidos, itens, historico, consumo e avarias. O rollback correspondente remove somente essas estruturas e preserva `clients`, `product_prices`, `sales`, `whatsapp_contacts` e demais tabelas anteriores.

`whatsapp_contacts` continua sendo a tabela legada da aba principal WhatsApp. Ela nao foi reconstruida para evitar risco sobre contatos existentes. O vinculo seguro com `clients` e o telefone normalizado ficam nas estruturas novas de consentimento, conversa e mensagem.

Endpoints locais preparados:

```text
GET  /api/whatsapp/status
GET  /api/clients/{client_id}/whatsapp
GET  /api/clients/{client_id}/whatsapp/conversations
GET  /api/whatsapp/conversations
GET  /api/whatsapp/conversations/{conversation_id}
GET  /api/whatsapp/orders
GET  /api/whatsapp/orders/{order_id}
GET  /api/clients/{client_id}/consumption
PUT  /api/clients/{client_id}/consumption
GET  /api/clients/{client_id}/damages
POST /api/clients/{client_id}/damages
POST /api/whatsapp/webhooks/incoming
```

Todos exigem a sessao existente, usam a empresa corrente e fecham a conexao em `finally`. O webhook publico continua reservado a simulacoes autenticadas. A recepcao real usa o canal interno descrito abaixo e nunca responde, cria venda, altera estoque ou aprova pedido.

No RBAC atual, as capacidades sao representadas pelos modulos `clientes_whatsapp` e `clientes_pedidos`, combinados com as acoes existentes (`view`, `create`, `edit`, `approve` e outras). Isso implementa negacao padrao para cargos gerenciados. A lista detalhada `whatsapp.*` permanece como vocabulario de dominio para uma futura evolucao do RBAC. Administrador continua protegido; nenhum cargo novo recebe acesso amplo automaticamente. Envio, aprovacao e conversao nao possuem endpoint neste ciclo.

#### Decisoes de dados

- Telefone armazenado para integracao: E.164 com `+55`; JID separado no formato usado pelo Baileys. Prefixos `00` sao removidos e numeros nacionais de 10 ou 11 digitos recebem `55`.
- Nono digito: nenhum digito e criado ou removido por heuristica. Casos antigos/ambiguos ficam `PENDENTE` de regra e revisao manual.
- Telefone invalido: evento rejeitado antes da escrita. Dois clientes ativos com o mesmo telefone normalizado tambem impedem associacao automatica.
- Unicidade de mensagem: `(company_key, instance_key, external_message_id)` e `(company_key, idempotency_key)` sao unicos. Repeticao retorna o registro existente sem nova conversa, evento ou pedido.
- Consentimento ausente nao equivale a opt-in. Uma conversa iniciada pelo cliente pode ser registrada, mas nao autoriza campanha. `SAIR`, `PARAR`, `STOP` e `CANCELAR` registram opt-out.
- Retomada apos opt-out: `PENDENTE`. Nao existe reativacao automatica; exigira origem e trilha de auditoria definidas.
- Avaria nasce como `informada`. Os estados futuros sao `aprovada`, `reposta` e `rejeitada`; este ciclo nao oferece transicao nem reposicao real.
- Percentual de reposicao fica entre 0 e 100 e o responsavel e registrado. Aprovacao e responsavel final pela reposicao continuam `PENDENTE`.
- Pedido permanece rascunho persistente. Confirmacao, aprovacao, cancelamento e conversao nao possuem comandos ativos. O preco unitario e gravado no item como fotografia do calculo; a politica para reajuste posterior esta `PENDENTE`.
- Mais de um pedido aberto, pedido recente e janela temporal de suspeita continuam `PENDENTE` de politica comercial. As constraints de idempotencia ja bloqueiam repeticoes exatas.
- Consumo e estoque rejeitam valores negativos ou invalidos. Sem consumo maximo, nao se inventa teto. Quantidade solicitada acima do maximo deve ser sinalizada para revisao, nunca aprovada automaticamente.

O backup incremental deste ciclo fica em `backups/client_whatsapp_orders_cycle2_20260914_220931/`. O manifesto inclui hashes e restauracao seletiva sem invalidar o backup anterior.

### Canal interno de recebimento

O adaptador `baileys-api/inbound.js` recebe `messages.upsert` do socket existente e encaminha somente um contrato minimo para `POST /internal/whatsapp/events`. O endereco padrao usa HTTP em loopback; URLs externas ou rotas diferentes sao recusadas pelo adaptador. O backend tambem exige origem local direta, rejeita cabecalhos de proxy e autentica o header `x-whatsapp-inbound-token` com comparacao constante.

O segredo existe apenas no ambiente dos dois processos. Nunca deve ser colocado no repositorio, frontend ou log. Configuracao local:

```ini
WHATSAPP_INBOUND_ENABLED=false
WHATSAPP_INBOUND_TOKEN=
WHATSAPP_INBOUND_INSTANCE=
WHATSAPP_INBOUND_COMPANY=
WHATSAPP_INBOUND_URL=http://127.0.0.1:8765/internal/whatsapp/events
WHATSAPP_INBOUND_TIMEOUT_MS=5000
WHATSAPP_INBOUND_MAX_ATTEMPTS=3
WHATSAPP_INBOUND_MAX_QUEUE=100
WHATSAPP_INBOUND_MAX_BODY_BYTES=32768
```

O padrao e desligado. Quando habilitado, a instancia e associada no backend a uma empresa configurada; o Node nao escolhe empresa nem cliente. O corpo JSON aceito contem `provider`, `instance`, `event_id`, `message_id`, `remote_jid`, `from_me`, `message_type`, `text`, `timestamp` e `raw_type` opcional. Payload bruto nao e persistido.

O diretorio de autenticacao do Baileys e definido somente pelo ambiente e permanece ignorado pelo Git, assim como artefatos locais de QR Code. O valor real e as credenciais da sessao nao devem ser documentados, copiados para backups de codigo ou exibidos em logs.

Grupos, mensagens proprias, mensagens de sistema, JID invalido e telefone invalido ficam bloqueados e auditados. Numeros sem um unico cliente ativo ficam `nao_identificado`. Eventos repetidos incrementam `duplicate_count` no registro existente e nao criam nova mensagem ou conversa. Mensagens diretas validas sao registradas transacionalmente; opt-out atualiza conversa e consentimento sem resposta automatica.

Se o FastAPI estiver indisponivel, o adaptador usa fila em memoria limitada, timeout e no maximo tres tentativas com backoff. Nao ha retry infinito e a conexao Baileys nao e encerrada. A fila nao e duravel: reiniciar o processo pode perder eventos ainda nao entregues, risco que exige decisao antes de uma futura fila persistente.

### Sugestoes e envio exclusivamente manual

`GET /api/whatsapp/suggestions` calcula clientes sem compra ha mais de sete dias e informa telefone, consentimento, ultima compra, dias sem compra, ultima mensagem, ultimo envio, conversa aberta, pedido pendente e bloqueios. A lista e apenas sugestao. Filtros ou recarregamento invalidam a selecao no navegador.

O fluxo manual usa:

```text
GET  /api/whatsapp/suggestions
GET  /api/whatsapp/manual-batches
POST /api/whatsapp/manual-batches
GET  /api/whatsapp/manual-batches/{id}
POST /api/whatsapp/manual-batches/{id}/confirm
POST /api/whatsapp/manual-batches/{id}/cancel
POST /api/whatsapp/manual-batches/{id}/send
GET  /api/whatsapp/inbound-events
```

O usuario seleciona clientes, prepara um lote, revisa a mensagem personalizada e confirma explicitamente. A selecao expira em 15 minutos. Antes de cada tentativa, o backend revalida empresa, cliente ativo, telefone, consentimento, opt-out, compra recente, conversa, pedido, sandbox e mensagem igual enviada recentemente. Cada item possui chave idempotente e resultado proprio; falhas nunca sao reenviadas automaticamente.

A criacao do lote aceita uma `request_id` local gerada pela interface. Repetir a mesma requisicao retorna o mesmo lote; reutilizar a chave com clientes, filtros ou mensagem diferentes e recusado. Isso protege repeticoes de clique ou de rede sem impedir que o usuario inicie conscientemente um novo lote com uma nova chave.

O agendador legado de mensagens motivacionais nao e iniciado pelo backend. O comando manual existente foi preservado, mas nenhuma rotina periodica envia mensagens sem acao humana.

O envio permanece protegido por duas travas independentes:

```ini
WHATSAPP_OUTBOUND_ENABLED=false
WHATSAPP_OUTBOUND_MODE=disabled
WHATSAPP_OUTBOUND_SANDBOX_NUMBERS=
WHATSAPP_OUTBOUND_PRODUCTION_APPROVED=false
WHATSAPP_OUTBOUND_DEDUPE_DAYS=7
```

Os modos aceitos sao `disabled`, `sandbox` e `production`. `sandbox` aceita somente numeros explicitamente permitidos. `production` ainda exige `WHATSAPP_OUTBOUND_PRODUCTION_APPROVED=true`, permissao RBAC e provedor Baileys configurado. Nenhuma dessas variaveis e ativada pelos testes.

O endpoint legado local `/send` permanece por compatibilidade, mas opera com falha fechada: `API_KEY` e obrigatoria, a comparacao e constante e chave ausente ou incorreta recusa a requisicao. Mesmo com chave correta, o endpoint continua bloqueado enquanto `WHATSAPP_OUTBOUND_ENABLED=false`. A chave nunca e registrada em log ou resposta.

### Migracao, teste e desligamento

`backend/migrations/20260914_whatsapp_inbound_up.sql` adiciona auditoria inbound, lotes e itens manuais. O rollback `20260914_whatsapp_inbound_down.sql` remove somente essas tres tabelas e preserva a migracao de pedidos, clientes, mensagens, vendas e estoque.

O `.gitignore` continua protegendo dumps SQL em geral, mas possui excecoes explicitas somente para as migracoes versionaveis de RBAC e WhatsApp. As migracoes `up` e `down` deste ciclo permanecem integras e nao foram aplicadas em banco remoto.

Para desligar imediatamente, configure `WHATSAPP_INBOUND_ENABLED=false`, `WHATSAPP_OUTBOUND_ENABLED=false` e `WHATSAPP_OUTBOUND_MODE=disabled`, depois use apenas o procedimento operacional autorizado para recarregar os processos. Nao apague sessao, QR Code ou dados.

Validacao local:

```bat
python -m py_compile backend\app.py backend\routers\whatsapp_inbound.py backend\routers\whatsapp_campaigns.py backend\services\whatsapp_inbound_service.py backend\services\whatsapp_campaign_service.py
node --check baileys-api\server.js
node --check baileys-api\inbound.js
node --check baileys-api\security.js
node tests\js\test_baileys_inbound.js
node tests\js\test_baileys_security.js
node tests\js\test_client_whatsapp_foundation.js
python -X faulthandler -m pytest -q tests\test_whatsapp_inbound_campaigns.py
python -X faulthandler -m pytest -q tests\test_cycle5_blockers.py
```

Os backups incrementais locais preservam arquivos anteriores e incluem manifesto, hashes e restauracao seletiva. Eles nao sao pacotes de deploy e nao devem conter `.env`, sessao Baileys, tokens, bancos ou mensagens reais.

Limitacoes conhecidas antes de qualquer futura ativacao: a fila inbound nao e persistente e nao possui dead-letter; nao ha politica automatica de retencao de mensagens; consentimento e retomada apos opt-out exigem governanca operacional; a politica de multiplos pedidos abertos permanece pendente; lotes interrompidos em `processando` nao possuem recuperacao automatica; vendas ainda sao relacionadas ao cliente por nome em parte da elegibilidade; e os avisos de depreciacao do ecossistema Python devem ser acompanhados separadamente de falhas reais.

## Seguranca e Privacidade

Este README publico evita expor detalhes de infraestrutura. Nao devem ser publicados:

- enderecos, dominios, hostnames ou portas de servidor;
- usuarios, senhas, tokens, chaves ou certificados;
- nomes de servicos de producao;
- caminhos locais ou remotos de ambientes privados;
- nomes de bancos, tenants, clientes reais ou dados persistentes;
- conteudo de arquivos de configuracao sensivel.

## Dados Persistentes

Arquivos de banco, uploads, logs e backups sao dados sensiveis e devem permanecer fora do pacote publico. A atualizacao da aplicacao deve preservar esses dados no ambiente de destino.

## Git

Antes de publicar alteracoes:

```bat
git status --short
git diff --stat
git diff --check
```

Nao use force push para publicar esta versao estavel.
