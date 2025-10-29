# app/main.py
# =============================================================================
# APLICAÇÃO FASTAPI — Ponto de Entrada
# -----------------------------------------------------------------------------
# O que este arquivo faz?
# - Cria a aplicação FastAPI, configura CORS, templates, estáticos e a rota /ui.
# - Registra TODOS os routers funcionais do sistema:
#   alunos, turmas, atividades, relatorios, chatbot (secretaria),
#   chatbot_prof (professor), consulta_rapida (professor), aluno_portal (status),
#   e auth (login/logout).
#
# Observações práticas:
# - Se você abrir o frontend por /ui, o CORS é dispensável (mas mantemos).
# - Se alguma dependência faltar, a API inicia e mostra WARN (evita "quebrar").
# - Este arquivo foi escrito para ser CLARO e MANUTENÍVEL (comentado linha a linha).
# =============================================================================

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# -----------------------------------------------------------------------------
# Criação da aplicação
# -----------------------------------------------------------------------------

app = FastAPI(title="Sistema Acadêmico Colaborativo (PIM)")

# -----------------------------------------------------------------------------
# CORS — Permite que um site externo (ex.: Live Server VSCode) consuma a API
# -----------------------------------------------------------------------------
# Se você acessar a UI por /ui, CORS não é exigido. Mantemos por compatibilidade.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# TEMPLATES (Jinja2) e STATIC
# -----------------------------------------------------------------------------
# templates/ → onde fica o index.html renderizado pela rota /ui
# static/    → css/js/imagens (se existir, montamos em /static)
# -----------------------------------------------------------------------------

_templates_dir = Path("templates")
templates = Jinja2Templates(directory=str(_templates_dir))

_static_dir = Path("static")
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# -----------------------------------------------------------------------------
# Registro de Routers
# -----------------------------------------------------------------------------
# Registra cada módulo de rota de forma isolada, com try/except para evitar
# que a ausência de um arquivo derrube toda a API (mostramos um WARN).
# -----------------------------------------------------------------------------

def _safe_include(router_module_path: str, attr_router: str = "router", label: Optional[str] = None):
    """
    Importa um módulo de rotas de forma segura e, se existir o atributo 'router',
    inclui na aplicação. Se der erro, exibe um aviso (sem derrubar a API).
    - router_module_path: caminho do módulo (ex.: 'app.routers.alunos')
    - attr_router: nome do objeto APIRouter dentro do módulo (padrão 'router')
    - label: nome amigável para log (opcional)
    """
    try:
        mod = __import__(router_module_path, fromlist=[attr_router])
        router = getattr(mod, attr_router, None)
        if router is not None:
            app.include_router(router)
        else:
            print(f"[WARN] Router '{label or router_module_path}' não foi registrado (módulo sem '{attr_router}').")
    except Exception as e:
        print(f"[WARN] Router '{label or router_module_path}' não carregado: {e}")

# alunos / turmas / atividades / relatorios (núcleo)
_safe_include("app.routers.alunos", label="alunos")
_safe_include("app.routers.turmas", label="turmas")
_safe_include("app.routers.atividades", label="atividades")
_safe_include("app.routers.relatorios", label="relatorios")

# chatbot (secretaria — aluno) e chatbot_prof (professor)
_safe_include("app.routers.chatbot", label="chatbot (secretaria)")
_safe_include("app.routers.chatbot_prof", label="chatbot_prof")

# consulta_rapida (professor) e portal do aluno (status)
_safe_include("app.routers.consulta_rapida", label="consulta_rapida")
_safe_include("app.routers.aluno_portal", label="aluno_portal")

# auth (login/logout)
try:
    from app import auth as _auth
    if hasattr(_auth, "router"):
        app.include_router(_auth.router)
    else:
        print("[WARN] Router '/auth' não foi registrado (módulo 'auth' sem router).")
except Exception as e:
    print(f"[WARN] Módulo 'auth' não carregado: {e}")

# -----------------------------------------------------------------------------
# Rota de UI (frontend simples) — Renderiza templates/index.html
# -----------------------------------------------------------------------------
# Abre a interface visual do sistema direto da API em /ui.
# Se templates/index.html não existir, devolve uma dica útil ao usuário.

@app.get("/ui")
def ui(request: Request):
    index_path = _templates_dir / "index.html"
    if not index_path.exists():
        return {
            "erro": "templates/index.html não encontrado. "
                    "Crie a pasta 'templates' na raiz e inclua um index.html."
        }
    return templates.TemplateResponse("index.html", {"request": request})

# Página de login simples (renderiza templates/login.html)
@app.get("/login")
def login_page(request: Request):
    login_path = _templates_dir / "login.html"
    if not login_path.exists():
        return {"erro": "templates/login.html não encontrado."}
    return templates.TemplateResponse("login.html", {"request": request})

# -----------------------------------------------------------------------------
# Rotas utilitárias / status
# -----------------------------------------------------------------------------

@app.get("/health")
def health():
    """Ping simples para teste/monitoramento (retorna sempre ok=True)."""
    return {"ok": True}

@app.get("/")
def root():
    """Status da API + dicas de navegação."""
    return {"status": "ok", "msg": "API do PIM rodando. Veja /docs (Swagger) ou /ui (interface)."}
