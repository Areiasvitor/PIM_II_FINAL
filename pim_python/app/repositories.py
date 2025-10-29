# app/repositories.py
# =============================================================================
# Camada de persistência (DataStore)
# -----------------------------------------------------------------------------
# - Guarda alunos, turmas e atividades em memória + salva/recupera de data/db.json
# - Oferece métodos de CRUD e utilitários (entregas, notas, situação do aluno)
# - Totalmente independente de FastAPI (reutilizável em testes/unitários)
# =============================================================================

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Importa os modelos pydantic usados para validar/informar tipos
from app.models import Aluno, Turma, Atividade

# Caminho do arquivo .json (persistência simples)
DATA_FILE = Path("data/db.json")


class DataStore:
    """
    Estrutura de dados principal do sistema.
    - Em memória (dicts) + serialização em JSON.
    - Ids de atividades autoincrementais (_next_atv_id).
    """

    def __init__(self) -> None:
        # Índices em memória
        self.alunos: Dict[str, Aluno] = {}         # RA -> Aluno
        self.turmas: Dict[str, Turma] = {}         # Código -> Turma
        self.atividades: Dict[int, Atividade] = {} # ID -> Atividade
        self._next_atv_id: int = 1                 # Auto-incremento simples

        # Tenta carregar do arquivo (se existir)
        self._load()

    # -------------------------------------------------------------------------
    # Serialização
    # -------------------------------------------------------------------------

    def _load(self) -> None:
        """Carrega o JSON (se existir) e reconstrói os objetos pydantic."""
        if not DATA_FILE.exists():
            return

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)

        # Reconstrói alunos (cada entrada do JSON vira um pydantic Aluno)
        self.alunos = {ra: Aluno(**a) for ra, a in raw.get("alunos", {}).items()}

        # Reconstrói turmas
        self.turmas = {cod: Turma(**t) for cod, t in raw.get("turmas", {}).items()}

        # Reconstrói atividades
        # Observação: se "entregas" contiver dicts (arquivo/nota), o model precisa aceitar.
        self.atividades = {
            int(i): Atividade(**atv) for i, atv in raw.get("atividades", {}).items()
        }

        # Restaura o contador de IDs
        self._next_atv_id = int(raw.get("next_id", 1))

    def _save(self) -> None:
        """Salva todo o estado atual em data/db.json."""
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "alunos": {ra: a.model_dump() for ra, a in self.alunos.items()},
            "turmas": {c: t.model_dump() for c, t in self.turmas.items()},
            "atividades": {i: a.model_dump() for i, a in self.atividades.items()},
            "next_id": self._next_atv_id,
        }

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # -------------------------------------------------------------------------
    # Alunos
    # -------------------------------------------------------------------------

    def add_aluno(self, aluno: Aluno) -> Aluno:
        """Adiciona novo aluno (RA deve ser único)."""
        if aluno.ra in self.alunos:
            raise ValueError("RA já cadastrado.")
        self.alunos[aluno.ra] = aluno
        self._save()
        return aluno

    def get_aluno(self, ra: str) -> Optional[Aluno]:
        """Obtém aluno pelo RA (ou None se não existir)."""
        return self.alunos.get(ra)

    def list_alunos(self) -> List[Aluno]:
        """Lista todos os alunos existentes."""
        return list(self.alunos.values())

    # -------------------------------------------------------------------------
    # Turmas
    # -------------------------------------------------------------------------

    def add_turma(self, turma: Turma) -> Turma:
        """Adiciona nova turma (código deve ser único)."""
        if turma.codigo in self.turmas:
            raise ValueError("Turma já cadastrada.")
        self.turmas[turma.codigo] = turma
        self._save()
        return turma

    def get_turma(self, codigo: str) -> Optional[Turma]:
        """Obtém turma pelo código (ou None)."""
        return self.turmas.get(codigo)

    def add_aluno_to_turma(self, codigo: str, ra: str) -> Turma:
        """
        Adiciona RA à lista de alunos da turma.
        - Valida se a turma/RA existem.
        - Evita duplicata no array.
        """
        turma = self.get_turma(codigo)
        if not turma:
            raise ValueError("Turma não encontrada.")
        if ra not in self.alunos:
            raise ValueError("Aluno (RA) não encontrado.")

        if ra not in turma.alunos:
            turma.alunos.append(ra)

        self._save()
        return turma

    # -------------------------------------------------------------------------
    # Atividades + Entregas
    # -------------------------------------------------------------------------

    def add_atividade(self, atv: Atividade) -> Atividade:
        """Registra uma nova atividade com ID autoincremental."""
        atv.id = self._next_atv_id
        self._next_atv_id += 1
        self.atividades[atv.id] = atv
        self._save()
        return atv

    def get_atividade(self, atv_id: int) -> Optional[Atividade]:
        """Obtém uma atividade pelo ID (ou None)."""
        return self.atividades.get(atv_id)

    def add_entrega(self, atv_id: int, ra: str, arquivo: str) -> Atividade:
        """
        Registra/atualiza a entrega de um aluno numa atividade.
        - Armazena como dict: {"arquivo": "...", "nota": <opcional>}
        """
        atv = self.get_atividade(atv_id)
        if not atv:
            raise ValueError("Atividade não encontrada.")
        if ra not in self.alunos:
            raise ValueError("Aluno (RA) não encontrado.")

        # Se o model aceitar dict, isso funcionará corretamente.
        payload = atv.entregas.get(ra, {})
        if not isinstance(payload, dict):
            payload = {}

        payload["arquivo"] = arquivo
        atv.entregas[ra] = payload

        self._save()
        return atv

    def set_nota_entrega(self, atv_id: int, ra: str, nota: float) -> Atividade:
        """
        Lança/atualiza a NOTA da entrega de um aluno numa atividade (0..10).
        - Não confundir com NP1/NP2/PIM (que são por ALUNO, não por atividade).
        """
        if nota is None:
            raise ValueError("Informe uma nota.")
        try:
            n = float(nota)
        except Exception:
            raise ValueError("Nota inválida.")
        if n < 0 or n > 10:
            raise ValueError("Nota deve estar entre 0 e 10.")

        atv = self.get_atividade(atv_id)
        if not atv:
            raise ValueError("Atividade não encontrada.")
        if ra not in self.alunos:
            raise ValueError("Aluno (RA) não encontrado.")

        payload = atv.entregas.get(ra, {})
        if not isinstance(payload, dict):
            payload = {}
        payload["nota"] = n
        atv.entregas[ra] = payload

        self._save()
        return atv

    # -------------------------------------------------------------------------
    # Notas do ALUNO (NP1, NP2, PIM) + cálculo de média/situação
    # -------------------------------------------------------------------------

    def get_notas(self, ra: str) -> Optional[dict]:
        """
        Retorna notas consolidadas de um aluno:
        {
          "np1": <float|None>,
          "np2": <float|None>,
          "pim": <float|None>,
          "media": <float|None>,
          "situacao": "Aprovado"|"Reprovado"|"Sem notas"
        }
        """
        aluno = self.alunos.get(ra)
        if not aluno:
            return None

        np1 = getattr(aluno, "np1", None)
        np2 = getattr(aluno, "np2", None)
        pim = getattr(aluno, "pim", None)

        media = None
        situacao = "Sem notas"
        if np1 is not None and np2 is not None and pim is not None:
            media = round(((float(np1) * 4) + (float(np2) * 4) + (float(pim) * 2)) / 10, 2)
            situacao = "Aprovado" if media >= 7.0 else "Reprovado"

        return {"np1": np1, "np2": np2, "pim": pim, "media": media, "situacao": situacao}

    def set_notas(self, ra: str, np1=None, np2=None, pim=None) -> dict:
        """
        Atualiza campos de nota de ALUNO (NP1/NP2/PIM) e retorna visão consolidada.
        Valida faixa 0..10 quando valores são fornecidos.
        """
        aluno = self.alunos.get(ra)
        if not aluno:
            raise ValueError("Aluno não encontrado.")

        def _val(v, nome):
            if v is None:
                return
            try:
                n = float(v)
            except Exception:
                raise ValueError(f"{nome} inválida.")
            if n < 0 or n > 10:
                raise ValueError(f"{nome} deve estar entre 0 e 10.")

        _val(np1, "NP1")
        _val(np2, "NP2")
        _val(pim, "PIM")

        if np1 is not None:
            setattr(aluno, "np1", float(np1))
        if np2 is not None:
            setattr(aluno, "np2", float(np2))
        if pim is not None:
            setattr(aluno, "pim", float(pim))

        self._save()
        return self.get_notas(ra)

    # -------------------------------------------------------------------------
    # Utilidades para “Consulta Rápida” do Professor
    # -------------------------------------------------------------------------

    def atividades_da_turma(self, codigo: str) -> List[Atividade]:
        """Lista todas as atividades pertencentes a uma turma."""
        return [a for a in self.atividades.values() if a.turma_codigo == codigo]

    def pendencias_entrega(self, codigo: str) -> Dict[int, List[str]]:
        """
        Para cada atividade da turma, lista RAs que NÃO entregaram.
        Retorno: { atividade_id: [ra1, ra2, ...], ... }
        """
        t = self.get_turma(codigo)
        if not t:
            raise ValueError("Turma não encontrada.")

        out: Dict[int, List[str]] = {}
        for atv in self.atividades_da_turma(codigo):
            faltam = [ra for ra in t.alunos if ra not in atv.entregas.keys()]
            out[atv.id] = faltam
        return out

    def pendencias_nota(self, codigo: str) -> Dict[int, List[str]]:
        """
        Para cada atividade, lista RAs que não possuem 'nota' registrada na entrega.
        Retorno: { atividade_id: [ra1, ra2, ...], ... }
        """
        t = self.get_turma(codigo)
        if not t:
            raise ValueError("Turma não encontrada.")

        out: Dict[int, List[str]] = {}
        for atv in self.atividades_da_turma(codigo):
            sem_nota = []
            for ra in t.alunos:
                payload = atv.entregas.get(ra)
                nota = None
                if isinstance(payload, dict):
                    nota = payload.get("nota")
                # Considera sem nota se não for número válido
                if nota is None:
                    sem_nota.append(ra)
            out[atv.id] = sem_nota
        return out


# Instância global do DataStore (singleton simples)
db = DataStore()
