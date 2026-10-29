# Menina dos Raios — aplicativo Android

O código-fonte Android é mantido em `android/` neste repositório e acompanha o ERP no branch `main`.
O APK oficial publicado é a versão `2.0.45` (`versionCode` `73`). O histórico funcional está em [`../CHANGELOG-APP.md`](../CHANGELOG-APP.md).

## Compilação

Use JDK e Android SDK compatíveis com o projeto e execute `gradlew.bat assembleDirectRelease` nesta pasta.
A distribuição oficial usa a variante `direct`; a variante `play` não habilita a atualização própria.

Antes de compilar, configure localmente `local.properties` com `sdk.dir`, `SERVER_BASE_URL` e `APP_NOTES_TOKEN`.
A assinatura oficial depende da chave existente e do arquivo local `signing/keystore.properties`.
Esses arquivos são ignorados pelo Git; nunca gere outra chave para substituir a oficial.
O projeto anterior em `Documentos/vendas APK` foi preservado com sua configuração local.

## Publicação

Use `../atualizar_apk.bat` como launcher padrão. Ele valida assinatura, identidade, versão, hash e catálogos; publica com backup e staging no PowerShell externo; e confirma o download público por tamanho e SHA-256 com tentativas limitadas e cache-busting.
Backend e APK têm validação independente. A versão `2.0.45` restringe notificações a admins, agenda cobranças Novo Tempo de vendas entregues e notificações de calendário em horários separados.

Artefato oficial publicado: `br.com.meninadosraios.vendas`, 2.759.094 bytes.
SHA-256 do APK: `808b5a6c26fe6095e013616ec08d8cf5aa0590486922e1994e6310541fe77504`.
SHA-256 do certificado oficial: `d9e833244c3a3db92428e83b6badb63a88058064fc1a2ee3996c799e60a16d3f`.
