# Menina dos Raios — aplicativo Android

Fontes oficiais centralizados neste repositório, na branch `main`, junto com o ERP.
A versão preparada é 2.0.43 (versionCode 71). O histórico funcional está em `CHANGELOG-APP.md`.

## Compilação

Use JDK e Android SDK compatíveis com o projeto e execute `gradlew.bat assembleDirectRelease` nesta pasta.
A distribuição oficial usa a variante `direct`; a variante `play` não habilita a atualização própria.

Antes de compilar, configure localmente `local.properties` com `sdk.dir`, `SERVER_BASE_URL` e `APP_NOTES_TOKEN`.
A assinatura oficial depende da chave existente e do arquivo local `signing/keystore.properties`.
Esses arquivos são ignorados pelo Git; nunca gere outra chave para substituir a oficial.
O projeto anterior em `Documentos/vendas APK` foi preservado com sua configuração local.

## Publicação

Siga `../AGENTS.md`: confira assinatura, identidade, versão, hash e catálogos; publique com backup e staging no PowerShell externo.
Backend e APK têm validação independente. As notificações do calendário na versão 2.0.42 exigem a correção correspondente no backend.

Artefato compilado: `br.com.meninadosraios.vendas`, 2.755.419 bytes.
SHA-256 do APK: `69df14d36e7c4a9887c281a38d5d068030cef002822f0890dbcb6e39f54254eb`.
SHA-256 do certificado oficial: `d9e833244c3a3db92428e83b6badb63a88058064fc1a2ee3996c799e60a16d3f`.
