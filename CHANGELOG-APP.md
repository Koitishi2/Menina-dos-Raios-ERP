# Changelog - Menina dos Raios Vendas

Este arquivo registra as alteracoes funcionais do aplicativo Android e da integracao com o sistema.

## Politica de versoes

- Revisoes: `1.0.1`, `1.0.2` ate `1.0.999`.
- Apos `1.0.999`, a proxima versao sera `1.1.0`.
- O `versionCode` interno do Android sempre aumenta a cada APK publicado.
- Uma versao publicada nunca deve ser reutilizada para outro APK.

## [2.0.10] - 12/08/2026

### Padronizacao de botoes, cards e filtros

- Home reorganizada com oito cards iguais em grade: Entregas, Projecao, Avarias, Produtividade, Clientes, Consolidado, Notificacoes e Atualizacoes.
- Notificacoes e Verificar atualizacoes deixaram de usar botoes menores e agora seguem o mesmo estilo dos demais cards.
- Cards da Home receberam altura, espacamento, alinhamento central, borda e sombra padronizados.
- Filtros de periodo em Projecao, Produtividade, Avarias e Consolidado passaram a usar o mesmo padrao visual, com altura uniforme, borda arredondada e espacamento entre botoes.
- Todos os botoes/cards principais mantem animacao leve ao toque, com escala e opacidade.
- Login, PIN, Entregas, modulos, atualizacao automatica e acentuacao foram preservados.

## [2.0.9] - 12/08/2026

### Refinamento visual, tema escuro e acentuacao

- Home e modulos principais receberam tema escuro em preto/grafite, com cards mais limpos e melhor contraste.
- Cards e botoes agora tem feedback visual ao tocar, com animacao leve de escala e opacidade.
- Projecao ganhou grafico de realizado x meta, KPIs e barras horizontais para ranking de produtos.
- Produtividade ganhou resumo visual, grafico de comparacao com media esperada e barras por periodo/dia.
- Avarias ganhou resumo visual e cards mais legiveis em tema escuro.
- Consolidado ganhou comparativo visual de receita/objetivo e barra de impacto das avarias.
- Adicionada normalizacao de textos quebrados vindos do app/backend, corrigindo casos como `Macaxeira a Vacuo`, `Pre-Cozida`, `â€` e `â†` antes de exibir.
- Login, PIN, Entregas, navegacao, assinatura, atualizacao automatica e PUBLICAR_APK.bat foram preservados.

## [2.0.8] - 12/08/2026

### Home com Projecao e modulo mobile

- Removido o modulo Notas / Pedido da Home.
- Adicionado o modulo Projecao no lugar, mantendo Entregas como area operacional para lancar pedido/entrega.
- A Home principal agora fica com seis modulos: Entregas, Projecao, Avarias, Produtividade, Clientes e Consolidado.
- Notificacoes e Verificar atualizacoes permanecem como botoes utilitarios abaixo da grade.
- Criada tela Projecao com filtros de periodo, produto, fonte e visualizacao.
- Projecao consome `/api/projecao/producao` com o token x-token e exibe KPIs, ranking, tendencia diaria e risco de ruptura em cards mobile.
- Login, PIN, Entregas e atualizacao automatica foram preservados.
## [2.0.7] - 12/08/2026

### Base dos modulos de leitura

- Produtividade passou a abrir uma tela funcional com filtros Hoje, Semana, Mes atual e Mes anterior.
- Avarias passou a listar ocorrencias em cards, usando dados de leitura do sistema.
- Clientes passou a ter busca, lista em cards e tela de detalhe com historico resumido.
- Consolidado passou a exibir KPIs simples por periodo e lista resumida por dia.
- As telas usam o token x-token do login compartilhado e mantem navegacao de volta para Home.
- Login, PIN, Entregas, Notas/Pedido e atualizacao automatica foram preservados.
## [2.0.6] - 12/08/2026

### Correcao de acentuacao e UTF-8

