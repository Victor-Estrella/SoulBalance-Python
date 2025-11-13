import os
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, conint, confloat

# Carrega .env se existir (opcional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

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


def build_prompt(data: AjusteRequest) -> str:
    return (
        "Você é o 'SoulBalance AI', consultor de produtividade focado em bem-estar.\n"
        "OBJETIVO: Garantir performance sustentável evitando burnout.\n\n"
        "ENTRADA:\n"
        f"Status de Recuperação: {data.recoveryStatus}\n"
        f"Fadiga Percebida: {data.perceivedFatigue}\n"
        f"Nível de Foco: {data.focusLevel}\n"
        f"Horas de Sono: {data.sleepHours}\n"
        f"Tarefa Principal: {data.mainTask}\n\n"
        "INSTRUÇÕES: Responda em JSON válido com as chaves: \n"
        "diagnostico (string), ajusteCarga (string opcional), recomendacoesAutocuidado (array de strings), "
        "planoDia (array opcional de objetos com titulo, duracaoMin, tipo, detalhes)."
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
        raise HTTPException(status_code=500, detail="Cliente Gemini não inicializado. Configure GEMINI_API_KEY.")

    prompt = build_prompt(req)
    try:
        # API conforme notebook (google.genai)
        resp = _client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        text = getattr(resp, "text", None)
        if not text:
            raise ValueError("Resposta vazia da IA")
        try:
            parsed = json.loads(text)
            # Valida contra o schema de resposta e retorna
            return AjusteResponse(**parsed, rawText=text)
        except Exception:
            # Fallback se não vier JSON
            return AjusteResponse(
                diagnostico="Texto livre recebido.",
                recomendacoesAutocuidado=["Pausa leve 5m"],
                rawText=text
            )
    except HTTPException:
        raise
    except Exception as e:
        # Fallback seguro
        return AjusteResponse(
            diagnostico="Falha na IA",
            recomendacoesAutocuidado=["Respiração 4-7-8", "Alongamento rápido"],
            rawText=str(e)
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
