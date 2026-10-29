# Menina dos Raios — aplicativo Android

Fontes oficiais centralizados neste repositório, na branch `main`, junto com o ERP.
A versão preparada é 2.0.45 (versionCode 72). O histórico funcional está em `CHANGELOG-APP.md`.

## Compilação

Use JDK e Android SDK compatíveis com o projeto e execute `gradlew.bat assembleDirectRelease` nesta pasta.
A distribuição oficial usa a variante `direct`; a variante `play` não habilita a atualização própria.

Antes de compilar, configure localmente `local.properties` com `sdk.dir`, `SERVER_BASE_URL` e `APP_NOTES_TOKEN`.
A assinatura oficial depende da chave existente e do arquivo local `signing/keystore.properties`.
Esses arquivos são ignorados pelo Git; nunca gere outra chave para substituir a oficial.
O projeto anterior em `Documentos/vendas APK` foi preservado com sua configuração local.

## Publicação

Siga `../AGENTS.md`: confira assinatura, identidade, versão, hash e catálogos; publique com backup e staging no PowerShell externo.
Backend e APK têm validação independente. A versão preparada contém os alertas de Novo Tempo limitados a notas entregues e o Calendário com ação de abertura direta.

Artefato compilado: `br.com.meninadosraios.vendas`, 2.756.287 bytes.
SHA-256 do APK: `7c9d4bb285c493675b7b512c45a76a1b63bbf6b429953759eb268ddadd9d4883`.
SHA-256 do certificado oficial: `d9e833244c3a3db92428e83b6badb63a88058064fc1a2ee3996c799e60a16d3f`.
