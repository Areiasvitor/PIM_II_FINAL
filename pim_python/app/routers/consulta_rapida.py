# app/routers/consulta_rapida.py
# =============================================================================
# Consulta Rápida (professor)
# - Centraliza tarefas comuns em 5 ações rápidas:
#   (1) atividades da turma
#   (2) pendências de entrega
#   (3) pendências de notas
#   (4) lançar/atualizar notas de ALUNO (np1/np2/pim)
#   (5) status atualizado do ALUNO
# =============================================================================

from fastapi import APIRouter, HTTPException, Body, Depends
from app.repositories import db
from app.auth import require_professor, require_auth

router = APIRouter(prefix="/consulta_rapida", tags=["consulta_rapida"])

# (1) Atividades da turma
@router.get("/atividades/{codigo}")
def atividades_da_turma(codigo: str, _=Depends(require_professor)):
    """
    Lista todas as atividades (id, titulo, data_entrega) de uma turma.
    """
    turma = db.get_turma(codigo)
    if not turma:
        raise HTTPException(404, "Turma não encontrada.")

    atividades = db.atividades_da_turma(codigo)
    return {
        "turma": codigo,
        "total_atividades": len(atividades),
        "atividades": [
            {"id": a.id, "titulo": a.titulo, "data_entrega": a.data_entrega}
            for a in atividades
        ]
    }

# (2) Pendências de entrega
@router.get("/pendencias/entrega/{codigo}")
def pendencias_entrega(codigo: str, _=Depends(require_professor)):
    """
    Para cada atividade da turma, lista RAs que ainda não entregaram.
    """
    try:
        mapa = db.pendencias_entrega(codigo)
    except ValueError as e:
        raise HTTPException(404, str(e))

    return {"turma": codigo, "pendencias_entrega": mapa}

# (3) Pendências de notas
@router.get("/pendencias/notas/{codigo}")
def pendencias_notas(codigo: str, _=Depends(require_professor)):
    """
    Para cada atividade da turma, lista RAs que ainda não possuem nota na entrega.
    """
    try:
        mapa = db.pendencias_nota(codigo)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"turma": codigo, "pendencias_notas": mapa}

# (4) Lançar/Atualizar notas do ALUNO (NP1, NP2, PIM)
@router.post("/notas/{ra}")
def lancar_notas(ra: str, payload: dict = Body(...), _=Depends(require_professor)):
    """
    Lança/atualiza notas de ALUNO (não confundir com nota da ENTREGA).
    Payload aceito (qualquer combinação):
      { "np1": 8.0, "np2": 7.5, "pim": 9.0 }
    Resposta: confirmação + visão consolidada (média e situação).
    """
    if not db.get_aluno(ra):
        raise HTTPException(404, "Aluno não encontrado.")

    np1 = payload.get("np1", None)
    np2 = payload.get("np2", None)
    pim = payload.get("pim", None)

    try:
        result = db.set_notas(ra, np1=np1, np2=np2, pim=pim)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {
        "status": "ok",
        "mensagem": "Notas lançadas/atualizadas com sucesso.",
        "ra": ra,
        **result
    }

# (5) Status atualizado do ALUNO
@router.get("/status/{ra}")
def status_atualizado(ra: str, _=Depends(require_professor)):
    """
    Retorna a visão consolidada de um aluno (np1/np2/pim/media/situacao).
    """
    if not db.get_aluno(ra):
        raise HTTPException(404, "Aluno não encontrado.")
    return {"ra": ra, **(db.get_notas(ra) or {})}
