# Menina dos Raios ERP

Sistema de gestao operacional com ERP web e aplicativo Android para vendas, entregas, estoque, boletos, calendario, analises e comunicacao.

## Estado do projeto

O branch `main` contem o codigo-fonte mais recente do ERP e do Android. A versao de servidor exibida pelo ERP permanece `2.1.0`; esse identificador, sozinho, nao informa qual commit esta ativo em producao. Para confirmar uma publicacao do backend, confira o commit retornado pelo health check e o log de deploy.

APK oficial publicado em 29/10/2026:

| Campo | Valor |
| --- | --- |
| Versao | `2.0.45` (`versionCode` `73`) |
| Pacote | `br.com.meninadosraios.vendas` |
| Tamanho | `2.759.094` bytes |
| SHA-256 | `808b5a6c26fe6095e013616ec08d8cf5aa0590486922e1994e6310541fe77504` |

Esse registro descreve o APK; a publicacao do APK e a implantacao do backend sao processos separados.

## Modulos do ERP

- **Hoje e Consolidado:** indicadores de faturamento, notas, produtor rural, avulsos, ticket medio e avarias, com filtros por periodo.
- **Vendas e notas:** lancamento e edicao de vendas/NF, consulta de itens e historico, clientes, vendedores e entregadores.
- **Entregas por voz:** interpreta produto e quantidade em qualquer ordem, incluindo pesos decimais com virgula; itens e valores sao apresentados no resumo da entrega.
- **Estoque:** abas de resumo e produtos, saldos e movimentacoes rastreados por venda/NF. Os cartoes de produtos abrem o historico de vendas por NF; o modal central permite consultar e abrir a venda correspondente.
- **Analises:** Projecao, Avarias e Produtividade.
- **Boletos:** filtros por vencimento e status, edicao de vencimento, baixa/reabertura como pago ou pendente, selecao de clientes acompanhados e paginacao.
- **Clientes e pedidos:** atendimento integrado ao Evolution GO, com fila de pedidos pendentes, aprovados e recusados e acoes humanas de aprovacao.
- **Orcamentos e configuracoes:** catalogos, precos e regras de acesso por perfil.

O Evolution GO e o transporte WhatsApp ativo. O runtime do ERP nao usa Baileys.

## Modulos do APK

O aplicativo Android compartilha o login do ERP e oferece fluxos moveis de entregas/notas, analises e acesso aos modulos conforme o perfil. As contas admin podem consultar boletos e configurar empresas acompanhadas. Notificacoes de cobranca e calendario ficam restritas a admins.

- **Cobrancas Novo Tempo:** considera somente vendas marcadas como entregues; o primeiro aviso ocorre 24 horas depois da entrega e os lembretes repetem as 08h, 12h, 16h e 20h ate a baixa.
- **Calendario:** verificacoes as 09h, 13h, 17h e 21h, respeitando o limite diario de avisos configurado em cada evento; as notificacoes abrem o calendario correspondente.
- **Boletos:** carteira com busca, filtros, selecao de clientes acompanhados, vencimento, status e paginacao de 20 itens.
- **Produtos e analises:** consulta de produtos e valores, alem dos paineis moveis disponiveis no app.

Consulte [android/README.md](android/README.md) para compilacao e publicacao, e [CHANGELOG-APP.md](CHANGELOG-APP.md) para o historico de versoes Android.

## Validacao

O repositorio possui testes automatizados para backend e componentes de interface. Execute os testes definidos para o modulo alterado antes de publicar; nao use resultados historicos de outra revisao como evidencia da revisao atual. O fluxo de deploy do servidor inclui preflight, backup, checksum, promocao e health check.

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
- desbloquear o app com biometria apos o login inicial, quando ativada no aparelho.

### Estrutura do app

O codigo-fonte Android fica em `android/`, neste mesmo repositorio e branch `main` do ERP.

O APK oficial compilado usa o nome padrao:

```text
Menina-dos-Raios-Vendas-OFICIAL.apk
```

O arquivo APK pode ou nao estar versionado no Git, conforme a politica operacional do ambiente. O item mais importante para manutencao e auditoria e o projeto Android fonte, pois o APK deve ser gerado a partir dele.

### Build e publicacao do APK

O APK deve ser compilado localmente com Android Studio ou Gradle, em uma maquina autorizada. A assinatura do aplicativo usa uma chave privada mantida apenas nas maquinas dos desenvolvedores autorizados.

