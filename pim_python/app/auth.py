# app/auth.py
# =============================================================================
# Autenticação extremamente simples para demonstração no PIM.
# - Aceita JSON no /auth/login: { "username": "...", "password": "..." }
# - Gera um token (UUID) guardado em memória (dicionário SESSIONS).
# - /auth/me valida o token e retorna o perfil do usuário.
# - /auth/logout invalida o token.
# - Dependências require_auth / require_professor / require_aluno
#   para proteger rotas por papel.
#
# IMPORTANTE: isso é apenas para protótipo. Em produção:
# - usar hash de senha, armazenamento persistente, JWT com expiração,
#   refresh token, etc.
# =============================================================================

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional, Dict
from uuid import uuid4
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# "Banco" de usuários fixos para demo
# - username → { password, role, ra(opcional), username }
# -----------------------------------------------------------------------------
USERS: Dict[str, Dict] = {
    "aluno": {
        "username": "aluno",
        "password": "aluno123",
        "role": "aluno",
        # RA associado ao aluno (usado pelo /aluno/status)
        "ra": "H76DJH0",
    },
    "professor": {
        "username": "professor",
        "password": "prof123",
        "role": "professor",
    },
}

# -----------------------------------------------------------------------------
# Sessões em memória: token → payload do usuário + expiração
# -----------------------------------------------------------------------------
SESSIONS: Dict[str, Dict] = {}

# Quanto tempo a sessão dura (apenas informativo)
SESSION_TTL = timedelta(hours=8)

# -----------------------------------------------------------------------------
# Modelos de entrada/saída
# -----------------------------------------------------------------------------
class LoginPayload(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    role: str
    username: str
    ra: Optional[str] = None
    exp: datetime

class MeResponse(BaseModel):
    username: str
    role: str
    ra: Optional[str] = None

# -----------------------------------------------------------------------------
# Criação do router
# -----------------------------------------------------------------------------
router = APIRouter(prefix="/auth", tags=["auth"])

# -----------------------------------------------------------------------------
# Funções utilitárias internas
# -----------------------------------------------------------------------------
def _issue_token(user: Dict) -> LoginResponse:
    """Gera e registra um token simples em memória."""
    token = str(uuid4())
    exp = datetime.utcnow() + SESSION_TTL
    SESSIONS[token] = {
        "username": user["username"],
        "role": user["role"],
        "ra": user.get("ra"),
        "exp": exp,
    }
    return LoginResponse(
        token=token,
        role=user["role"],
        username=user["username"],
        ra=user.get("ra"),
        exp=exp,
    )

def _get_session_from_header(authorization: Optional[str]) -> Dict:
    """
    Lê 'Authorization: Bearer <token>' e devolve o payload da sessão.
    Lança 401 se ausente/inválido/expirado.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header ausente.")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization inválido (use Bearer token).")

    token = parts[1]
    sess = SESSIONS.get(token)
    if not sess:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")
    if sess["exp"] < datetime.utcnow():
        # Token expirou — remove e bloqueia
        SESSIONS.pop(token, None)
        raise HTTPException(status_code=401, detail="Token expirado.")
    return sess

# -----------------------------------------------------------------------------
# ENDPOINTS
# -----------------------------------------------------------------------------
@router.post("/login", response_model=LoginResponse)
def login(payload: LoginPayload):
    """
    Autentica usuário a partir de JSON { username, password }.
    Retorna token + perfil. Em caso de erro, 401.
    """
    user = USERS.get(payload.username)
    if not user or payload.password != user["password"]:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos.")
    return _issue_token(user)

@router.get("/me", response_model=MeResponse)
def me(authorization: Optional[str] = Header(None)):
    """
    Retorna o perfil (username/role/ra) do portador do token.
    """
    sess = _get_session_from_header(authorization)
    return MeResponse(username=sess["username"], role=sess["role"], ra=sess.get("ra"))

@router.post("/logout")
def logout(authorization: Optional[str] = Header(None)):
    """
    Invalida o token atual (remove da memória). Não dá erro se já estiver inválido.
    """
    try:
        parts = (authorization or "").split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            SESSIONS.pop(parts[1], None)
    except Exception:
        pass
    return {"ok": True}

# -----------------------------------------------------------------------------
# DEPENDÊNCIAS PARA PROTEGER ROTAS
# -----------------------------------------------------------------------------
def require_auth(authorization: Optional[str] = Header(None)) -> Dict:
    """
    Garante que haja um token válido. Retorna o payload da sessão.
    Use em rotas que exigem usuário logado (qualquer papel).
    """
    return _get_session_from_header(authorization)

def require_professor(sess: Dict = Depends(require_auth)) -> Dict:
    """
    Garante que o usuário logado seja professor.
    """
    if sess.get("role") != "professor":
        raise HTTPException(status_code=403, detail="Acesso permitido somente ao professor.")
    return sess

def require_aluno(sess: Dict = Depends(require_auth)) -> Dict:
    """
    Garante que o usuário logado seja aluno.
    """
    if sess.get("role") != "aluno":
        raise HTTPException(status_code=403, detail="Acesso permitido somente ao aluno.")
    return sess
