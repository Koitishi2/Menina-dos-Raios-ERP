from typing import Optional


def _quote_companies():
    return {
        "estrada":{
            "key":"estrada",
            "cnpj":"63.585.166/0001-37",
            "razao_social":"J. M. de Lima",
            "nome_fantasia":"Menina da Estrada",
            "endereco":"Rua Raimundo Alves de Souza, 205 - Jardim Tropical, Boa Vista - Roraima - Brasil",
            "cep":"69314-670",
            "email":"adrianoabreub@gmail.com",
            "whatsapp":"+55 (21) 98426-1686 / (95) 99123-3960",
            "logo":"/assets/menina-estrada-logo.png"
        },
        "raios":{
            "key":"raios",
            "cnpj":"45.783.879/0001-23",
            "razao_social":"Menina dos Raios LTDA",
            "nome_fantasia":"Menina dos Raios",
            "endereco":"Rua Raimundo Alves de Souza, 205 - Jardim Tropical, Boa Vista - Roraima - Brasil",
            "cep":"69314-670",
            "email":"meninadosraios@gmail.com",
            "whatsapp":"+55 (95) 99123-3960 / (21) 98426-1686",
            "logo":"/assets/menina-dos-raios-logo.png"
        }
    }


def _quote_company(key:Optional[str]=None):
    companies=_quote_companies()
    return companies.get((key or "estrada").strip().lower(), companies["estrada"])