Depois da compilacao e assinatura, publique o APK oficial pelo `atualizar_apk.bat`. O fluxo pre-valida pacote, versao, certificado, catalogos, tamanho e SHA-256; cria backup remoto; envia APK e metadados a um staging; valida o checksum remoto; promove os arquivos; e confirma os metadados e o APK baixado publicamente. A verificacao final repete o GET com cache-busting quando a resposta vier incompleta e so aprova tamanho e SHA-256 correspondentes.

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
5. ativar a biometria, se desejado e disponivel no aparelho;
6. usar as funcionalidades disponiveis, como pedidos e entregas.

### Sessao e sincronizacao movel

O login Android identifica a sessao por `x-client-type: android`. Essas sessoes tem validade e inatividade de ate 30 dias; a regra web permanece em 10 horas de validade e 20 minutos sem atividade. O backend adiciona automaticamente o tipo de cliente em bancos existentes.

Falhas temporarias de rede durante a validacao nao apagam o token nem a preferencia de biometria. Uma resposta HTTP 401/403 remove apenas as credenciais expiradas, preservando a biometria para o proximo login. A opcao **Sair da conta** continua removendo a sessao e a biometria local.

Vales com assinatura sao gravados no armazenamento local antes do envio. Se o servidor estiver indisponivel, o vale permanece pendente; a tela apresenta o detalhe do erro e o app tenta sincronizar os pendentes ao entrar novamente. Notas de produtos tambem possuem fila local e reenvio manual pela tela de pendencias.

## Publicacao e atualizacao

Use `atualizar_apk.bat` para publicar o APK oficial. Use `ATUALIZAR.bat` para abrir o menu operacional do ERP; a implantacao do backend e independente da publicacao Android. O processo do servidor exige o commit aprovado no `main`, preflight, backup, checksum e health check. Consulte [AGENTS.md](AGENTS.md) para os procedimentos locais vigentes.

O pacote publicado nao deve conter:

- credenciais, tokens, chaves privadas ou arquivos `.env`;
- bancos de dados locais ou dados persistentes;
- uploads, logs, caches, backups ou artefatos temporarios;
- ambientes virtuais ou `node_modules`;
- metadados Git.

O checksum SHA-256 deve ser publicado junto ao pacote quando o arquivo for disponibilizado.

Os launchers nao armazenam senhas nem chaves privadas. A autenticacao SSH ocorre interativamente na janela externa do PowerShell; nao publique configuracoes locais ou segredos.

## Integracao WhatsApp

O Evolution GO e o transporte WhatsApp ativo. O ERP recebe eventos pelo webhook, aplica controles de empresa, permissao, sandbox, consentimento e idempotencia, e apresenta pedidos para decisao humana. A aprovacao ou recusa e feita no painel; o pedido recebido nao se transforma automaticamente em venda nem altera o estoque. O runtime e o painel nao usam Baileys.

## Tokens Dos Apps Moveis

As rotas moveis de Notas APP e Calendario APP usam tokens externos de ambiente:

```ini
APP_NOTES_TOKEN=
APP_CALENDAR_TOKEN=
```

Esses valores devem ser configurados fora do Git e fora do pacote publico. O
codigo nao deve possuir fallback funcional hardcoded, e o README nao deve
documentar valores reais. Quando o token correspondente estiver ausente ou
vazio, somente a rota movel dependente fica bloqueada com falha fechada; a
aplicacao principal continua inicializando para permitir operacao e correcao de
configuracao.

Se houver evidencia de que um valor real ja foi versionado, trate-o como
exposto: planeje a rotacao em ciclo operacional separado, com backup e janela
aprovada. Nao rotacione credenciais durante revisoes locais ou geracao de
pacote.

## Instalacao e Atualizacao

O fluxo operacional com identificacao de release, validacao remota, health check
e diagnosticos por execucao esta em [GUIA_ATUALIZACOES.md](GUIA_ATUALIZACOES.md).

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

A area **Clientes** possui as sub-abas **WhatsApp** e **Pedidos**. O recebimento pelo Evolution GO, o bot de pedidos e o envio de respostas ao cliente sao controlados por variaveis de ambiente, permissoes RBAC e configuracoes de sandbox. A confirmacao do cliente cria pedido em `aguardando_aprovacao`; aprovacao, recusa e remocao sao acoes humanas feitas no painel. Nao existe conversao automatica em venda nem alteracao automatica de estoque.

O ambiente operacional atual usa pacotes controlados e backups incrementais para publicar mudancas. Deploys de codigo nao enviam mensagem WhatsApp. Mensagens reais sao disparadas apenas por fluxos explicitamente acionados depois do deploy, como o bot respondendo a uma mensagem recebida ou a notificacao de aprovacao/recusa pelo operador.

