# Changelog — Menina dos Raios Vendas

Este arquivo registra as alterações funcionais do aplicativo Android e da integração com o sistema.

## Política de versões

- Revisões: `1.0.1`, `1.0.2` até `1.0.999`.
- Após `1.0.999`, a próxima versão será `1.1.0`.
- O `versionCode` interno do Android sempre aumenta a cada APK publicado.
- Uma versão publicada nunca deve ser reutilizada para outro APK.

## [2.0.1] - 12/08/2026

### MÃ³dulo Entregas no app

- Adicionado botÃ£o "Entregas" na tela principal do aplicativo.
- Criada tela prÃ³pria para listar entregas pendentes e concluÃ­das.
- O app busca as notas fiscais do sistema via `/api/sales` usando o token do login compartilhado.
- As entregas sÃ£o agrupadas por data, cliente, NF e entregador para evitar poluiÃ§Ã£o visual quando uma nota tem vÃ¡rios produtos.
- Cada entrega mostra cliente, data, NF, quantidade de produtos, total, entregador, placa e resumo dos itens.
- Adicionada aÃ§Ã£o "Concluir" para marcar a entrega como realizada pelo celular.
- A conclusÃ£o usa o endpoint existente `/api/sales/bulk-delivered`, preservando o fluxo do site.

## [2.0.0] - 12/08/2026

### Login compartilhado + PIN local

- O app passou a exigir login com o mesmo usuÃ¡rio e senha do sistema web.
- A autenticaÃ§Ã£o usa o backend oficial em `/api/auth/login` e guarda o token `x-token` no aparelho.
- Ao abrir novamente, o app pede PIN local de 4 dÃ­gitos antes de liberar a tela principal.
- O PIN fica somente no celular, com hash local, e nÃ£o Ã© enviado ao backend.
- Depois do PIN, o app valida a sessÃ£o no servidor por `/api/auth/me`.
- Adicionado botÃ£o "Sair da conta" para remover login e PIN do aparelho.
- As funÃ§Ãµes atuais de pedido, colagem do WhatsApp, notas pendentes, recibos, calendÃ¡rio e atualizaÃ§Ã£o automÃ¡tica foram preservadas.

## [1.0.27] - 25/07/2026

### ImportaÃ§Ã£o de pedidos do WhatsApp no app

- Adicionado botÃ£o "Colar pedido do WhatsApp" no app Android.
- Ao abrir o app, se existir um pedido copiado no celular, o app pergunta se deseja colar e interpretar.
- O app passa a ler pedidos copiados do WhatsApp e identificar automaticamente produto, medida e unidade.
- CompatÃ­vel com formatos como `produto = 18kg`, `02 caixas de cenoura`, `10 kg de melÃ£o` e `Abacaxi 2 und`.
- IncluÃ­das interpretaÃ§Ãµes para variaÃ§Ãµes com maiÃºsculas, minÃºsculas, acentos, `und`, `cx`, `mÃ§`, `mc`, `sc`, `kg`, `caixa`, `maÃ§o` e `saco`.
- ApÃ³s importar, o app pergunta para qual cliente/unidade enviar e confirma antes de mandar para o sistema.
- Produtos importados sem valor unitÃ¡rio continuam sendo enviados sem preÃ§o, para o sistema usar o valor atual cadastrado.

## [1.0.26] - 17/07/2026

### Orçamentos dentro do Monteiro

- A área de Orçamentos deixou de aparecer como aba principal do sistema.
- O acesso aos orçamentos fica somente dentro do Monteiro, no site/desktop.
- O botão roxo Orçamentos agora abre a tela de orçamento dentro do próprio Monteiro, sem sair para outra aba principal.
- Orçamentos foi removido do menu lateral e da matriz de permissões de abas principais.

## [1.0.25] - 17/07/2026

### Orçamentos somente no site desktop

- O atalho roxo Orçamentos no cabeçalho do Monteiro passa a aparecer apenas no site/desktop.
- O botão fica oculto no layout mobile para não confundir com ações do celular.

## [1.0.24] - 17/07/2026

### Atalho de Orçamentos no Monteiro

- Adicionado botão roxo Orçamentos no cabeçalho do Monteiro, ao lado de Lançar Venda.
- O botão fica separado visualmente para não confundir orçamento com venda.
- Ao clicar, o Monteiro fecha e abre diretamente a aba Orçamento.

## [1.0.23] - 17/07/2026

### Orçamento com duas empresas emissoras

