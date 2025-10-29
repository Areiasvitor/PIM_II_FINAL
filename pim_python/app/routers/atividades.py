# app/routers/atividades.py
# =============================================================================
# ROTAS DO DOMÍNIO "ATIVIDADES" — ACESSO: PROFESSOR
# -----------------------------------------------------------------------------
# O professor pode:
#   - Criar atividade (vinculada a uma turma existente)
#   - Obter dados de uma atividade
#   - Registrar/atualizar uma entrega (arquivo por RA)
#   - Registrar/atualizar nota de um aluno na atividade
#
# Observação:
#   - "entregas" na Atividade são guardadas como dict[RA] -> payload (arquivo/nota).
#   - Persistência via repositório db (em memória + JSON).
#   - Todas as rotas exigem autenticação de professor (require_professor).
# =============================================================================

from fastapi import APIRouter, HTTPException, Depends            # FastAPI e validações
from pydantic import BaseModel                                   # Pydantic para modelos de entrada
from app.models import AtividadeCreate, Atividade, EntregaCreate # Modelos do domínio
from app.repositories import db                                  # Repositório em memória/JSON
from app.auth import require_professor                           # Dependência de autorização

# Cria o agrupador de rotas para "atividades"
router = APIRouter(prefix="/atividades", tags=["atividades"])

# -----------------------------------------------------------------------------
# POST /atividades/  → Criar nova atividade
# -----------------------------------------------------------------------------
@router.post("/", response_model=Atividade, dependencies=[Depends(require_professor)])
def criar_atividade(payload: AtividadeCreate):
    """
    Cria atividade vinculada a uma turma existente.
    - payload: { "turma_codigo": "TADS01", "titulo": "Atv 1", "data_entrega": "2025-11-30" }
    - O ID é atribuído automaticamente no repositório.
    - Inicia com entregas vazias.
    """
    turma = db.get_turma(payload.turma_codigo)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    # Monta objeto Atividade; id será substituído no add_atividade()
    atv = Atividade(
        id=0,
        turma_codigo=payload.turma_codigo,
        titulo=payload.titulo,
        data_entrega=payload.data_entrega,
        entregas={}
    )
    return db.add_atividade(atv)

# -----------------------------------------------------------------------------
# GET /atividades/{atividade_id}  → Obter atividade específica
# -----------------------------------------------------------------------------
@router.get("/{atividade_id}", response_model=Atividade, dependencies=[Depends(require_professor)])
def obter_atividade(atividade_id: int):
    """
    Retorna todos os dados de uma atividade.
    - Se não existir, retorna 404.
    """
    atv = db.get_atividade(atividade_id)
    if not atv:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.")
    return atv

# -----------------------------------------------------------------------------
# POST /atividades/{atividade_id}/entregar  → Registrar/atualizar entrega
# -----------------------------------------------------------------------------
@router.post("/{atividade_id}/entregar", response_model=Atividade, dependencies=[Depends(require_professor)])
def entregar_atividade(atividade_id: int, entrega: EntregaCreate):
    """
    Registra a entrega de um aluno (por RA) para uma atividade.
    - Se o RA já tiver entrega, o arquivo é atualizado (substitui).
    """
    try:
        return db.add_entrega(atividade_id, entrega.ra, entrega.arquivo)
    except ValueError as e:
        # Mensagens do repositório: "Atividade não encontrada", "Aluno (RA) não encontrado", etc.
        raise HTTPException(status_code=400, detail=str(e))

# -----------------------------------------------------------------------------
# Modelo para lançamento de nota (0..10)
# -----------------------------------------------------------------------------
class NotaCreate(BaseModel):
    """
    Modelo de entrada para registrar nota de um aluno (0..10) em uma atividade.
    - Ex.: { "ra": "H76DJH0", "nota": 8.5 }
    """
    ra: str
    nota: float

# -----------------------------------------------------------------------------
# POST /atividades/{atividade_id}/nota  → Lançar/atualizar nota
# -----------------------------------------------------------------------------
@router.post("/{atividade_id}/nota", response_model=Atividade, dependencies=[Depends(require_professor)])
def registrar_nota(atividade_id: int, payload: NotaCreate):
    """
    Lança ou atualiza a nota de um RA em uma determinada atividade.
    - Valida faixa de 0 a 10 (no repositório).
    - Atualiza o objeto da atividade e persiste no JSON.
    """
    try:
        return db.set_nota(atividade_id, payload.ra, payload.nota)
    except ValueError as e:
        # Pode ocorrer: "Atividade não encontrada", "Aluno (RA) não encontrado", "Nota fora de 0..10", etc.
        raise HTTPException(status_code=400, detail=str(e))