- Corrigidos textos corrompidos por encoding no APK, incluindo Home, Entregas, notificacoes, mensagens e alertas.
- O arquivo MainActivity.java foi normalizado em UTF-8 sem BOM.
- A compilacao Java passou a declarar encoding UTF-8 no Gradle.
- A logica de login, PIN, navegacao, atualizacao automatica, endpoints e PUBLICAR_APK.bat foi preservada.
## [2.0.5] - 12/08/2026

### Home em grade e atualizacao centralizada

- A Home de modulos foi reorganizada em grade de duas colunas.
- O botao de verificar atualizacoes do APK foi movido para a Home.
- A tela de pedido/Entregas deixou de exibir o botao de atualizacao do APK.
- O botao Atualizar entregas foi mantido na lista de Entregas, pois serve apenas para recarregar as entregas.
- Login, PIN, navegacao, PUBLICAR_APK.bat e leitura do catalogo de atualizacao foram preservados.
## [2.0.4] - 12/08/2026

### Cabecalho da tela Entregas

- Adicionado cabecalho na lista de Entregas com botao "Home".
- O novo botao retorna diretamente para a Home de modulos.
- O comportamento atual do botao voltar do Android foi mantido.
- O botao inferior "Voltar para Entregas" continua retornando para o menu do modulo Entregas.
## [2.0.3] - 12/08/2026

### PIN com janela de confianca

- O app deixa de pedir PIN em toda troca rapida entre aplicativos.
- Depois de desbloquear, o PIN fica liberado por 15 minutos neste aparelho.
- Se o app ficar parado por mais tempo, for fechado ou a sessao expirar, o PIN volta a ser solicitado.
- Login compartilhado, validacao de sessao e seguranca local do PIN foram preservados.
## [2.0.2] - 12/08/2026

### Home de modulos no app

- Apos login e PIN, o app passa a abrir uma Home de modulos em vez de cair direto na tela de pedido.
- Adicionados botoes grandes para Entregas, Notas / Pedido, Avarias, Produtividade, Clientes e Consolidado.
- O modulo Entregas ganhou uma tela intermediaria com as opcoes "Lancar entrega / pedido" e "Pendentes / Concluidas".
- O atalho Notas / Pedido continua abrindo diretamente a tela atual de montagem de pedido.
- Avarias, Produtividade, Clientes e Consolidado foram adicionados como telas base "Em breve".
- O botao Voltar do Android retorna para a Home quando o usuario esta dentro de um modulo.
- Login compartilhado, PIN, atualizacao automatica, colagem do WhatsApp, notas pendentes, recibos, calendario e Entregas 2.0.1 foram preservados.

## [2.0.1] - 12/08/2026

### MÃƒÂ³dulo Entregas no app

- Adicionado botÃƒÂ£o "Entregas" na tela principal do aplicativo.
- Criada tela prÃƒÂ³pria para listar entregas pendentes e concluÃƒÂ­das.
- O app busca as notas fiscais do sistema via `/api/sales` usando o token do login compartilhado.
- As entregas sÃƒÂ£o agrupadas por data, cliente, NF e entregador para evitar poluiÃƒÂ§ÃƒÂ£o visual quando uma nota tem vÃƒÂ¡rios produtos.
- Cada entrega mostra cliente, data, NF, quantidade de produtos, total, entregador, placa e resumo dos itens.
- Adicionada aÃƒÂ§ÃƒÂ£o "Concluir" para marcar a entrega como realizada pelo celular.
- A conclusÃƒÂ£o usa o endpoint existente `/api/sales/bulk-delivered`, preservando o fluxo do site.

## [2.0.0] - 12/08/2026

### Login compartilhado + PIN local

