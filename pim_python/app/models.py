# app/models.py
# =============================================================================
# MODELOS (Pydantic) — Definições de dados trocados pela API
# -----------------------------------------------------------------------------
# Por que este arquivo existe?
# - Centraliza os "contratos" (modelos) usados entre frontend, routers e
#   repositório; facilita manutenção e validação automática.
#
# Observações importantes:
# - Aluno possui campos de notas (np1, np2, pim) Opcionais (podem faltar).
# - Atividade.entregas é um dict RA -> { "arquivo": str, "nota": float|None }.
#   Mantemos como "Dict[str, dict]" para aceitar dados vindos do JSON (persistência),
#   evitando o erro de validação que você viu (Pydantic tentando ler "string").
# =============================================================================

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# ALUNOS
# -----------------------------------------------------------------------------

class AlunoCreate(BaseModel):
    """
    Payload de criação de aluno:
    - nome: nome completo
    - ra: registro acadêmico (deve ser único no sistema)
    - curso: sigla/descrição do curso (ex.: 'ADS')
    """
    nome: str
    ra: str
    curso: str


class Aluno(AlunoCreate):
    """
    Modelo de aluno armazenado:
    - herda nome/ra/curso do AlunoCreate
    - acrescenta campos de NOTAS (opcionais): np1, np2, pim
      * Podem não existir até o professor lançar em /consulta_rapida/notas/{ra}
    """
    np1: Optional[float] = Field(default=None)
    np2: Optional[float] = Field(default=None)
    pim: Optional[float] = Field(default=None)


# -----------------------------------------------------------------------------
# TURMAS
# -----------------------------------------------------------------------------

class TurmaCreate(BaseModel):
    """
    Payload de criação de turma:
    - codigo: identificador único da turma (ex.: 'TADS01')
    - nome: nome amigável (ex.: 'ADS - 1º Semestre')
    """
    codigo: str
    nome: str


class Turma(BaseModel):
    """
    Modelo de turma armazenado:
    - codigo, nome
    - alunos: lista de RAs pertencentes à turma
    """
    codigo: str
    nome: str
    alunos: List[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# ATIVIDADES / ENTREGAS
# -----------------------------------------------------------------------------

class AtividadeCreate(BaseModel):
    """
    Payload de criação de atividade:
    - turma_codigo: código da turma à qual a atividade pertence
    - titulo: título da atividade
    - data_entrega: data-limite (string simples para simplificar)
    """
    turma_codigo: str
    titulo: str
    data_entrega: str


class EntregaCreate(BaseModel):
    """
    Payload para registrar a entrega de um aluno em uma atividade:
    - ra: RA do aluno que está entregando
    - arquivo: identificador/descrição do arquivo enviado (string)
    """
    ra: str
    arquivo: str


class Atividade(BaseModel):
    """
    Modelo de atividade armazenado:
    - id: identificador único (atribuído pelo repositório ao criar)
    - turma_codigo, titulo, data_entrega
    - entregas: dicionário RA -> payload da entrega.
      ATENÇÃO: usamos "Dict[str, dict]" para aceitar tanto dicts puros
      quanto dados carregados do JSON. O repositório já lida com ambos.
      Exemplo de item:
        "H76DJH0": { "arquivo": "Atividade1.pdf", "nota": 9.5 }
    """
    id: int
    turma_codigo: str
    titulo: str
    data_entrega: str
    entregas: Dict[str, dict] = Field(default_factory=dict)