### Arquitetura inicial

- `backend/domains/whatsapp_states.py`: contratos e estados previstos para mensagens, conversas, consentimento e pedidos;
- `backend/domains/whatsapp_policies.py`: normalizacao de telefone, comandos de controle, idempotencia, elegibilidade de campanha e bloqueios de duplicidade;
- `backend/services/whatsapp_calculation_service.py`: simulacao pura de consumo, avaria, estoque, limite e quantidade sugerida;
- `backend/static/js/client_whatsapp.js`: apresentacao local de clientes e telefones na sub-aba WhatsApp;
- `backend/static/js/client_orders.js`: estados, filtros e estado vazio da sub-aba Pedidos;
- `backend/static/css/client_whatsapp.css` e `backend/static/css/client_orders.css`: layout responsivo das novas sub-abas.

O ERP usa Evolution GO para conexao, envio e recebimento WhatsApp. O webhook validado encaminha os eventos ao bot existente; nao ha servico Baileys no runtime do ERP.

### Bot de pedidos

As mensagens do fluxo ficam em **Configuracoes > WhatsApp > Bot**. O administrador pode editar o aviso de atendimento automatizado e registro, a saudacao/lista de produtos, a pergunta de quantidade, a pergunta de avaria, a confirmacao e a mensagem final. O marcador `{cliente}` usa o nome do cliente cadastrado.

O fluxo automatico atual e:

```text
qualquer mensagem inicial -> cadastro inicial se cliente novo -> escolha do produto
-> quantidade em KG/UN -> avaria em KG/UN -> confirmacao SIM/NAO/ADICIONAR
-> pedido aguardando aprovacao humana
```

Os produtos aceitos sao Macaxeira com casca, Macaxeira a vacuo, Alho descascado 250g, Alho descascado 1kg, Macaxeira chips e Macaxeira pre-cozida. O cliente pode responder pelo numero de 1 a 6 ou pelo nome. A unidade e validada conforme o produto e a avaria nao pode superar a quantidade solicitada. A resposta `ADICIONAR` permite incluir outro item no mesmo atendimento antes da confirmacao final.

Quando o telefone/JID recebido ainda nao possui cliente cadastrado, o bot coleta como o cliente gostaria de ser chamado e o endereco antes de iniciar o pedido. Quando o evento vier por LID, o sistema tenta associar e gravar o telefone usando o JID numerico alternativo fornecido pelo Evolution GO; se esse dado nao existir no evento, o telefone real nao e inferido por heuristica.

O bot somente responde quando todas as travas estiverem liberadas: canal inbound configurado, `bot_active=1`, `auto_reply_enabled=1`, horario permitido, provedor Evolution GO, outbound habilitado e modo inbound coerente. Em modo `sandbox`, apenas numeros permitidos respondem. Em `production`, o inbound aceita clientes individuais validos, mas o envio continua dependente das travas de outbound. Falha de envio fica registrada e nao cria venda nem movimenta estoque.

O atendimento iniciado pelo cliente usa a origem `cliente_iniciou_contato` e nao depende de consentimento de marketing. `SAIR`, `STOP`, `PARAR` ou `CANCELAR` registram opt-out e bloqueiam novas respostas automaticas. Pedidos de atendente mudam a conversa para `atendimento_humano`. A pontuacao de completude e sua composicao ficam registradas na memoria de calculo do pedido; um pedido confirmado com todos os dados recebe 100 pontos.

### Aprovacao, recusa, remocao e notificacao

A sub-aba **Pedidos** possui visoes para **Pendentes**, **Aprovados** e **Recusados**. A lista principal deve mostrar somente a fila pendente; pedidos aprovados e recusados ficam nas respectivas abas para consulta.

O operador pode:

- aprovar um pedido pendente;
- recusar um pedido pendente informando motivo;
- remover pedido pendente, aprovado ou recusado;
- criar um rascunho manual para o cliente a partir do painel lateral.

A aprovacao ou recusa nao cria venda, nao baixa estoque e nao envia mensagem durante deploy. Quando a acao e executada na UI e a transicao realmente muda o status (`changed=true`), o backend tenta enviar uma notificacao formal ao cliente:

- aprovacao: informa que o pedido foi aprovado e que a equipe dara continuidade ao atendimento;
- recusa: informa que o pedido nao podera ser atendido naquele momento e inclui o motivo informado pelo operador.