- O app passou a exigir login com o mesmo usuÃƒÂ¡rio e senha do sistema web.
- A autenticaÃƒÂ§ÃƒÂ£o usa o backend oficial em `/api/auth/login` e guarda o token `x-token` no aparelho.
- Ao abrir novamente, o app pede PIN local de 4 dÃƒÂ­gitos antes de liberar a tela principal.
- O PIN fica somente no celular, com hash local, e nÃƒÂ£o ÃƒÂ© enviado ao backend.
- Depois do PIN, o app valida a sessÃƒÂ£o no servidor por `/api/auth/me`.
- Adicionado botÃƒÂ£o "Sair da conta" para remover login e PIN do aparelho.
- As funÃƒÂ§ÃƒÂµes atuais de pedido, colagem do WhatsApp, notas pendentes, recibos, calendÃƒÂ¡rio e atualizaÃƒÂ§ÃƒÂ£o automÃƒÂ¡tica foram preservadas.

## [1.0.27] - 25/07/2026

### ImportaÃƒÂ§ÃƒÂ£o de pedidos do WhatsApp no app

- Adicionado botÃƒÂ£o "Colar pedido do WhatsApp" no app Android.
- Ao abrir o app, se existir um pedido copiado no celular, o app pergunta se deseja colar e interpretar.
- O app passa a ler pedidos copiados do WhatsApp e identificar automaticamente produto, medida e unidade.
- CompatÃƒÂ­vel com formatos como `produto = 18kg`, `02 caixas de cenoura`, `10 kg de melÃƒÂ£o` e `Abacaxi 2 und`.
- IncluÃƒÂ­das interpretaÃƒÂ§ÃƒÂµes para variaÃƒÂ§ÃƒÂµes com maiÃƒÂºsculas, minÃƒÂºsculas, acentos, `und`, `cx`, `mÃƒÂ§`, `mc`, `sc`, `kg`, `caixa`, `maÃƒÂ§o` e `saco`.
- ApÃƒÂ³s importar, o app pergunta para qual cliente/unidade enviar e confirma antes de mandar para o sistema.
- Produtos importados sem valor unitÃƒÂ¡rio continuam sendo enviados sem preÃƒÂ§o, para o sistema usar o valor atual cadastrado.

## [1.0.26] - 17/07/2026

### OrÃ§amentos dentro do Monteiro

- A Ã¡rea de OrÃ§amentos deixou de aparecer como aba principal do sistema.
- O acesso aos orÃ§amentos fica somente dentro do Monteiro, no site/desktop.
- O botÃ£o roxo OrÃ§amentos agora abre a tela de orÃ§amento dentro do prÃ³prio Monteiro, sem sair para outra aba principal.
- OrÃ§amentos foi removido do menu lateral e da matriz de permissÃµes de abas principais.

## [1.0.25] - 17/07/2026

### OrÃ§amentos somente no site desktop

- O atalho roxo OrÃ§amentos no cabeÃ§alho do Monteiro passa a aparecer apenas no site/desktop.
- O botÃ£o fica oculto no layout mobile para nÃ£o confundir com aÃ§Ãµes do celular.

## [1.0.24] - 17/07/2026

### Atalho de OrÃ§amentos no Monteiro

- Adicionado botÃ£o roxo OrÃ§amentos no cabeÃ§alho do Monteiro, ao lado de LanÃ§ar Venda.
- O botÃ£o fica separado visualmente para nÃ£o confundir orÃ§amento com venda.
- Ao clicar, o Monteiro fecha e abre diretamente a aba OrÃ§amento.

## [1.0.23] - 17/07/2026

### OrÃ§amento com duas empresas emissoras

- A aba OrÃ§amento ganhou seleÃ§Ã£o da empresa emissora: Menina da Estrada ou Menina dos Raios.
- Adicionados dados em portuguÃªs da Menina dos Raios LTDA, CNPJ, endereÃ§o, email, WhatsApp e logo.
- O cabeÃ§alho e a impressÃ£o/PDF do orÃ§amento mudam automaticamente conforme a empresa escolhida.
- Cada proposta salva passa a guardar qual empresa emitiu o orÃ§amento.
- A lista de propostas salvas mostra a empresa emissora.
- A proposta passa a permitir no mÃ¡ximo 20 itens.
- Ao salvar, produtos digitados sem cadastro disparam a pergunta: produto nÃ£o cadastrado, deseja cadastrar?
- Produtos cadastrados na aba OrÃ§amento continuam separados da aba Produtos principal.

