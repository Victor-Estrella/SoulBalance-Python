import os
import json
import re
from typing import List, Optional
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, conint, confloat

# Carrega .env se existir (opcional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Logging básico (em produção, ajuste para JSON logs/níveis adequados)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s %(message)s')

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    # Não interrompe o boot; retornaremos erro 500 nas chamadas
    print("[WARN] GEMINI_API_KEY não definido. Configure sua variável de ambiente.")

try:
    # SDK oficial novo (conforme seu notebook):
    from google import genai
    _client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
    MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
except Exception as e:
    print(f"[WARN] Falha ao importar google.genai: {e}")
    _client = None
    MODEL_NAME = "gemini-2.5-flash"


class AjusteRequest(BaseModel):
    recoveryStatus: conint(ge=0, le=10) = Field(..., description="0-10")
    perceivedFatigue: conint(ge=0, le=10) = Field(..., description="0-10")
    focusLevel: conint(ge=0, le=10) = Field(..., description="0-10")
    sleepHours: confloat(ge=0, le=24) = Field(..., description="0-24")
    mainTask: str = Field(..., min_length=1)


class PlanoDiaItem(BaseModel):
    titulo: str
    duracaoMin: Optional[int] = None
    tipo: Optional[str] = None
    detalhes: Optional[str] = None


class AjusteResponse(BaseModel):
    diagnostico: str
    ajusteCarga: Optional[str] = None
    recomendacoesAutocuidado: List[str] = []
    planoDia: Optional[List[PlanoDiaItem]] = None
    rawText: Optional[str] = None
    error: Optional[str] = None


def parse_text_fallback(text: str) -> AjusteResponse:
    try:
        # Quebra simples em linhas/marcadores e extrai heurísticas
        parts = re.split(r"[\r\n\*•]+", text)
        lines = [s.strip() for s in parts if s and s.strip()]
        diagnostico = lines[0][:140] if lines else "Texto livre recebido."
        suggestion_verbs = re.compile(r"^(faça|pausa|respiração|alongamento|hidrate|caminhe|medite|planeje|descanse|evite|reduza|aumente|organize)", re.I)
        recs = [l for l in lines[1:] if suggestion_verbs.search(l) or re.search(r"\d+\s?m(in)?", l)]
        recs = recs[:5] if recs else ["Pausa leve 5m"]
        ajuste_carga = None
        m = re.search(r"(reduz\w+|diminu\w+|aument\w+|eleve)[^\.!?]{0,80}", text, re.I)
        if m:
            ajuste_carga = m.group(0).strip()
        return AjusteResponse(
            diagnostico=diagnostico,
            ajusteCarga=ajuste_carga,
            recomendacoesAutocuidado=recs,
            rawText=text
        )
    except Exception as e:
        return AjusteResponse(
            diagnostico="Texto livre recebido.",
            recomendacoesAutocuidado=["Pausa leve 5m"],
            rawText=text,
            error=str(e)
        )