- A aba Orçamento ganhou seleção da empresa emissora: Menina da Estrada ou Menina dos Raios.
- Adicionados dados em português da Menina dos Raios LTDA, CNPJ, endereço, email, WhatsApp e logo.
- O cabeçalho e a impressão/PDF do orçamento mudam automaticamente conforme a empresa escolhida.
- Cada proposta salva passa a guardar qual empresa emitiu o orçamento.
- A lista de propostas salvas mostra a empresa emissora.
- A proposta passa a permitir no máximo 20 itens.
- Ao salvar, produtos digitados sem cadastro disparam a pergunta: produto não cadastrado, deseja cadastrar?
- Produtos cadastrados na aba Orçamento continuam separados da aba Produtos principal.

## [1.0.22] - 17/07/2026

### Aba Orçamento - Menina da Estrada

- Criada a nova aba Orçamento no sistema.
- Adicionado modelo de proposta baseado no PDF de referência, com dados fixos da empresa Menina da Estrada / J. M. de Lima.
- Incluída a logo da Menina da Estrada no modelo e na impressão da proposta.
- Criado cadastro separado de produtos para orçamento, sem misturar com a aba Produtos atual.
- Criado banco separado para propostas, itens da proposta e produtos de orçamento.
- A proposta salva mantém cliente, dados cadastrais, produtos, descontos, forma de pagamento, observações, validade e total.
- Adicionado botão para imprimir ou salvar a proposta como PDF pelo navegador.

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

## [1.0.16] — 11/07/2026

### Correção das unidades automáticas

- Maçã passa a usar automaticamente a unidade CX.
- Melancia passa a usar sempre UN e exibe Unidade (UN), nunca Peso.
- Toda a tabela de produtos predefinidos foi revisada conforme a relação fornecida.
- Os nomes são normalizados para evitar erros causados por acentos, como Maçã, Melão, Limão, Açafrão e Pimentão.
- A unidade oficial dos produtos predefinidos tem prioridade sobre configurações antigas salvas no celular.
- Unidades salvas continuam sendo usadas normalmente para produtos novos cadastrados pelo usuário.

### Recibo das Notas APP no site

- Adicionado botão Recibo em cada nota enviada pelo celular, tanto pendente quanto concluída.
- O recibo apresenta cliente, data, situação, produtos, tipo de medida, valores e total.
- Incluída versão própria para impressão em papel A4, com áreas de assinatura.
- O documento identifica que se trata de comprovante interno de pedido e não substitui documento fiscal.
- Notas sem valor informado pelo celular passam a usar dinamicamente o preço atual da aba Produtos do Monteiro.
- Valores trazidos do catálogo são identificados na tela e no recibo, e o total é recalculado automaticamente.

## [1.0.15] — 11/07/2026

### Unidade automática por produto

- Cada produto passa a selecionar automaticamente sua unidade cadastrada.
- Ao selecionar um produto, o foco segue diretamente para o campo de medida com a unidade identificada, como Peso (KG).
- O seletor manual de unidade foi retirado da tela principal, deixando o formulário mais curto e fluido.
- Abacaxi, Alface e Melancia usam UN; Cheiro Verde, Couve e Manjericão usam MC; Laranja usa SC; os demais produtos informados usam KG.
- O cadastro de novo produto agora solicita a unidade KG, UN, CX, MC ou SC e guarda a escolha no celular.
- Ao renomear um produto, sua unidade cadastrada é preservada; ao excluir, ela também é removida.

## [1.0.14] — 11/07/2026

### Unidade destacada e resumo de produtos

- O seletor Unidade foi movido para antes do campo Peso/medida, logo abaixo dos botões do catálogo.
- A área Unidade recebeu fundo amarelo e borda destacada para facilitar sua identificação.
- O teclado passa a ser recolhido automaticamente ao tocar em Adicionar produto.
- O resumo final informa dinamicamente quantos produtos foram adicionados ao pedido.

## [1.0.13] — 11/07/2026

### Remoção do campo Quantidade

- Removido o campo Quantidade da montagem do pedido.
- Os itens agora usam somente Produto, Peso/medida, Unidade e Valor unitário opcional.
- Quantidade também deixou de aparecer na lista de itens e no conteúdo enviado ao sistema.
- A edição de produtos passa a posicionar o cursor diretamente no campo Peso/medida.

## [1.0.12] — 11/07/2026

### Fila offline de notas

- Notas que não puderem ser enviadas por falta ou instabilidade de internet ficam salvas no celular.
- Adicionada a opção Notas pendentes de envio, com contador de notas aguardando transmissão.
- Cada pendência mostra cliente, data e quantidade de produtos.
- É possível reenviar individualmente quando o sinal retornar ou excluir uma pendência após confirmação.
- A nota permanece salva quando uma nova tentativa falha.
- Cada nota conserva seu identificador único para impedir duplicações no servidor.
- Após salvar offline, o formulário é liberado para montar outro pedido sem perder o anterior.