## [1.0.22] - 17/07/2026

### Aba OrÃ§amento - Menina da Estrada

- Criada a nova aba OrÃ§amento no sistema.
- Adicionado modelo de proposta baseado no PDF de referÃªncia, com dados fixos da empresa Menina da Estrada / J. M. de Lima.
- IncluÃ­da a logo da Menina da Estrada no modelo e na impressÃ£o da proposta.
- Criado cadastro separado de produtos para orÃ§amento, sem misturar com a aba Produtos atual.
- Criado banco separado para propostas, itens da proposta e produtos de orÃ§amento.
- A proposta salva mantÃ©m cliente, dados cadastrais, produtos, descontos, forma de pagamento, observaÃ§Ãµes, validade e total.
- Adicionado botÃ£o para imprimir ou salvar a proposta como PDF pelo navegador.

## [1.0.21] - 14/07/2026

### Dashboard mensal do Consolidado

- Os cards principais do sistema passam a mostrar o relatorio do mes atual.
- Total Consolidado, NF-e, Produtor Rural, Avulso, Ticket Medio e Avarias agora resetam automaticamente a cada mes.
- A API de resumo passou a aceitar filtro por mes e ano, mantendo compatibilidade com consultas anuais.
- Os rotulos dos cards foram ajustados para indicar que os valores exibidos sao mensais.

## [1.0.20] - 12/07/2026

### Recorrencia no Calendario APP

- A janela Nova notificacao ganhou opcao de recorrencia mensal.
- Ao informar por quantos meses, o sistema cria automaticamente uma notificacao por mes.
- A edicao continua individual para evitar alterar uma serie inteira sem querer.
- Recorrencias mensais agora aparecem unificadas em uma unica linha no site, evitando poluicao visual.
- A linha agrupada mostra o periodo da recorrencia, a proxima data e permite ver os meses.
- Notificacoes pendentes com data anterior ao dia atual passam a ser concluidas automaticamente.

### Notificacoes individuais do Calendario APP

- Cada item cadastrado no Calendario APP agora aparece como uma notificacao separada no celular.
- Se houver 10 notificacoes no dia, o Android exibira 10 cards distintos para leitura.
- O botao Parar hoje passa a silenciar somente a notificacao escolhida.

## [1.0.19] - 12/07/2026

### Recibos das notas enviadas no app

- Adicionado botao Notas ao lado esquerdo da logo do aplicativo.
- O app passa a manter um historico local das notas enviadas com sucesso para o sistema.
- Cada nota enviada pode emitir recibo dentro do app.
- O recibo pode ser compartilhado diretamente pelo WhatsApp.

## [1.0.18] - 12/07/2026

### Notificacoes sonoras no celular

- As notificacoes do Calendario APP passam a usar canal de alta prioridade no Android, com som e vibracao.
- A notificacao aparece como aviso do celular e pode ser descartada normalmente.
- Adicionado botao Parar hoje para interromper os lembretes daquele dia sem concluir a notificacao no site.
- O app respeita o limite de avisos por dia configurado no Calendario APP.

## [1.0.17] - 12/07/2026

### Calendario de notificacoes internas

- Criada a aba Monteiro > Calendario para cadastrar notificacoes internas do aplicativo.
- As notificacoes do calendario possuem data, detalhes, antecedencia e quantidade de avisos por dia.
- O site permite editar, remover, concluir e devolver notificacoes para pendente.
- O app Android ganhou um sino ao lado da logo para abrir o calendario de notificacoes.
- O app consulta o servidor em segundo plano e mostra avisos locais das notificacoes pendentes dentro da janela de antecedencia.
- Ao marcar uma notificacao como concluida no site, ela para de aparecer para o celular.
- O Calendario APP passa a ter permissao propria no painel de Administracao: admin por padrao, com opcao de liberar editor ou visualizador.

