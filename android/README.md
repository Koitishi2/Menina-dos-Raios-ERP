# Menina dos Raios — aplicativo Android

O código-fonte Android é mantido em `android/` neste repositório e acompanha o ERP no branch `main`.
O código-fonte local está preparado para a versão `2.0.50` (`versionCode` `78`); a versão pública permanece em `2.0.49` até validar e concluir o envio oficial. O histórico funcional está em [`../CHANGELOG-APP.md`](../CHANGELOG-APP.md).

## Compilação

Use JDK e Android SDK compatíveis com o projeto e execute `gradlew.bat assembleDirectRelease` nesta pasta.
A distribuição oficial usa a variante `direct`; a variante `play` não habilita a atualização própria.

Antes de compilar, configure localmente `local.properties` com `sdk.dir`, `SERVER_BASE_URL` e `APP_NOTES_TOKEN`.
A assinatura oficial depende da chave existente e do arquivo local `signing/keystore.properties`.
Esses arquivos são ignorados pelo Git; nunca gere outra chave para substituir a oficial.
O projeto anterior em `Documentos/vendas APK` foi preservado com sua configuração local.

## Publicação

Use `../atualizar_apk.bat` como launcher padrão. Ele valida assinatura, identidade, versão, hash e catálogos; publica com backup e staging no PowerShell externo; e confirma o download público por tamanho e SHA-256 com tentativas limitadas e cache-busting.
Backend e APK têm validação independente. A versão `2.0.47` aprimora a atualização própria e agenda notificações nos horários autorizados pelo Android.

Artefato oficial publicado: `br.com.meninadosraios.vendas`, 2766755 bytes.
SHA-256 do APK: `0346ad18833b7c53bf3df8f6e807a8b34c579a9e7bc610a714a85b8b7cf087f9`.
SHA-256 do certificado oficial: `d9e833244c3a3db92428e83b6badb63a88058064fc1a2ee3996c799e60a16d3f`.
