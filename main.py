import os
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai


class AjusteRequest(BaseModel):
    recoveryStatus: int
    perceivedFatigue: int
    focusLevel: int
    sleepHours: float
    mainTask: str


class AjusteResponse(BaseModel):
    diagnostico: str
    ajusteCarga: Optional[str] = None
    recomendacoesAutocuidado: List[str]
    planoDia: Optional[list] = None
    rawText: Optional[str] = None


API_KEY = os.getenv("GEMINI_API_KEY") or ""
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

try:
    client = genai.Client(api_key=API_KEY)
except Exception:
    client = None


def criar_prompt(req: AjusteRequest) -> str:
    base = """Você é o "SoulBalance AI", um consultor de produtividade focado em bem-estar. Sua função é analisar dados diários de bem-estar e performance de um usuário para fornecer **ajustes de carga de trabalho e recomendações de autocuidado**.

**OBJETIVO:** Garantir a performance sustentável do usuário, evitando o burnout e otimizando a recuperação.

**ENTRADA DE DADOS:**

* **Status de Recuperação (0-10):** {rec}
* **Fadiga Percebida (0-10):** {fad}
* **Nível de Foco (0-10):** {foc}
* **Horas de Sono (última noite):** {sono}
* **Tipo de Tarefa/Missão Principal do Dia:** {tarefa}

**INSTRUÇÕES DE SAÍDA:**

1. **Diagnóstico Rápido:** Avalie o estado do usuário (ex: "Sinais de fadiga leve, foco baixo").
2. **Ajuste de Carga Sugerido (Se Necessário):**
   * Se a Recuperação for alta (> 7) e a Fadiga baixa (< 3), recomende **manter a carga ou focar em tarefas complexas**.
   * Se a Recuperação for baixa (< 5) ou a Fadiga alta (> 6), recomende **redução de carga** (ex: reduzir duração da tarefa em 20%) e/ou **troca de foco** (ex: priorizar soft skills ou atividades criativas).
3. **Recomendação de Autocuidado (Obrigatória):** Sugira 1 ou 2 ações específicas (pausa, meditação, exercício leve) com base na análise.
"""
    return base.format(
        rec=req.recoveryStatus,
        fad=req.perceivedFatigue,
        foc=req.focusLevel,
        sono=req.sleepHours,
        tarefa=req.mainTask,
    )


app = FastAPI(title="SoulBalance AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz():
    return {"ok": True, "model": MODEL_NAME, "hasKey": bool(API_KEY), "clientReady": client is not None}


@app.post("/api/ai/ajuste", response_model=AjusteResponse)
def ajustar_carga(req: AjusteRequest):
    if client is None:
        return AjusteResponse(
            diagnostico="Falha na IA",
            ajusteCarga=None,
            recomendacoesAutocuidado=["Respiração 4-7-8", "Alongamento rápido"],
            planoDia=None,
            rawText="Cliente Gemini não inicializado. Verifique GEMINI_API_KEY.",
        )

    prompt = criar_prompt(req)
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        text = getattr(response, "text", None) or str(response)
        # Por enquanto, devolvemos texto livre em rawText e um diagnóstico simples
        return AjusteResponse(
            diagnostico="Gerado com sucesso",
            ajusteCarga=None,
            recomendacoesAutocuidado=["Pausa leve 5m"],
            planoDia=None,
            rawText=text,
        )
    except Exception as e:
        return AjusteResponse(
            diagnostico="Falha na IA",
            ajusteCarga=None,
            recomendacoesAutocuidado=["Respiração 4-7-8", "Alongamento rápido"],
            planoDia=None,
            rawText=str(e),
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
