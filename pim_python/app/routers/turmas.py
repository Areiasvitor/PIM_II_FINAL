# app/routers/turmas.py
# =============================================================================
# ROTAS DO DOMÍNIO "TURMAS" — ACESSO: PROFESSOR
# -----------------------------------------------------------------------------
# O professor pode:
#   - Criar turma
#   - Obter turma por código
#   - Adicionar aluno em turma
#   - Listar atividades de uma turma (visão rápida)
#
# Observação:
#   - Persistência simples via app/repositories.py (em memória + arquivo JSON).
#   - Todas as rotas exigem autenticação de professor (require_professor).
# =============================================================================

from fastapi import APIRouter, HTTPException, Depends            # FastAPI e validações
from typing import List                                          # Tipagem para respostas
from app.models import TurmaCreate, Turma, Atividade             # Modelos Pydantic usados
from app.repositories import db                                  # Repositório in-memory/JSON
from app.auth import require_professor                           # Dependência de autorização

# Cria o agrupador de rotas para "turmas"
router = APIRouter(prefix="/turmas", tags=["turmas"])

# -----------------------------------------------------------------------------
# POST /turmas/  → Criar nova turma
# -----------------------------------------------------------------------------
@router.post("/", response_model=Turma, dependencies=[Depends(require_professor)])
def criar_turma(payload: TurmaCreate):
    """
    Cria uma turma nova com código e nome.
    - payload: { "codigo": "TADS01", "nome": "Análise e Desenvolvimento..." }
    - alunos[] inicia vazio por padrão.
    """
    try:
        # Monta objeto Turma com lista de alunos vazia
        turma = Turma(codigo=payload.codigo, nome=payload.nome, alunos=[])
        # Persiste via repositório (também grava no JSON)
        return db.add_turma(turma)
    except ValueError as e:
        # Ex.: turma duplicada (código já existente)
        raise HTTPException(status_code=400, detail=str(e))

# -----------------------------------------------------------------------------
# GET /turmas/{codigo}  → Buscar detalhes da turma
# -----------------------------------------------------------------------------
@router.get("/{codigo}", response_model=Turma, dependencies=[Depends(require_professor)])
def obter_turma(codigo: str):
    """
    Retorna dados completos de uma turma (código, nome e RAs dos alunos).
    """
    turma = db.get_turma(codigo)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return turma

# -----------------------------------------------------------------------------
# POST /turmas/{codigo}/alunos/{ra}  → Adicionar aluno em turma
# -----------------------------------------------------------------------------
@router.post("/{codigo}/alunos/{ra}", response_model=Turma, dependencies=[Depends(require_professor)])
def adicionar_aluno_na_turma(codigo: str, ra: str):
    """
    Inclui o RA de um aluno já cadastrado dentro da turma.
    - Valida se a turma existe e se o RA do aluno existe.
    - Evita duplicidade de RA na lista.
    """
    try:
        return db.add_aluno_to_turma(codigo, ra)
    except ValueError as e:
        # Mensagens amigáveis do repositório: "Turma não encontrada", "Aluno (RA) não encontrado" etc.
        raise HTTPException(status_code=400, detail=str(e))

# -----------------------------------------------------------------------------
# GET /turmas/{codigo}/atividades  → Listar atividades da turma
# -----------------------------------------------------------------------------
@router.get("/{codigo}/atividades", response_model=List[Atividade], dependencies=[Depends(require_professor)])
def listar_atividades_da_turma(codigo: str):
    """
    Lista todas as atividades vinculadas a uma turma específica (por código).
    - Útil para o professor ter uma visão rápida das atividades cadastradas.
    """
    turma = db.get_turma(codigo)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    # Filtra atividades por turma_codigo
    atividades = [atv for atv in db.atividades.values() if atv.turma_codigo == codigo]
    return atividades
