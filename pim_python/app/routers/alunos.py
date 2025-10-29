# app/routers/alunos.py
# =============================================================================
# Rotas relacionadas a ALUNOS.
# Inclui:
#   - POST /alunos/{ra}/notas      (professor)   -> lançar/atualizar NP1/NP2/PIM
#   - GET  /alunos/{ra}/notas      (auth)        -> ver notas + média + situação
#     • aluno só pode ver o próprio RA
#     • professor pode ver qualquer RA
# =============================================================================

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
from app.models import AlunoCreate, Aluno, NotasUpdate, NotasView
from app.repositories import db
from app.auth import require_professor, require_auth

router = APIRouter(prefix="/alunos", tags=["alunos"])

# -------------------------------------------------------------------------
# CRUD simples de alunos (mantenha os seus já existentes)
# -------------------------------------------------------------------------
@router.post("/", response_model=Aluno)
def criar_aluno(payload: AlunoCreate, _=Depends(require_professor)):
    try:
        return db.add_aluno(Aluno(**payload.model_dump()))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=list[Aluno])
def listar_alunos(_=Depends(require_professor)):
    return db.list_alunos()

@router.get("/{ra}", response_model=Aluno)
def obter_aluno(ra: str, _=Depends(require_professor)):
    aluno = db.get_aluno(ra)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")
    return aluno

# -------------------------------------------------------------------------
# >>> NOTAS – PROFESSOR LANÇA / ATUALIZA
# -------------------------------------------------------------------------
@router.post("/{ra}/notas", response_model=NotasView)
def lancar_notas(ra: str, payload: NotasUpdate, _=Depends(require_professor)):
    """
    Lança/atualiza NP1, NP2 e/ou PIM para o RA informado.
    - Qualquer campo omitido é mantido como está.
    """
    try:
        return db.set_notas(ra, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------------------
# >>> NOTAS – LEITURA (ALUNO OU PROFESSOR)
# -------------------------------------------------------------------------
@router.get("/{ra}/notas", response_model=NotasView)
def consultar_notas(ra: str, sess=Depends(require_auth)):
    """
    Retorna notas + média + situação.
    - Aluno logado só pode consultar seu próprio RA (sess['ra']).
    - Professor pode consultar qualquer RA.
    """
    # se for aluno, restringe o RA
    if sess.get("role") == "aluno":
        ra = sess.get("ra")

    try:
        return db.get_status(ra)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
