# app/routers/aluno_portal.py
# =============================================================================
# Portal do Aluno — “Meu Status”
# - Mostra np1/np2/pim + média e situação (Aprovado/Reprovado)
# - Protegido por require_auth (qualquer usuário logado pode ver)
# =============================================================================

from fastapi import APIRouter, HTTPException, Depends
from app.repositories import db
from app.auth import require_auth  # middleware/mixin de autenticação

router = APIRouter(prefix="/aluno", tags=["aluno_portal"])

@router.get("/status/{ra}")
def status_aluno(ra: str, _=Depends(require_auth)):
    """
    Retorna o status consolidado do aluno:
    {
      ra, nome, curso, np1, np2, pim, media, situacao
    }
    """
    aluno = db.get_aluno(ra)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")

    notas = db.get_notas(ra) or {}
    # Descobre a(s) turma(s) do aluno pelo RA
    try:
        turmas_aluno = [t.codigo for t in db.turmas.values() if ra in t.alunos]
    except Exception:
        turmas_aluno = []
    turma = turmas_aluno[0] if turmas_aluno else None
    return {
        "ra": ra,
        "nome": aluno.nome,
        "curso": aluno.curso,
        "turma": turma,
        "np1": notas.get("np1"),
        "np2": notas.get("np2"),
        "pim": notas.get("pim"),
        "media": notas.get("media"),
        "situacao": notas.get("situacao", "Sem notas"),
    }
