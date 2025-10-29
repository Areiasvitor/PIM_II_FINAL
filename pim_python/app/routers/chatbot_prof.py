# app/routers/chatbot_prof.py
# =============================================================================
# CHATBOT DO PROFESSOR — FAQ via botões
# - Lista perguntas oficiais (/faq) para montar botões no frontend
# - Responde por key selecionada (/faq/{key})
# - Sem dependência de banco; conteúdo ajustável pelo professor
# =============================================================================

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/chatbot_prof", tags=["chatbot_professor"])

# Base de perguntas/respostas do professor (ajustável)
FAQ_PROF = [
    {
        "key": "inicio_correcao_ads",
        "pergunta": "Qual a data de inicio de correção das atividades da turma de ADS ?",
        "resposta": "A data limite é 25/10/2025"
    },
    {
        "key": "prazo_atividade_01",
        "pergunta": "Qual é o prazo limite que os alunos tem para enviar a atividade 01 ?",
        "resposta": "A data limite é 10/10/2025"
    },
    {
        "key": "quantidade_atividades",
        "pergunta": "Quantas atividades devem ser postadas para os alunos ?",
        "resposta": "Pelo menos duas atividades"
    },
]

@router.get("/faq")
def listar_faq_prof():
    """
    Devolve apenas key/pergunta para o frontend montar botões.
    """
    return {"faq": [{"key": f["key"], "pergunta": f["pergunta"]} for f in FAQ_PROF]}

@router.post("/faq/{key}")
def responder_faq_prof(key: str):
    """
    Dada uma 'key', retorna a resposta da pergunta correspondente.
    """
    for f in FAQ_PROF:
        if f["key"] == key:
            return {"pergunta": f["pergunta"], "resposta": f["resposta"]}
    raise HTTPException(status_code=404, detail="Pergunta não encontrada.")