## [1.0.16] â€” 11/07/2026

### CorreÃ§Ã£o das unidades automÃ¡ticas

- MaÃ§Ã£ passa a usar automaticamente a unidade CX.
- Melancia passa a usar sempre UN e exibe Unidade (UN), nunca Peso.
- Toda a tabela de produtos predefinidos foi revisada conforme a relaÃ§Ã£o fornecida.
- Os nomes sÃ£o normalizados para evitar erros causados por acentos, como MaÃ§Ã£, MelÃ£o, LimÃ£o, AÃ§afrÃ£o e PimentÃ£o.
- A unidade oficial dos produtos predefinidos tem prioridade sobre configuraÃ§Ãµes antigas salvas no celular.
- Unidades salvas continuam sendo usadas normalmente para produtos novos cadastrados pelo usuÃ¡rio.

### Recibo das Notas APP no site

- Adicionado botÃ£o Recibo em cada nota enviada pelo celular, tanto pendente quanto concluÃ­da.
- O recibo apresenta cliente, data, situaÃ§Ã£o, produtos, tipo de medida, valores e total.
- IncluÃ­da versÃ£o prÃ³pria para impressÃ£o em papel A4, com Ã¡reas de assinatura.
- O documento identifica que se trata de comprovante interno de pedido e nÃ£o substitui documento fiscal.
- Notas sem valor informado pelo celular passam a usar dinamicamente o preÃ§o atual da aba Produtos do Monteiro.
- Valores trazidos do catÃ¡logo sÃ£o identificados na tela e no recibo, e o total Ã© recalculado automaticamente.

## [1.0.15] â€” 11/07/2026

### Unidade automÃ¡tica por produto

- Cada produto passa a selecionar automaticamente sua unidade cadastrada.
- Ao selecionar um produto, o foco segue diretamente para o campo de medida com a unidade identificada, como Peso (KG).
- O seletor manual de unidade foi retirado da tela principal, deixando o formulÃ¡rio mais curto e fluido.
- Abacaxi, Alface e Melancia usam UN; Cheiro Verde, Couve e ManjericÃ£o usam MC; Laranja usa SC; os demais produtos informados usam KG.
- O cadastro de novo produto agora solicita a unidade KG, UN, CX, MC ou SC e guarda a escolha no celular.
- Ao renomear um produto, sua unidade cadastrada Ã© preservada; ao excluir, ela tambÃ©m Ã© removida.

## [1.0.14] â€” 11/07/2026

### Unidade destacada e resumo de produtos

- O seletor Unidade foi movido para antes do campo Peso/medida, logo abaixo dos botÃµes do catÃ¡logo.
- A Ã¡rea Unidade recebeu fundo amarelo e borda destacada para facilitar sua identificaÃ§Ã£o.
- O teclado passa a ser recolhido automaticamente ao tocar em Adicionar produto.
- O resumo final informa dinamicamente quantos produtos foram adicionados ao pedido.

## [1.0.13] â€” 11/07/2026

### RemoÃ§Ã£o do campo Quantidade

- Removido o campo Quantidade da montagem do pedido.
- Os itens agora usam somente Produto, Peso/medida, Unidade e Valor unitÃ¡rio opcional.
- Quantidade tambÃ©m deixou de aparecer na lista de itens e no conteÃºdo enviado ao sistema.
- A ediÃ§Ã£o de produtos passa a posicionar o cursor diretamente no campo Peso/medida.

## [1.0.12] â€” 11/07/2026

### Fila offline de notas

- Notas que nÃ£o puderem ser enviadas por falta ou instabilidade de internet ficam salvas no celular.
- Adicionada a opÃ§Ã£o Notas pendentes de envio, com contador de notas aguardando transmissÃ£o.
- Cada pendÃªncia mostra cliente, data e quantidade de produtos.
- Ã‰ possÃ­vel reenviar individualmente quando o sinal retornar ou excluir uma pendÃªncia apÃ³s confirmaÃ§Ã£o.
- A nota permanece salva quando uma nova tentativa falha.
- Cada nota conserva seu identificador Ãºnico para impedir duplicaÃ§Ãµes no servidor.
- ApÃ³s salvar offline, o formulÃ¡rio Ã© liberado para montar outro pedido sem perder o anterior.