## [1.0.11] — 11/07/2026

### Fluxo Pendente e Concluído

- Notas APP novas passam a ser criadas com status Pendente.
- Criadas sub-abas Pendentes e Concluídas.
- Adicionada ação Concluir para finalizar uma nota.
- Notas concluídas podem ser editadas ou devolvidas para Pendente.
- Um novo envio para cliente/data já concluídos acrescenta os produtos e reabre a nota como Pendente.
- Cliente no cartão tornou-se clicável e abre uma janela detalhada com todos os produtos.
- Adicionado botão Ver para abrir os detalhes sem entrar na edição.
- O sino principal passou a contabilizar também Notas APP pendentes.
- O painel do sino identifica separadamente Notas APP e notas de entrega.
- Adicionado contador vermelho diretamente na aba Notas APP.
- As notificações de Notas APP são atualizadas periodicamente a cada 30 segundos.

## [1.0.10] — 11/07/2026

### Visualização dinâmica dos produtos no site

- Cada nota passou a ser exibida como um cartão independente com Data, Cliente, quantidade de produtos e Total do dia.
- Cada produto agora ocupa uma linha própria dentro da nota.
- Informações separadas em colunas: Produto, Quantidade, Tipo, Medida, Valor unitário e Subtotal.
- O tipo de medida é exibido como identificador visual: Peso, Unidade, Caixa, Maço ou Saco.
- Quantidade e preço ausentes aparecem como `Não informado`, facilitando identificar o que precisa ser completado.
- Adicionado subtotal individual por produto quando existe valor unitário.
- A tabela interna possui rolagem horizontal em telas pequenas, preservando a leitura.
- Itens acumulados do mesmo cliente/dia continuam dentro do mesmo cartão.

## [1.0.9] — 11/07/2026

### Consolidação diária por cliente

- Envios do mesmo cliente na mesma data agora são reunidos em uma única Nota APP.
- Novos itens são acrescentados à nota diária já existente.
- O valor total do cliente no dia é recalculado automaticamente após cada envio.
- Reenvios com o mesmo identificador continuam protegidos contra duplicação.
- Notas antigas duplicadas do mesmo cliente e dia são consolidadas automaticamente na migração.
- A tabela passou a exibir Itens acumulados e Total do dia.
- O indicador financeiro da aba passou a se chamar Total consolidado.
- Clientes sem nome não são unidos automaticamente, evitando misturar pedidos desconhecidos.

## [1.0.8] — 11/07/2026

### Teclado e visualização dos valores

- A tela agora é redimensionada quando o teclado é aberto.
- Quantidade, Peso/Medida e Valor unitário rolam automaticamente para uma posição visível ao receber foco.
- O campo Valor unitário permanece acima do teclado durante a digitação.
- Valores digitados com ponto ou vírgula podem ser acompanhados em tempo real.

## [1.0.7] — 11/07/2026

### Produtos e campos opcionais

- Produtos novos agora são inseridos em ordem alfabética junto ao catálogo existente.
- Quantidade deixou de ser obrigatória ao adicionar um item.
- Valor unitário pode ficar vazio mesmo quando o produto ainda não possui preço salvo.
- Peso/Medida continua obrigatório para permitir pedidos como `100 KG de COLORAU`.
- Quantidade e Valor não informados são enviados ao sistema como campos vazios, não como zero.
- A lista do pedido e a aba Notas APP exibem `—` para informações que ainda serão completadas.
- Valores já salvos continuam sendo usados automaticamente quando o campo Valor unitário fica vazio.

## [1.0.6] — 11/07/2026

### Preços dos produtos

- O valor unitário passou a ser salvo individualmente para cada produto no aparelho.
- Quando o campo Valor unitário fica vazio, o aplicativo usa automaticamente o preço atual salvo.
- Quando um novo valor é digitado, o preço atual do produto é atualizado para os próximos pedidos.
- O campo mostra o preço atual do produto selecionado como referência.
- Produtos sem preço cadastrado solicitam o valor somente na primeira utilização.
- Ao renomear um produto, seu preço salvo acompanha o novo nome.
- Ao excluir um produto, seu preço salvo também é removido.

## [1.0.5] — 11/07/2026

### Assinatura oficial e Google Play

