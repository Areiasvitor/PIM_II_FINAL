# PIM II — Sistema Acadêmico Aprimorado

Interface web e API para o projeto acadêmico **PIM** desenvolvidos com FastAPI (backend) e HTML/CSS/JS puro (frontend). Esta versão traz um tema dark customizado, fluxo de navegação segmentado por perfis (aluno/professor) e módulos prontos para consulta rápida de dados, chatbots e portal do aluno.

---

## 🚀 Stack

- **Backend:** FastAPI (Python 3.10+)
- **Frontend:** HTML + CSS custom (tema “PIM”) + JavaScript vanilla
- **Banco:** Persistência simples em `data/db.json`
- **Ferramentas extras:** script de backup local (`backups/`)

---

## 🔧 Pré-requisitos

- Python 3.10 ou superior instalado
- (opcional) Git — para versionamento e deploy

```bash
python --version
pip --version
```

---

## 🛠️ Instalação e Execução

1. **Clone / copie** o repositório:

```bash
git clone https://github.com/<SEU-USUARIO>/PIM_II_APRIMORADO.git
cd PIM_II_APRIMORADO
```

2. **Crie e ative um ambiente virtual (opcional, mas recomendado):**

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Windows CMD
.venv\Scripts\activate.bat
# Linux/macOS
source .venv/bin/activate
```

3. **Instale as dependências:**

```bash
pip install -r requirements.txt
```

4. **Suba a API (modo local):**

```bash
uvicorn app.main:app --reload
```

5. **Acesse a interface e a documentação:**

- UI: [http://localhost:8000/ui](http://localhost:8000/ui)
- Login dedicado: [http://localhost:8000/login](http://localhost:8000/login)
- Swagger (API): [http://localhost:8000/docs](http://localhost:8000/docs)

> Use `Ctrl+F5` se notar cache antigo de CSS/JS.

---

## 👤 Perfis e Credenciais de Demonstração

| Perfil      | Usuário     | Senha      | Acesso                                           |
|-------------|-------------|------------|--------------------------------------------------|
| Professor   | `professor` | `prof123`  | Consulta rápida, chatbot professor, Swagger      |
| Aluno       | `aluno`     | `aluno123` | Meu status, chatbot secretaria                   |

> Ao logar, o menu lateral e o botão principal exibem apenas os módulos permitidos para cada papel.

---

## 🧭 Estrutura de Pastas (principal)

```
PIM_II_APRIMORADO/
├── app/
│   ├── main.py                # ponto de entrada FastAPI
│   ├── auth.py                # rotas de autenticação e dependências
│   ├── repositories.py        # camada de persistência (JSON)
│   ├── routers/               # módulos de API (alunos, professores etc.)
│   └── ai/                    # intents de chatbot (secretaria/professor)
├── templates/
│   ├── index.html             # dashboard UI (tema PIM)
│   └── login.html             # tela de login
├── static/
│   └── style.css              # tema dark custom
├── data/
│   └── db.json                # base de dados simples (salvo automaticamente)
├── backups/                   # snapshots .zip gerados manualmente
├── requirements.txt
└── README.md
```

---

## 💾 Backup

Snapshots locais são gerados em `backups/` usando:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
$zip = "backups/pim_python-$ts.zip"
Compress-Archive -Path * -DestinationPath $zip -Force
```

> O comando ignora `.venv`, `.git`, `backups` e outros diretórios voláteis no script utilizado.

---

## 📌 Roadmap / Ideias futuras

- Adicionar testes automatizados (pytest) para os principais endpoints
- Integrar autenticação JWT ou OAuth2 para uso em produção
- Criar pipeline CI/CD (GitHub Actions) para formatar, testar e fazer deploy
- Disponibilizar contêiner Docker (API + UI)
- Criar página de métricas/kpis adicionais para professores

---

## 🤝 Contribuições

1. Faça um fork
2. Crie uma branch (`git checkout -b feature/minha-ideia`)
3. Faça commit das mudanças (`git commit -m 'Minha ideia'`)
4. Push para a branch (`git push origin feature/minha-ideia`)
5. Abra um Pull Request

---

## 📜 Licença

Projeto de uso acadêmico. Ajuste a licença conforme necessário (MIT, GPL etc.) antes de publicar.