## [1.0.11] â€” 11/07/2026

### Fluxo Pendente e ConcluÃ­do

- Notas APP novas passam a ser criadas com status Pendente.
- Criadas sub-abas Pendentes e ConcluÃ­das.
- Adicionada aÃ§Ã£o Concluir para finalizar uma nota.
- Notas concluÃ­das podem ser editadas ou devolvidas para Pendente.
- Um novo envio para cliente/data jÃ¡ concluÃ­dos acrescenta os produtos e reabre a nota como Pendente.
- Cliente no cartÃ£o tornou-se clicÃ¡vel e abre uma janela detalhada com todos os produtos.
- Adicionado botÃ£o Ver para abrir os detalhes sem entrar na ediÃ§Ã£o.
- O sino principal passou a contabilizar tambÃ©m Notas APP pendentes.
- O painel do sino identifica separadamente Notas APP e notas de entrega.
- Adicionado contador vermelho diretamente na aba Notas APP.
- As notificaÃ§Ãµes de Notas APP sÃ£o atualizadas periodicamente a cada 30 segundos.

## [1.0.10] â€” 11/07/2026

### VisualizaÃ§Ã£o dinÃ¢mica dos produtos no site

- Cada nota passou a ser exibida como um cartÃ£o independente com Data, Cliente, quantidade de produtos e Total do dia.
- Cada produto agora ocupa uma linha prÃ³pria dentro da nota.
- InformaÃ§Ãµes separadas em colunas: Produto, Quantidade, Tipo, Medida, Valor unitÃ¡rio e Subtotal.
- O tipo de medida Ã© exibido como identificador visual: Peso, Unidade, Caixa, MaÃ§o ou Saco.
- Quantidade e preÃ§o ausentes aparecem como `NÃ£o informado`, facilitando identificar o que precisa ser completado.
- Adicionado subtotal individual por produto quando existe valor unitÃ¡rio.
- A tabela interna possui rolagem horizontal em telas pequenas, preservando a leitura.
- Itens acumulados do mesmo cliente/dia continuam dentro do mesmo cartÃ£o.

## [1.0.9] â€” 11/07/2026

### ConsolidaÃ§Ã£o diÃ¡ria por cliente

- Envios do mesmo cliente na mesma data agora sÃ£o reunidos em uma Ãºnica Nota APP.
- Novos itens sÃ£o acrescentados Ã  nota diÃ¡ria jÃ¡ existente.
- O valor total do cliente no dia Ã© recalculado automaticamente apÃ³s cada envio.
- Reenvios com o mesmo identificador continuam protegidos contra duplicaÃ§Ã£o.
- Notas antigas duplicadas do mesmo cliente e dia sÃ£o consolidadas automaticamente na migraÃ§Ã£o.
- A tabela passou a exibir Itens acumulados e Total do dia.
- O indicador financeiro da aba passou a se chamar Total consolidado.
- Clientes sem nome nÃ£o sÃ£o unidos automaticamente, evitando misturar pedidos desconhecidos.

## [1.0.8] â€” 11/07/2026

### Teclado e visualizaÃ§Ã£o dos valores

- A tela agora Ã© redimensionada quando o teclado Ã© aberto.
- Quantidade, Peso/Medida e Valor unitÃ¡rio rolam automaticamente para uma posiÃ§Ã£o visÃ­vel ao receber foco.
- O campo Valor unitÃ¡rio permanece acima do teclado durante a digitaÃ§Ã£o.
- Valores digitados com ponto ou vÃ­rgula podem ser acompanhados em tempo real.

## [1.0.7] â€” 11/07/2026

### Produtos e campos opcionais

