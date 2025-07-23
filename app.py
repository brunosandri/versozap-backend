from flask import Flask, jsonify, request
from flask_cors import CORS
from database import engine, SessionLocal
from models import Base, Usuario, Leitura
from apscheduler.schedulers.background import BackgroundScheduler
from gtts import gTTS
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash, check_password_hash
import jwt, os, re, requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configurações básicas
# ---------------------------------------------------------------------------
load_dotenv()

SENDER_URL = os.getenv("SENDER_URL")
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "versozap-dev")  # troque em produção
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

app = Flask(__name__)

# CORS detalhado — apenas rotas /api/* precisam e-mail/telefone
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "https://app.versozap.com.br",
                "http://localhost:5173",
            ],
            "allow_headers": ["Content-Type", "Authorization"],
            "methods": ["GET", "POST", "OPTIONS"],
        }
    },
    supports_credentials=False,  # não estamos usando cookies
)

# Fallback para outros endpoints (ex.: /enviar-leitura) — permite tudo
@app.after_request
def apply_cors_headers(resp):
    # Se o Flask‑CORS já adicionou, não duplicamos
    if "Access-Control-Allow-Origin" not in resp.headers:
        origin = request.headers.get("Origin")
        if origin and origin.startswith(("https://app.versozap.com.br", "http://localhost:5173")):
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
            resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return resp

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
TRECHOS_POR_DIA = {
    1: "Gênesis 1",
    2: "Gênesis 2",
    3: "Gênesis 3",
    4: "Mateus 1",
    5: "Salmos 1",
    # ... até 365
}

def obter_trecho_do_dia():
    dia_do_ano = date.today().timetuple().tm_yday
    return TRECHOS_POR_DIA.get(dia_do_ano, "Fim do plano de leitura")

def gerar_audio_versiculo(texto: str, nome_arquivo: str) -> str:
    tts = gTTS(text=texto, lang="pt")
    os.makedirs("audios", exist_ok=True)
    caminho = f"audios/{nome_arquivo}.mp3"
    tts.save(caminho)
    return caminho

# ---------------------------------------------------------------------------
# Jobs de agendamento
# ---------------------------------------------------------------------------

