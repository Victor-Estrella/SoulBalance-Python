# 🧬 SoulBalance AI API - Consultor de Carga e Recuperação

## 🎯 Objetivo do Projeto

O **SoulBalance AI** é um microserviço de inteligência artificial
desenvolvido para promover a produtividade sustentável ao integrar o
bem-estar do usuário na gestão da carga de trabalho diária.

### Propósito Central

O sistema atua como um **Consultor de Produtividade e Bem-Estar
virtual**. Ele analisa diariamente os dados psico-fisiológicos do
usuário para prevenir o esgotamento (burnout), sugerindo ajustes
inteligentes na carga de trabalho e fornecendo recomendações de
autocuidado altamente personalizadas.\
O objetivo final é **otimizar o desempenho**, garantindo **recuperação e
equilíbrio físico/mental**.

O projeto utiliza uma arquitetura **API REST com FastAPI**, permitindo
integração com qualquer frontend (web, mobile, dashboards).

------------------------------------------------------------------------

## 🧠 Inteligência Artificial (Gemini)

A inteligência é fornecida pelo **Gemini 2.5 Flash**, um modelo
otimizado para raciocínio rápido, interpretação e sumarização.

### Funcionamento e Fluxo da IA

#### 1. Definição da Persona (Prompting Estruturado)

A função `criar_prompt` define o papel da IA como *Consultor de
Produtividade focado em bem-estar*, garantindo regras fixas de
raciocínio e formato da resposta.

#### 2. Análise de Dados

A IA recebe as seguintes métricas do usuário:

-   **Status de Recuperação (0-10)**
-   **Fadiga Percebida (0-10)**
-   **Nível de Foco (0-10)**
-   **Horas de Sono (float)**
-   **Tipo de Tarefa Principal do Dia**

#### 3. Estruturação da Saída (Parsing)

A função `parse_raw_text` utiliza **RegEx** para identificar blocos de
texto na resposta do Gemini e gerar um JSON estruturado
(`AjusteResponse`).

------------------------------------------------------------------------

## ⚙️ Arquitetura Técnica

O backend utiliza **FastAPI**, com suporte a:

-   Tipagem e validação via **Pydantic**
-   Middleware CORS
-   Servidor ASGI com **Uvicorn**
-   Integração com **google-genai**

------------------------------------------------------------------------

## 📜 Componentes e Modelos de Dados

  ------------------------------------------------------------------------
  Componente                  Tipo                        Descrição
  --------------------------- --------------------------- ----------------
  FastAPI                     Framework                   Gerencia rotas,
                                                          middleware e
                                                          lógica central
                                                          do microserviço

  AjusteRequest               Pydantic Model              Define o JSON de
                                                          entrada

  AjusteResponse              Pydantic Model              Estrutura a
                                                          resposta JSON
                                                          enviada ao
                                                          frontend

  google.genai                Biblioteca                  Comunicação com
                                                          o Gemini

  parse_raw_text              Função Core                 Parsing do texto
                                                          livre em JSON
                                                          estruturado

  CORS Middleware             Configuração                Libera o
                                                          frontend para
                                                          acessar a API
  ------------------------------------------------------------------------

------------------------------------------------------------------------

## 🚀 Como Rodar o Projeto

### 1. Pré-requisitos

-   Python 3.8+
-   pip instalado

### 2. Instalação das Dependências

``` bash
pip install fastapi uvicorn pydantic google-genai
```

### 3. Configuração da API Key

Linux/macOS:

``` bash
export GEMINI_API_KEY="SUA_CHAVE_OBTIDA_AQUI"
```

Windows (PowerShell):

``` powershell
$env:GEMINI_API_KEY="SUA_CHAVE_OBTIDA_AQUI"
```

### 4. Executando o Servidor

``` bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em: **http://localhost:8000**

------------------------------------------------------------------------

## 📌 Endpoints da API

Documentação Swagger:\
👉 **http://localhost:8000/docs**

  -----------------------------------------------------------------------
  Endpoint                 Método              Descrição
  ------------------------ ------------------- --------------------------
  `/healthz`               GET                 Verifica status do
                                               servidor e conexão com o
                                               Gemini

  `/api/ai/ajuste`         POST                Endpoint principal que
                                               processa a análise da IA
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 🧪 Exemplo de Uso (POST /api/ai/ajuste)

### 📥 Exemplo de Payload

``` json
{
  "recoveryStatus": 4,
  "perceivedFatigue": 7,
  "focusLevel": 5,
  "sleepHours": 6.0,
  "mainTask": "Preparação para Prova (Cognitivo Alto)"
}
```

### 📤 Exemplo de Resposta

``` json
{
  "diagnostico": "Sinais de fadiga elevada e recuperação baixa, impactando seu foco.",
  "ajusteCarga": "Recomenda-se redução de 25% na tarefa cognitiva.",
  "recomendacoesAutocuidado": [
    "Faça uma pausa ativa de 15 minutos.",
    "Beba água e evite cafeína por 2 horas.",
    "Considere um cochilo de 20 minutos."
  ],
  "planoDia": null,
  "rawText": "O texto completo retornado pela IA."
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