- Produtos novos agora sÃ£o inseridos em ordem alfabÃ©tica junto ao catÃ¡logo existente.
- Quantidade deixou de ser obrigatÃ³ria ao adicionar um item.
- Valor unitÃ¡rio pode ficar vazio mesmo quando o produto ainda nÃ£o possui preÃ§o salvo.
- Peso/Medida continua obrigatÃ³rio para permitir pedidos como `100 KG de COLORAU`.
- Quantidade e Valor nÃ£o informados sÃ£o enviados ao sistema como campos vazios, nÃ£o como zero.
- A lista do pedido e a aba Notas APP exibem `â€”` para informaÃ§Ãµes que ainda serÃ£o completadas.
- Valores jÃ¡ salvos continuam sendo usados automaticamente quando o campo Valor unitÃ¡rio fica vazio.

## [1.0.6] â€” 11/07/2026

### PreÃ§os dos produtos

- O valor unitÃ¡rio passou a ser salvo individualmente para cada produto no aparelho.
- Quando o campo Valor unitÃ¡rio fica vazio, o aplicativo usa automaticamente o preÃ§o atual salvo.
- Quando um novo valor Ã© digitado, o preÃ§o atual do produto Ã© atualizado para os prÃ³ximos pedidos.
- O campo mostra o preÃ§o atual do produto selecionado como referÃªncia.
- Produtos sem preÃ§o cadastrado solicitam o valor somente na primeira utilizaÃ§Ã£o.
- Ao renomear um produto, seu preÃ§o salvo acompanha o novo nome.
- Ao excluir um produto, seu preÃ§o salvo tambÃ©m Ã© removido.

## [1.0.5] â€” 11/07/2026

### Assinatura oficial e Google Play

- Definido o identificador definitivo `br.com.meninadosraios.vendas`.
- Criada chave permanente de assinatura release da Menina dos Raios.
- Criada variante Direct Release para distribuiÃ§Ã£o pelo servidor prÃ³prio.
- Criada variante Google Play em formato Android App Bundle (AAB).
- A variante Google Play nÃ£o solicita permissÃ£o para instalar outros APKs.
- A atualizaÃ§Ã£o externa foi desativada na variante Google Play; atualizaÃ§Ãµes nessa versÃ£o serÃ£o feitas pela prÃ³pria loja.
- A variante direta mantÃ©m a consulta e instalaÃ§Ã£o de atualizaÃ§Ãµes pelo servidor.
- Preparada configuraÃ§Ã£o reproduzÃ­vel para que todas as prÃ³ximas versÃµes usem a mesma identidade criptogrÃ¡fica.

### Pedido e medidas

- Adicionado o campo Peso/Medida abaixo de Quantidade.
- Ordem dos campos alterada para Quantidade, Peso/Medida e Valor unitÃ¡rio.
- O nome da medida muda em tempo real conforme a unidade selecionada.
- Unidades disponÃ­veis limitadas a `KG` (Peso), `UN` (Unidade), `CX` (Caixa), `MC` (MaÃ§o) e `SC` (Saco).
- Removidas as unidades antigas que nÃ£o pertencem Ã  nova lista.
- Campos de quantidade, medida e valor unitÃ¡rio agora aceitam ponto ou vÃ­rgula decimal, incluindo valores como `22,50`.
- O total do item passa a usar Peso/Medida multiplicado pelo Valor unitÃ¡rio.
- Quantidade e Peso/Medida sÃ£o armazenados separadamente no banco Notas APP.
- A ediÃ§Ã£o e a visualizaÃ§Ã£o no site foram adaptadas para mostrar ambos os valores.

## [1.0.4] â€” 11/07/2026

### Aplicativo Android

- Removida do subtÃ­tulo a referÃªncia antiga ao compartilhamento pelo WhatsApp.
- O texto da tela inicial agora informa: `Monte o pedido e envie para o sistema.`

## [1.0.3] â€” 11/07/2026

### AtualizaÃ§Ã£o automÃ¡tica