- Definido o identificador definitivo `br.com.meninadosraios.vendas`.
- Criada chave permanente de assinatura release da Menina dos Raios.
- Criada variante Direct Release para distribuição pelo servidor próprio.
- Criada variante Google Play em formato Android App Bundle (AAB).
- A variante Google Play não solicita permissão para instalar outros APKs.
- A atualização externa foi desativada na variante Google Play; atualizações nessa versão serão feitas pela própria loja.
- A variante direta mantém a consulta e instalação de atualizações pelo servidor.
- Preparada configuração reproduzível para que todas as próximas versões usem a mesma identidade criptográfica.

### Pedido e medidas

- Adicionado o campo Peso/Medida abaixo de Quantidade.
- Ordem dos campos alterada para Quantidade, Peso/Medida e Valor unitário.
- O nome da medida muda em tempo real conforme a unidade selecionada.
- Unidades disponíveis limitadas a `KG` (Peso), `UN` (Unidade), `CX` (Caixa), `MC` (Maço) e `SC` (Saco).
- Removidas as unidades antigas que não pertencem à nova lista.
- Campos de quantidade, medida e valor unitário agora aceitam ponto ou vírgula decimal, incluindo valores como `22,50`.
- O total do item passa a usar Peso/Medida multiplicado pelo Valor unitário.
- Quantidade e Peso/Medida são armazenados separadamente no banco Notas APP.
- A edição e a visualização no site foram adaptadas para mostrar ambos os valores.

## [1.0.4] — 11/07/2026

### Aplicativo Android

- Removida do subtítulo a referência antiga ao compartilhamento pelo WhatsApp.
- O texto da tela inicial agora informa: `Monte o pedido e envie para o sistema.`

## [1.0.3] — 11/07/2026

### Atualização automática

- Confirmada a verificação automática de atualização sempre que o aplicativo é aberto.
- O aviso agora mostra claramente o número e as novidades da versão encontrada.
- Adicionada a pergunta direta se o usuário deseja atualizar naquele momento.
- Renomeadas as ações para `Atualizar agora` e `Agora não`.
- Mantido o botão manual Verificar atualizações como alternativa.
- Confirmado que o catálogo de atualizações do servidor está online e acessível pelo aplicativo.

## [1.0.2] — 11/07/2026

### Sistema web

- Movida a aba Notas APP para depois da aba Pagamentos.
- Corrigida a estrutura HTML para que Notas APP pertença ao contêiner rolável principal do Monteiro.
- Removido o grande espaço vazio que empurrava as informações para o final da página.
- O conteúdo de Notas APP agora começa imediatamente abaixo da navegação, de cima para baixo.
- Preservadas as estruturas das abas Painel, Lançamentos, Produtos, Clientes e Pagamentos.

## [1.0.1] — 11/07/2026

### Aplicativo Android

- Substituído o compartilhamento pelo WhatsApp pelo envio direto ao sistema.
- Adicionado envio de notas por cliente com data, produtos, quantidades, unidades, preços e total.
- Adicionado identificador único para impedir notas duplicadas quando houver repetição de envio.
- O pedido permanece no celular quando o servidor não confirma o recebimento.
- O pedido só é limpo após a confirmação do servidor.
- Adicionados clientes predefinidos: PALADAR DISTRITO, PALADAR BASE, SESAU, MATERNIDADE e HGR.
- Adicionada a opção OUTRO com preenchimento manual do cliente.
- Adicionada confirmação para continuar quando cliente, data ou produtos estiverem vazios.
- Melhorados alinhamento, espaçamento e aparência dos botões.
- Produtos adicionados passaram a ser exibidos em cartões com ações alinhadas.
- Adicionada verificação automática de atualizações pelo servidor.
- Adicionado botão manual Verificar atualizações.
- Downloads de atualização agora são validados por SHA-256 antes da instalação.

### Sistema web

- Criada a aba Monteiro > Notas APP.
- Criado banco independente `app_notes.db` para não interferir nas vendas e pagamentos existentes.
- Adicionados filtros de notas por cliente, mês e ano.
- Adicionados indicadores de quantidade de notas, clientes e valor total.
- Adicionada visualização detalhada dos itens enviados pelo celular.
- Adicionadas funções para editar e remover notas.
- Administradores e editores podem alterar ou remover notas; outros usuários podem consultar.

### Publicação e servidor

- Criada pasta pública `backend/static/app-updates`.
- Criados `PUBLICAR_APK.bat` e `PUBLICAR_APK.ps1`.
- O publicador identifica a versão do APK automaticamente.
- O publicador valida a assinatura e calcula o SHA-256 automaticamente.
- O `ATUALIZAR.bat` passou a oferecer a publicação do APK após atualizar o site.
- O changelog passa a ser atualizado e enviado ao servidor durante cada publicação.
