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