- Confirmada a verificaÃ§Ã£o automÃ¡tica de atualizaÃ§Ã£o sempre que o aplicativo Ã© aberto.
- O aviso agora mostra claramente o nÃºmero e as novidades da versÃ£o encontrada.
- Adicionada a pergunta direta se o usuÃ¡rio deseja atualizar naquele momento.
- Renomeadas as aÃ§Ãµes para `Atualizar agora` e `Agora nÃ£o`.
- Mantido o botÃ£o manual Verificar atualizaÃ§Ãµes como alternativa.
- Confirmado que o catÃ¡logo de atualizaÃ§Ãµes do servidor estÃ¡ online e acessÃ­vel pelo aplicativo.

## [1.0.2] â€” 11/07/2026

### Sistema web

- Movida a aba Notas APP para depois da aba Pagamentos.
- Corrigida a estrutura HTML para que Notas APP pertenÃ§a ao contÃªiner rolÃ¡vel principal do Monteiro.
- Removido o grande espaÃ§o vazio que empurrava as informaÃ§Ãµes para o final da pÃ¡gina.
- O conteÃºdo de Notas APP agora comeÃ§a imediatamente abaixo da navegaÃ§Ã£o, de cima para baixo.
- Preservadas as estruturas das abas Painel, LanÃ§amentos, Produtos, Clientes e Pagamentos.

## [1.0.1] â€” 11/07/2026

### Aplicativo Android

- SubstituÃ­do o compartilhamento pelo WhatsApp pelo envio direto ao sistema.
- Adicionado envio de notas por cliente com data, produtos, quantidades, unidades, preÃ§os e total.
- Adicionado identificador Ãºnico para impedir notas duplicadas quando houver repetiÃ§Ã£o de envio.
- O pedido permanece no celular quando o servidor nÃ£o confirma o recebimento.
- O pedido sÃ³ Ã© limpo apÃ³s a confirmaÃ§Ã£o do servidor.
- Adicionados clientes predefinidos: PALADAR DISTRITO, PALADAR BASE, SESAU, MATERNIDADE e HGR.
- Adicionada a opÃ§Ã£o OUTRO com preenchimento manual do cliente.
- Adicionada confirmaÃ§Ã£o para continuar quando cliente, data ou produtos estiverem vazios.
- Melhorados alinhamento, espaÃ§amento e aparÃªncia dos botÃµes.
- Produtos adicionados passaram a ser exibidos em cartÃµes com aÃ§Ãµes alinhadas.
- Adicionada verificaÃ§Ã£o automÃ¡tica de atualizaÃ§Ãµes pelo servidor.
- Adicionado botÃ£o manual Verificar atualizaÃ§Ãµes.
- Downloads de atualizaÃ§Ã£o agora sÃ£o validados por SHA-256 antes da instalaÃ§Ã£o.

### Sistema web

- Criada a aba Monteiro > Notas APP.
- Criado banco independente `app_notes.db` para nÃ£o interferir nas vendas e pagamentos existentes.
- Adicionados filtros de notas por cliente, mÃªs e ano.
- Adicionados indicadores de quantidade de notas, clientes e valor total.
- Adicionada visualizaÃ§Ã£o detalhada dos itens enviados pelo celular.
- Adicionadas funÃ§Ãµes para editar e remover notas.
- Administradores e editores podem alterar ou remover notas; outros usuÃ¡rios podem consultar.

### PublicaÃ§Ã£o e servidor

- Criada pasta pÃºblica `backend/static/app-updates`.
- Criados `PUBLICAR_APK.bat` e `PUBLICAR_APK.ps1`.
- O publicador identifica a versÃ£o do APK automaticamente.
- O publicador valida a assinatura e calcula o SHA-256 automaticamente.
- O `ATUALIZAR.bat` passou a oferecer a publicaÃ§Ã£o do APK apÃ³s atualizar o site.
- O changelog passa a ser atualizado e enviado ao servidor durante cada publicaÃ§Ã£o.








