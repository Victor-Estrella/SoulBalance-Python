import os
from typing import List, Optional
import re

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


def parse_raw_text(text: str) -> tuple[str, Optional[str], List[str]]:
    """Extrai diagnostico, ajusteCarga e recomendações de autocuidado do texto rico da IA.

    A lógica é simples e tolerante: se algo não for encontrado, devolve valores seguros.
    """
    if not text:
        return "Texto livre recebido.", None, ["Pausa leve 5m"]

    # Normaliza quebras de linha e remove excesso de espaços
    normalized = text.replace("\r", "")

    # 1) Diagnóstico Rápido: pegamos o parágrafo após o título correspondente
    diag = None
    m_diag = re.search(r"diagn[óo]stico\s+r[áa]pido[:\n]*(.+?)(?:\n\s*\n|\n\s*\*\*Ajuste|\Z)", normalized, re.IGNORECASE | re.DOTALL)
    if m_diag:
        diag_raw = m_diag.group(1)
        diag = " ".join(line.strip() for line in diag_raw.strip().split("\n") if line.strip())

    # 2) Ajuste de Carga: parágrafo após o título correspondente
    ajuste = None
    m_aj = re.search(r"ajuste\s+de\s+carga\s+sugerido[:\n]*(.+?)(?:\n\s*\n|\n\s*\*\*Recomenda|\Z)", normalized, re.IGNORECASE | re.DOTALL,
)
    if m_aj:
        aj_raw = m_aj.group(1)
        ajuste = " ".join(line.strip() for line in aj_raw.strip().split("\n") if line.strip())

    # 3) Recomendações de Autocuidado: linhas numeradas (1., 2., etc) depois da seção
    recs: List[str] = []
    m_auto = re.search(r"recomenda[çc][ãa]o\s+de\s+autocuidado[:\n]*(.+)", normalized, re.IGNORECASE | re.DOTALL)
    if m_auto:
        bloco = m_auto.group(1)
        for line in bloco.split("\n"):
            line = line.strip(" -*\t")
            m_item = re.match(r"\d+\.\s*(.+)", line)
            if m_item:
                item = m_item.group(1).strip()
                if item:
                    recs.append(item)

    if not diag:
        # fallback: primeira linha não vazia
        for line in normalized.split("\n"):
            line = line.strip()
            if line:
                diag = line
                break
    if not diag:
        diag = "Texto livre recebido."

    if not recs:
        recs = ["Pausa leve 5m"]

    return diag, ajuste, recs


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
        diagnostico, ajuste, recs = parse_raw_text(text)
        return AjusteResponse(
            diagnostico=diagnostico,
            ajusteCarga=ajuste,
            recomendacoesAutocuidado=recs,
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
