# app/routers/relatorios.py
# =============================================================================
# RELATÓRIOS/ANALÍTICOS — ACESSO: PROFESSOR
# -----------------------------------------------------------------------------
# Fornece estatísticas e agregações para apoio ao professor:
#   - Panorama geral de turma (entregas por atividade e percentuais)
#   - Média de notas de uma atividade
#   - Distribuição de notas (histograma 0..10) de uma atividade
#   - Total de alunos cadastrados (métrica global)
#
# Observação:
#   - Cálculo não depende de BD externo; usamos o repositório em memória/JSON.
#   - Todas as rotas exigem autenticação de professor (require_professor).
# =============================================================================

from fastapi import APIRouter, HTTPException, Depends   # FastAPI + validações
from typing import Dict, List                           # Tipagem
from app.repositories import db                         # Repositório de dados
from app.auth import require_professor                  # Autorização (somente professor)

# Cria o agrupador de rotas para "relatorios"
router = APIRouter(prefix="/relatorios", tags=["relatorios"])

# -----------------------------------------------------------------------------
# Função utilitária: coletar notas válidas (0..10) de uma atividade
# -----------------------------------------------------------------------------
def _coletar_notas_da_atividade(atv) -> List[float]:
    """
    Coleta todas as notas válidas (0..10) de uma atividade.
    - As entregas podem estar como dict (com chave "nota") ou como objetos
      Pydantic com atributo ".nota". Esta função trata ambos os casos.
    - Ignora ausências de nota ou valores inválidos.
    """
    notas: List[float] = []
    for payload in atv.entregas.values():
        # Caso 1: dicionário {"arquivo": "...", "nota": 8.5}
        if isinstance(payload, dict):
            valor = payload.get("nota", None)
        else:
            # Caso 2: objeto com atributo "nota" (robustez)
            valor = getattr(payload, "nota", None)

        if valor is None:
            continue

        try:
            n = float(valor)
        except (TypeError, ValueError):
            continue

        if 0.0 <= n <= 10.0:
            notas.append(n)

    return notas

# -----------------------------------------------------------------------------
# GET /relatorios/turma/{codigo}  → Panorama geral de uma turma
# -----------------------------------------------------------------------------
@router.get("/turma/{codigo}", dependencies=[Depends(require_professor)])
def relatorio_turma(codigo: str) -> Dict:
    """
    Retorna indicadores da turma:
      - total de alunos
      - total de atividades
      - por atividade: total de entregas e percentual (entregas / alunos)
      - média de entregas por atividade (quantidade absoluta)
    """
    turma = db.get_turma(codigo)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    # Seleciona apenas atividades dessa turma
    atividades = [atv for atv in db.atividades.values() if atv.turma_codigo == codigo]

    resultado: Dict = {
        "turma": turma.codigo,
        "nome": turma.nome,
        "total_alunos": len(turma.alunos),
        "total_atividades": len(atividades),
        "atividades": []
    }

    # Para cada atividade, calcula quantidade e percentual de entregas
    for atv in atividades:
        total_entregas = len(atv.entregas)
        percentual = 0.0
        if turma.alunos:
            percentual = round((total_entregas / len(turma.alunos)) * 100.0, 2)

        resultado["atividades"].append({
            "id": atv.id,
            "titulo": atv.titulo,
            "data_entrega": atv.data_entrega,
            "total_entregas": total_entregas,
            "percentual_entregas": percentual,
        })

    # Média de entregas por atividade (quantitativo)
    if atividades:
        soma = sum(len(atv.entregas) for atv in atividades)
        resultado["media_entregas_por_atividade"] = round(soma / len(atividades), 2)
    else:
        resultado["media_entregas_por_atividade"] = 0.0

    return resultado

# -----------------------------------------------------------------------------
# GET /relatorios/notas/media/{atividade_id}  → Média de notas de uma atividade
# -----------------------------------------------------------------------------
@router.get("/notas/media/{atividade_id}", dependencies=[Depends(require_professor)])
def media_notas(atividade_id: int) -> Dict:
    """
    Calcula a média das notas registradas em uma atividade.
    - Retorna mensagem amigável se não houver notas.
    """
    atv = db.get_atividade(atividade_id)
    if not atv:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.")

    notas = _coletar_notas_da_atividade(atv)
    if not notas:
        return {"atividade_id": atividade_id, "mensagem": "Sem notas registradas."}

    media = round(sum(notas) / len(notas), 2)
    return {"atividade_id": atividade_id, "media": media, "total_notas": len(notas)}

# -----------------------------------------------------------------------------
# GET /relatorios/notas/distribuicao/{atividade_id}  → Histograma 0..10
# -----------------------------------------------------------------------------
@router.get("/notas/distribuicao/{atividade_id}", dependencies=[Depends(require_professor)])
def distribuicao_notas(atividade_id: int) -> Dict:
    """
    Retorna a distribuição (histograma 0..10) das notas de uma atividade.
    - Arredonda cada nota para o inteiro mais próximo ao contar no bucket.
    """
    atv = db.get_atividade(atividade_id)
    if not atv:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.")

    notas = _coletar_notas_da_atividade(atv)
    if not notas:
        return {"atividade_id": atividade_id, "mensagem": "Sem notas registradas."}

    # Inicializa buckets de 0 a 10
    buckets: Dict[int, int] = {i: 0 for i in range(11)}
    for n in notas:
        k = min(max(int(round(n)), 0), 10)
        buckets[k] += 1

    return {"atividade_id": atividade_id, "distribuicao": buckets}

# -----------------------------------------------------------------------------
# GET /relatorios/alunos/total  → Total de alunos cadastrados
# -----------------------------------------------------------------------------
@router.get("/alunos/total", dependencies=[Depends(require_professor)])
def total_alunos() -> Dict:
    """
    Retorna a contagem total de alunos cadastrados no sistema.
    - Métrica global, útil para dashboards.
    """
    return {"total_alunos": len(db.list_alunos())}
