# app/routers/chatbot.py
# =============================================================================
# CHATBOT (SECRETARIA/FAQ) — por botões + compatível com /perguntar
# -----------------------------------------------------------------------------
# Este router oferece:
# 1) GET /chatbot/faq           -> lista perguntas "oficiais" (para botões do front)
# 2) POST /chatbot/faq/{key}    -> retorna a resposta da pergunta escolhida
# 3) POST /chatbot/perguntar    -> mantido por compatibilidade (regex simples)
#
# Obs.: Mantemos TUDO isolado (sem consultar repositório/relatórios), pois é FAQ.
# =============================================================================

from fastapi import APIRouter, HTTPException, Body
import re

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# -----------------------------------------------------------------------------
# Base de conhecimento — perguntas oficiais (apenas secretaria)
# -----------------------------------------------------------------------------
FAQ = [
    {
        "key": "provas_substitutivas",
        "pergunta": "Perdi uma prova, como funciona as substitutivas?",
        "resposta": (
            "Provas substitutivas: agende no portal do aluno e compareça "
            "na semana de provas substitutivas, no dia do professor da disciplina. "
            "Neste ano, de 21/novembro a 24/novembro."
        ),
    },
    {
        "key": "carteirinha_2via",
        "pergunta": "Como solicito 2ª via da carteirinha?",
        "resposta": (
            "2ª via da carteirinha: solicite no portal do aluno (Serviços → Documentos). "
            "Retirada na secretaria em até 5 dias úteis."
        ),
    },
    {
        "key": "trancamento",
        "pergunta": "Como funciona trancamento de disciplina?",
        "resposta": (
            "Trancamento de disciplina: abra requerimento no portal até a 4ª semana letiva. "
            "Sujeito a cobrança proporcional conforme regulamento."
        ),
    },
    {
        "key": "revisao_nota",
        "pergunta": "Como pedir revisão de nota?",
        "resposta": (
            "Revisão de nota: solicite no portal até 48 horas após a publicação da nota. "
            "A coordenação responde em até 7 dias."
        ),
    },
]

# -----------------------------------------------------------------------------
# 1) Lista de perguntas oficiais (para o frontend mostrar botões)
# -----------------------------------------------------------------------------
@router.get("/faq")
def listar_faq():
    """Retorna a lista de perguntas oficiais (somente secretaria)."""
    return {"faq": [{"key": f["key"], "pergunta": f["pergunta"]} for f in FAQ]}

# -----------------------------------------------------------------------------
# 2) Resposta para uma pergunta escolhida por 'key'
# -----------------------------------------------------------------------------
@router.post("/faq/{key}")
def responder_faq(key: str):
    """Retorna a resposta para a pergunta oficial escolhida."""
    for f in FAQ:
        if f["key"] == key:
            return {"pergunta": f["pergunta"], "resposta": f["resposta"]}
    raise HTTPException(404, "Pergunta não encontrada.")

# -----------------------------------------------------------------------------
# 3) /perguntar compatível (regex simples) — caso o botão use texto
# -----------------------------------------------------------------------------
INTENTS = [
    (r"substitutiv", "provas_substitutivas"),
    (r"2.?via.*carteirinh", "carteirinha_2via"),
    (r"trancament", "trancamento"),
    (r"revis[aã]o.*nota", "revisao_nota"),
]

def _action(name: str) -> str:
    """Mapeia a action para a mesma resposta do FAQ."""
    for f in FAQ:
        if f["key"] == name:
            return f["resposta"]
    return "Desculpe, não encontrei a informação."

@router.post("/perguntar")
def perguntar(payload: dict = Body(...)):
    """
    Recebe {"pergunta": "..."} e tenta casar com alguma intent.
    Mantido por compatibilidade. Para a UI nova, use /faq + /faq/{key}.
    """
    pergunta = (payload.get("pergunta") or "").lower()
    if not pergunta:
        raise HTTPException(400, "Envie a chave 'pergunta'.")

    for pattern, key in INTENTS:
        if re.search(pattern, pergunta):
            return {"pergunta": pergunta, "resposta": _action(key)}

    # Se não casou, sugere usar as perguntas oficiais
    return {
        "pergunta": pergunta,
        "resposta": "Não reconheci. Use as perguntas oficiais via botões.",
        "exemplos": [f["pergunta"] for f in FAQ],
    }