def build_prompt(data: AjusteRequest) -> str:
    return (
        "Você é o \"SoulBalance AI\", um consultor de produtividade focado em bem-estar.\n"
        "OBJETIVO: Garantir a performance sustentável do usuário, evitando burnout e otimizando a recuperação.\n\n"
        "ENTRADA:\n"
        f"- Status de Recuperação (0-10): {data.recoveryStatus}\n"
        f"- Fadiga Percebida (0-10): {data.perceivedFatigue}\n"
        f"- Nível de Foco (0-10): {data.focusLevel}\n"
        f"- Horas de Sono (última noite): {data.sleepHours}\n"
        f"- Tipo de Tarefa/Missão Principal do Dia: {data.mainTask}\n\n"
        "REGRAS PARA AJUSTE DE CARGA:\n"
        "- Se a Recuperação for alta (> 7) e a Fadiga baixa (< 3): recomende manter a carga ou focar em tarefas complexas.\n"
        "- Se a Recuperação for baixa (< 5) ou a Fadiga for alta (> 6): recomende redução de carga (ex.: reduzir duração em ~20%) e/ou troca de foco (priorizar atividades menos cognitivas ou criativas).\n\n"
        "SAÍDA (RESPONDA SOMENTE ESTRITAMENTE UM OBJETO JSON VÁLIDO):\n"
        "O objeto deve conter as chaves: \n"
        "  - diagnostico: string (curta avaliação do estado),\n"
        "  - ajusteCarga: string (opcional, recomendação sobre carga/tarefas),\n"
        "  - recomendacoesAutocuidado: array de strings (1-3 ações específicas),\n"
        "  - planoDia: opcional array de objetos com { titulo, duracaoMin (opcional), tipo (opcional), detalhes (opcional) }\n\n"
        "EXIJA JSON VÁLIDO: Responda APENAS o JSON sem texto adicional, explicações ou marcações.\n\n"
        "EXEMPLO DE SAÍDA (somente para referência, NÃO inclua texto adicional):\n"
        "{\n"
        "  \"diagnostico\": \"Sinais de fadiga leve, foco moderado\",\n"
        "  \"ajusteCarga\": \"Reduzir duração das tarefas cognitivas em 20% e priorizar blocos curtos\",\n"
        "  \"recomendacoesAutocuidado\": [\"Pausa de 10 min a cada 90 min\", \"Caminhada leve de 10 min\"],\n"
        "  \"planoDia\": [{\"titulo\": \"Sessão de estudo\", \"duracaoMin\": 45, \"tipo\": \"cognitivo\"}]\n"
        "}\n"
    )


app = FastAPI(title="SoulBalance AI Proxy", version="1.0.0")

# CORS aberto para desenvolvimento; restrinja em produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz():
    return {"ok": True, "model": MODEL_NAME, "hasKey": bool(GEMINI_API_KEY)}


@app.post("/api/ai/ajuste", response_model=AjusteResponse)
def ajustar_carga(req: AjusteRequest):
    if _client is None:
        logging.error("Chamado /api/ai/ajuste sem cliente Gemini inicializado")
        raise HTTPException(status_code=500, detail="Cliente Gemini não inicializado. Configure GEMINI_API_KEY.")

    prompt = build_prompt(req)
    try:
        # API conforme notebook (google.genai) forçando retorno JSON
        generation_config = {
            "temperature": float(os.getenv("GEN_TEMPERATURE", "0.3")),
            "max_output_tokens": int(os.getenv("GEN_MAX_TOKENS", "400")),
            "response_mime_type": "application/json",
        }
        logging.info("Gerando conteúdo com modelo=%s", MODEL_NAME)
        resp = _client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            generation_config=generation_config,
        )
        text = getattr(resp, "text", None)
        if not text:
            raise ValueError("Resposta vazia da IA")
        try:
            parsed = json.loads(text)
            # Valida contra o schema de resposta e retorna
            return AjusteResponse(**parsed, rawText=text)
        except Exception:
            # Tenta extrair um bloco JSON de dentro do texto livre
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                try:
                    parsed2 = json.loads(m.group(0))
                    return AjusteResponse(**parsed2, rawText=text)
                except Exception:
                    pass
            # Fallback heurístico se não vier JSON estrito
            logging.warning("Resposta não-JSON recebida; aplicando heurísticas de parsing")
            return parse_text_fallback(text)
    except HTTPException:
        raise
    except Exception as e:
        # Fallback seguro com detalhe do erro
        logging.exception("Erro ao gerar conteúdo da IA: %s", e)
        return AjusteResponse(
            diagnostico="Falha na IA",
            recomendacoesAutocuidado=["Respiração 4-7-8", "Alongamento rápido"],
            rawText=str(e),
            error=str(e)
        )


@app.post("/debug/echo")
async def debug_echo(request: Request):
    try:
        data = await request.json()
        return {"ok": True, "received": data}
    except Exception as e:
        raw = await request.body()
        return {
            "ok": False,
            "error": str(e),
            "raw": raw.decode("utf-8", "ignore"),
            "content_type": request.headers.get("content-type")
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