def enviar_leitura_diaria():
    db = SessionLocal()
    usuarios = db.query(Usuario).all()

    for usuario in usuarios:
        agora = datetime.now().strftime("%H:%M")
        if usuario.horario_envio == agora:
            trecho = obter_trecho_do_dia()
            nova_leitura = Leitura(usuario_id=usuario.id, trecho=trecho, concluido=False)
            db.add(nova_leitura)
            db.commit()
            db.refresh(nova_leitura)

            caminho_audio = gerar_audio_versiculo(trecho, f"audio_{usuario.id}_{nova_leitura.id}")

            try:
                requests.post(
                    SENDER_URL,
                    json={
                        "telefone": usuario.telefone,
                        "mensagem": f"Olá {usuario.nome}, seu versículo de hoje é:\n{trecho}",
                        "audio": caminho_audio,
                    },
                )
            except Exception as e:
                print(f"[Erro WhatsApp] {usuario.nome}: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(enviar_leitura_diaria, "interval", minutes=1)
scheduler.start()

# ---------------------------------------------------------------------------
# Rotas públicas
# ---------------------------------------------------------------------------
@app.get("/")
def home():
    return "VersoZap está funcionando!"

@app.get("/versiculo")
def versiculo():
    return jsonify({"versiculo": "Porque Deus amou o mundo…"})

# ---------------------------------------------------------------------------
# Autenticação por E-MAIL
# ---------------------------------------------------------------------------
@app.post("/api/register")
def register_email():
    data = request.get_json() or {}
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    if not EMAIL_RE.match(email):
        return jsonify(error="E-mail inválido"), 400
    if len(password) < 6:
        return jsonify(error="Senha deve ter 6+ caracteres"), 400

    db = SessionLocal()
    if db.query(Usuario).filter_by(email=email).first():
        return jsonify(error="E-mail já cadastrado"), 409

    user = Usuario(nome=email.split("@")[0], email=email)
    user.password_hash = generate_password_hash(password)
    db.add(user)
    db.commit()
    db.refresh(user)

    return jsonify(message="ok"), 201

@app.post("/api/login")
def login_email():
    data = request.get_json() or {}
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    db = SessionLocal()
    user = db.query(Usuario).filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify(error="Credenciais inválidas"), 401

    payload = {"sub": user.id, "exp": datetime.utcnow() + timedelta(days=7)}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return jsonify(token=token, user={"id": user.id, "nome": user.nome}), 200

# ---------------------------------------------------------------------------
# Cadastro via TELEFONE (rota legada)
# ---------------------------------------------------------------------------
@app.post("/api/register-phone")
def cadastrar_usuario_telefone():
    data = request.get_json() or {}
    db = SessionLocal()

    if db.query(Usuario).filter_by(telefone=data.get("telefone")).first():
        return jsonify({"erro": "Usuário já cadastrado"}), 400

    novo_usuario = Usuario(
        nome=data.get("nome"),
        telefone=data.get("telefone"),
        versao_biblia=data.get("versao_biblia"),
        plano_leitura=data.get("plano_leitura"),
        tipo_ordem=data.get("tipo_ordem"),
        horario_envio=data.get("horario_envio"),
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return jsonify({"mensagem": "Usuário cadastrado com sucesso", "id": novo_usuario.id}), 201

# ---------------------------------------------------------------------------
# Endpoints de leitura via WhatsApp (reaproveitados)
# ---------------------------------------------------------------------------
@app.post("/enviar-leitura")
def enviar_leitura():
    data = request.get_json() or {}
    telefone = data.get("telefone")

    db = SessionLocal()
    usuario = db.query(Usuario).filter_by(telefone=telefone).first()
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    leitura_pendente = db.query(Leitura).filter(
        Leitura.usuario_id == usuario.id,
        Leitura.concluido.is_(False),
        Leitura.data >= datetime.now() - timedelta(days=2),
    ).first()

    if leitura_pendente:
        trecho = leitura_pendente.trecho
        id_leitura = leitura_pendente.id
    else:
        trecho = obter_trecho_do_dia()
        nova_leitura = Leitura(usuario_id=usuario.id, trecho=trecho, concluido=False)
        db.add(nova_leitura)
        db.commit()
        db.refresh(nova_leitura)
        id_leitura = nova_leitura.id

    caminho_audio = gerar_audio_versiculo(trecho, f"audio_{usuario.id}_{id_leitura}")

    try:
        requests.post(SENDER_URL, json={
            "telefone": usuario.telefone,
            "mensagem": f"Olá {usuario.nome}, seu versículo de hoje é:\n{trecho}",
            "audio": caminho_audio,
        })
    except Exception as e:
        print("Erro ao enviar mensagem via WhatsApp:", e)

    return jsonify({"mensagem": "Leitura enviada com sucesso", "trecho": trecho, "id_leitura": id_leitura}), 200

@app.post("/confirmar-leitura")
def confirmar_leitura():
    data = request.get_json() or {}
    id_leitura = data.get("id_leitura")

    db = SessionLocal()
    leitura = db.query(Leitura).filter_by(id=id_leitura).first()
    if not leitura:
        return jsonify({"erro": "Leitura não encontrada"}), 404

    leitura.concluido = True
    db.commit()

    return jsonify({"mensagem": "Leitura marcada como concluída"}), 200

@app.get("/usuarios")
def listar_usuarios():
    db = SessionLocal()
    usuarios = db.query(Usuario).all()
    resultado = [
        {
            "id": u.id,
            "nome": u.nome,
            "telefone": u.telefone,
            "email": u.email,
            "versao_biblia": u.versao_biblia,
            "plano_leitura": u.plano_leitura,
            "horario_envio": u.horario_envio,
        }
        for u in usuarios
    ]
    return jsonify(resultado)

# ---------------------------------------------------------------------------
# Inicialização do banco
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