Cliques repetidos nao reenviam a notificacao porque a acao idempotente retorna `changed=false`. A notificacao respeita `WHATSAPP_OUTBOUND_ENABLED`, `WHATSAPP_OUTBOUND_MODE`, allowlist de sandbox e `WHATSAPP_OUTBOUND_PRODUCTION_APPROVED`. Se o envio for bloqueado por configuracao, a mudanca de status permanece valida e a resposta da API indica o motivo em `notification.reason`.

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

Uma mensagem recebida devera ser identificada por empresa, ID externo, JID, horario e hash do evento. A chave de idempotencia e deterministica e inclui a empresa, impedindo que o mesmo evento seja tratado como novo em repeticoes do Evolution GO. Antes de criar um pedido, o servico futuro devera verificar mensagem processada, pedido aberto na conversa, chave repetida, confirmacao anterior e pedido recente do cliente. Uma ocorrencia suspeita deve ficar em `duplicado_suspeito` para revisao humana.

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
POST /api/whatsapp/orders/{order_id}/confirm
POST /api/whatsapp/orders/{order_id}/reject
DELETE /api/whatsapp/orders/{order_id}
POST /api/whatsapp/orders/new-for-client
```

Todos exigem a sessao existente, usam a empresa corrente e fecham a conexao em `finally`. O webhook publico continua reservado a simulacoes autenticadas. A recepcao real usa o canal interno descrito abaixo. O bot pode responder quando configurado; nenhuma resposta cria venda, altera estoque ou aprova pedido sem acao humana.

No RBAC atual, as capacidades sao representadas pelos modulos `clientes_whatsapp` e `clientes_pedidos`, combinados com as acoes existentes (`view`, `create`, `edit`, `approve` e outras). Isso implementa negacao padrao para cargos gerenciados. A lista detalhada `whatsapp.*` permanece como vocabulario de dominio para uma futura evolucao do RBAC. Administrador continua protegido; nenhum cargo novo recebe acesso amplo automaticamente. Aprovacao, recusa, remocao e criacao de rascunho possuem endpoints protegidos; conversao automatica em venda permanece fora desta linha.

#### Decisoes de dados

- Telefone armazenado para integracao: E.164 com `+55`; JID separado no formato usado pelo Evolution GO. Prefixos `00` sao removidos e numeros nacionais de 10 ou 11 digitos recebem `55`.
- Nono digito: nenhum digito e criado ou removido por heuristica. Casos antigos/ambiguos ficam `PENDENTE` de regra e revisao manual.
- Telefone invalido: evento rejeitado antes da escrita. Dois clientes ativos com o mesmo telefone normalizado tambem impedem associacao automatica.
- Unicidade de mensagem: `(company_key, instance_key, external_message_id)` e `(company_key, idempotency_key)` sao unicos. Repeticao retorna o registro existente sem nova conversa, evento ou pedido.
- Consentimento ausente nao equivale a opt-in. Uma conversa iniciada pelo cliente pode ser registrada, mas nao autoriza campanha. `SAIR`, `PARAR`, `STOP` e `CANCELAR` registram opt-out.
- Retomada apos opt-out: `PENDENTE`. Nao existe reativacao automatica; exigira origem e trilha de auditoria definidas.
- Avaria nasce como `informada`. Os estados futuros sao `aprovada`, `reposta` e `rejeitada`; este ciclo nao oferece transicao nem reposicao real.
- Percentual de reposicao fica entre 0 e 100 e o responsavel e registrado. Aprovacao e responsavel final pela reposicao continuam `PENDENTE`.
- Pedido permanece persistente e revisavel. Confirmacao do cliente gera `aguardando_aprovacao`; aprovacao, cancelamento/recusa e remocao sao comandos humanos protegidos. Conversao em venda continua fora desta linha. O preco unitario e gravado no item como fotografia do calculo; a politica para reajuste posterior esta `PENDENTE`.
- O bot permite varios itens no mesmo atendimento por `ADICIONAR`. Politicas comerciais de janela temporal e suspeita continuam conservadoras; as constraints de idempotencia bloqueiam repeticoes exatas.
- Consumo e estoque rejeitam valores negativos ou invalidos. Sem consumo maximo, nao se inventa teto. Quantidade solicitada acima do maximo deve ser sinalizada para revisao, nunca aprovada automaticamente.

O backup incremental deste ciclo fica em `backups/client_whatsapp_orders_cycle2_20260914_220931/`. O manifesto inclui hashes e restauracao seletiva sem invalidar o backup anterior.

### Recebimento por webhook Evolution GO

O ERP recebe mensagens pelo webhook do Evolution GO, valida o segredo associado à empresa e confere a instância antes de normalizar e processar cada evento. Eventos repetidos são identificados para impedir mensagens e conversas duplicadas. O bot conserva as regras de sandbox, consentimento, horário, limites e bloqueio de grupos.

O webhook não persiste o payload bruto. Falhas de validação ficam auditadas sem criar pedido, venda ou movimento de estoque. O recebimento depende da instância e do webhook configurados no painel Evolution GO.

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

O agendador diario de mensagens motivacionais e iniciado junto com o backend. Ele usa `motivation_enabled` e `motivation_time` do banco (padrao 07:00, fuso `America/Manaus`), tenta durante uma janela de duas horas e registra o resultado por contato em `whatsapp_log`. A tentativa diaria e protegida por transacao SQLite para evitar duplicidade quando houver mais de um worker. A tela de WhatsApp mostra se o agendador esta ativo, se o provedor tem configuracao e a data da ultima tentativa/sucesso. O envio continua sujeito a `WHATSAPP_OUTBOUND_ENABLED` e aos controles de sandbox/producao do ERP.

O envio permanece protegido por duas travas independentes:

```ini
WHATSAPP_OUTBOUND_ENABLED=false
WHATSAPP_OUTBOUND_MODE=disabled
WHATSAPP_OUTBOUND_SANDBOX_NUMBERS=
WHATSAPP_OUTBOUND_PRODUCTION_APPROVED=false
WHATSAPP_OUTBOUND_DEDUPE_DAYS=7
```

Os modos aceitos sao `disabled`, `sandbox` e `production`. `sandbox` aceita somente numeros explicitamente permitidos. `production` ainda exige `WHATSAPP_OUTBOUND_PRODUCTION_APPROVED=true`, permissao RBAC e provedor Evolution GO configurado. Nenhuma dessas variaveis e ativada pelos testes.

O endpoint legado local `/send` permanece por compatibilidade, mas opera com falha fechada: `API_KEY` e obrigatoria, a comparacao e constante e chave ausente ou incorreta recusa a requisicao. Mesmo com chave correta, o endpoint continua bloqueado enquanto `WHATSAPP_OUTBOUND_ENABLED=false`. A chave nunca e registrada em log ou resposta.

### Recebimento WhatsApp via Evolution GO

O Evolution GO encaminha mensagens pelo webhook integrado. O ERP valida segredo, empresa e instancia antes de processar o evento; o bot mantem seus bloqueios de sandbox, consentimento, horario e idempotencia. O serviço e os controles de Baileys foram removidos do runtime e do painel. Os caminhos de credenciais antigas permanecem excluidos dos pacotes de deploy durante a retirada segura.

### Migracao, teste e desligamento

`backend/migrations/20260914_whatsapp_inbound_up.sql` adiciona auditoria inbound, lotes e itens manuais. O rollback `20260914_whatsapp_inbound_down.sql` remove somente essas tres tabelas e preserva a migracao de pedidos, clientes, mensagens, vendas e estoque.

O `.gitignore` continua protegendo dumps SQL em geral, mas possui excecoes explicitas somente para as migracoes versionaveis de RBAC e WhatsApp. As migracoes `up` e `down` deste ciclo permanecem integras e nao foram aplicadas em banco remoto.

Para desligar imediatamente o envio automatico, configure `WHATSAPP_OUTBOUND_ENABLED=false` e `WHATSAPP_OUTBOUND_MODE=disabled`, depois use apenas o procedimento operacional autorizado para recarregar os processos. Para limitar a entrada sem desligar o listener, coloque o inbound em `sandbox` pela UI e mantenha a allowlist controlada. Nao apague sessao, QR Code ou dados.

Validacao local:

```bat
python -m py_compile backend\app.py backend\routers\whatsapp_inbound.py backend\routers\whatsapp_campaigns.py backend\services\whatsapp_inbound_service.py backend\services\whatsapp_campaign_service.py
node tests\js\test_client_whatsapp_foundation.js
python -X faulthandler -m pytest -q tests\test_whatsapp_inbound_campaigns.py
python -X faulthandler -m pytest -q tests\test_cycle5_blockers.py
```

Os backups incrementais locais preservam arquivos anteriores e incluem manifesto, hashes e restauracao seletiva. Eles nao sao pacotes de deploy e nao devem conter `.env`, credenciais legadas de integracao, tokens, bancos ou mensagens reais.

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
