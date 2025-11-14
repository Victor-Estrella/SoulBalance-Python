# 🧬 SoulBalance AI API --- Consultor de Carga e Recuperação

## 🎯 Objetivo do Projeto

O **SoulBalance AI** é um sistema de consultoria de produtividade com
foco em bem-estar.\
Ele ajuda o usuário a manter uma **performance sustentável**, prevenindo
burnout e sugerindo ajustes inteligentes na carga de trabalho, além de
recomendações de autocuidado.

O sistema atua como um **Consultor de Produtividade**, diagnosticando o
estado atual do usuário com base em métricas fisiológicas e
comportamentais.

------------------------------------------------------------------------

## 🧠 Inteligência Artificial (Gemini)

A API utiliza o modelo **Gemini 2.5 Flash** para interpretar os dados e
gerar respostas estruturadas.

### Como funciona a IA:

-   Um *System Prompt* (função `criar_prompt`) define o papel da IA como
    consultora de bem-estar.
-   A IA recebe as métricas:
    -   Recuperação\
    -   Fadiga\
    -   Foco\
    -   Sono\
    -   Tipo de tarefa\
-   A resposta gerada contém três seções:
    -   **Diagnóstico Rápido**\
    -   **Ajuste de Carga Sugerido**\
    -   **Recomendações de Autocuidado**

A função `parse_raw_text` extrai essas seções usando regex e transforma
tudo em um **JSON tipado**, seguindo o modelo `AjusteResponse`.

------------------------------------------------------------------------

## ⚙️ Arquitetura Técnica

O backend é desenvolvido com **FastAPI**, garantindo alta performance,
tipagem forte e documentação automática.

------------------------------------------------------------------------

## 📜 Componentes Principais

  -----------------------------------------------------------------------
  Componente                          Descrição
  ----------------------------------- -----------------------------------
  **FastAPI**                         Framework principal para criação da
                                      API REST.

  **AjusteRequest (Pydantic)**        Valida os dados enviados pelo
                                      usuário.

  **AjusteResponse (Pydantic)**       Estrutura tipada do retorno da IA.

  **google.genai**                    Biblioteca oficial do Google para
                                      acessar o Gemini.

  **parse_raw_text**                  Converte texto natural em JSON
                                      estruturado.

  **CORS Middleware**                 Permite chamadas da API via
                                      frontend (incluindo localhost).
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 🚀 Como Rodar o Projeto

### 1. Pré-requisitos

-   Python **3.8+**
-   `pip`

------------------------------------------------------------------------

### 2. Instalação das Dependências

``` bash
pip install fastapi uvicorn pydantic google-genai
```

------------------------------------------------------------------------

### 3. Configuração da API Key

Defina sua chave do Gemini na variável de ambiente:

``` bash
export GEMINI_API_KEY="SUA_CHAVE_OBTIDA_AQUI"
```

No Windows (PowerShell):

``` powershell
$env:GEMINI_API_KEY="SUA_CHAVE_OBTIDA_AQUI"
```

------------------------------------------------------------------------

### 4. Executando o Servidor

Se o arquivo se chama `main.py`:

``` bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Se tiver outro nome (ex.: `api_soulbalance.py`):

``` bash
uvicorn api_soulbalance:app --reload --host 0.0.0.0 --port 8000
```

A API ficará disponível em:

    http://localhost:8000

------------------------------------------------------------------------

## 📌 Endpoints da API

### Swagger (Documentação Automática)

    http://localhost:8000/docs

### Endpoints

  ------------------------------------------------------------------------
  Endpoint                             Método         Descrição
  ------------------------------------ -------------- --------------------
  `/healthz`                           GET            Verifica o status do
                                                      servidor e conexão
                                                      ao Gemini.

  `/api/ai/ajuste`                     POST           Envia métricas do
                                                      usuário e recebe
                                                      diagnóstico +
                                                      recomendações.
  ------------------------------------------------------------------------

------------------------------------------------------------------------

## 🧪 Exemplo de Payload (POST `/api/ai/ajuste`)

``` json
{
  "recuperacao": 75,
  "fadiga": 40,
  "foco": 82,
  "sono": 6,
  "tarefa": "Analisar documentos"
}
```

------------------------------------------------------------------------

## 📤 Exemplo de Resposta da API

``` json
{
  "diagnostico": "Sua recuperação está estável e o nível de foco é positivo...",
  "ajuste_carga": "Mantenha tarefas cognitivamente médias por enquanto...",
  "recomendacoes": "Faça pausas a cada 90 minutos, hidrate-se..."
}
```

------------------------------------------------------------------------

## 📎 Observações

-   A API foi criada como um microserviço simples, podendo ser consumida
    por HTML, mobile ou pipelines.
-   Pode ser facilmente deployada em GCP, AWS, Azure ou Docker.

------------------------------------------------------------------------

## 📄 Licença

Este projeto pode ser utilizado para fins acadêmicos, POCs ou estudos.
