from flask import Flask, jsonify, request
from database import engine, SessionLocal
from models import Base, Usuario, Leitura
from apscheduler.schedulers.background import BackgroundScheduler
from gtts import gTTS
from datetime import datetime, timedelta, date
import os
import requests
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

SENDER_URL = os.getenv("SENDER_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)

@app.route("/")
def home():
    return "VersoZap está funcionando!"

# Simulação de trechos bíblicos por dia
TRECHOS_POR_DIA = {
    1: "Gênesis 1",
    2: "Gênesis 2",
    3: "Gênesis 3",
    4: "Mateus 1",
    5: "Salmos 1",
    # ... continue até 365
}

def obter_trecho_do_dia():
    dia_do_ano = date.today().timetuple().tm_yday
    return TRECHOS_POR_DIA.get(dia_do_ano, "Fim do plano de leitura")

def gerar_audio_versiculo(texto, nome_arquivo):
    tts = gTTS(text=texto, lang='pt')
    os.makedirs("audios", exist_ok=True)
    caminho = f"audios/{nome_arquivo}.mp3"
    tts.save(caminho)
    return caminho

def enviar_leitura_diaria():
    db = SessionLocal()
    usuarios = db.query(Usuario).all()

    for usuario in usuarios:
        agora = datetime.now().strftime('%H:%M')
        if usuario.horario_envio == agora:
            trecho = obter_trecho_do_dia()
            nova_leitura = Leitura(
                usuario_id=usuario.id,
                trecho=trecho,
                concluido=False
            )
            db.add(nova_leitura)
            db.commit()
            db.refresh(nova_leitura)

            caminho_audio = gerar_audio_versiculo(
                trecho, f"audio_{usuario.id}_{nova_leitura.id}"
            )

            try:
                requests.post(SENDER_URL, json={
                    "telefone": usuario.telefone,
                    "mensagem": f"Olá {usuario.nome}, seu versículo de hoje é:\n{trecho}",
                    "audio": caminho_audio
                })
            except Exception as e:
                print(f"[Erro WhatsApp] {usuario.nome}: {e}")

@app.route("/versiculo")
def versiculo():
    return jsonify({
        "versiculo": "Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito."
    })

@app.route("/cadastrar", methods=["POST"])
def cadastrar_usuario():
    data = request.json
    db = SessionLocal()

    if db.query(Usuario).filter_by(telefone=data["telefone"]).first():
        return jsonify({"erro": "Usuário já cadastrado"}), 400

    novo_usuario = Usuario(
        nome=data["nome"],
        telefone=data["telefone"],
        versao_biblia=data["versao_biblia"],
        plano_leitura=data["plano_leitura"],
        tipo_ordem=data["tipo_ordem"],
        horario_envio=data["horario_envio"]
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return jsonify({
        "mensagem": "Usuário cadastrado com sucesso",
        "id": novo_usuario.id
    }), 201

@app.route("/enviar-leitura", methods=["POST"])
def enviar_leitura():
    data = request.json
    telefone = data.get("telefone")

    db = SessionLocal()
    usuario = db.query(Usuario).filter_by(telefone=telefone).first()
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    leitura_pendente = db.query(Leitura).filter(
        Leitura.usuario_id == usuario.id,
        Leitura.concluido == False,
        Leitura.data >= datetime.now() - timedelta(days=2)
    ).first()

    if leitura_pendente:
        trecho = leitura_pendente.trecho
        id_leitura = leitura_pendente.id
    else:
        trecho = obter_trecho_do_dia()
        nova_leitura = Leitura(
            usuario_id=usuario.id,
            trecho=trecho,
            concluido=False
        )
        db.add(nova_leitura)
        db.commit()
        db.refresh(nova_leitura)
        id_leitura = nova_leitura.id

    caminho_audio = gerar_audio_versiculo(trecho, f"audio_{usuario.id}_{id_leitura}")

    try:
        requests.post(SENDER_URL, json={
            "telefone": usuario.telefone,
            "mensagem": f"Olá {usuario.nome}, seu versículo de hoje é:\n{trecho}",
            "audio": caminho_audio
        })
    except Exception as e:
        print("Erro ao enviar mensagem via WhatsApp:", e)

    return jsonify({
        "mensagem": "Leitura enviada com sucesso",
        "trecho": trecho,
        "id_leitura": id_leitura
    }), 200

@app.route("/confirmar-leitura", methods=["POST"])
def confirmar_leitura():
    data = request.json
    id_leitura = data.get("id_leitura")

    db = SessionLocal()
    leitura = db.query(Leitura).filter_by(id=id_leitura).first()

    if not leitura:
        return jsonify({"erro": "Leitura não encontrada"}), 404

    leitura.concluido = True
    db.commit()

    return jsonify({"mensagem": "Leitura marcada como concluída"}), 200

# Inicialização
Base.metadata.create_all(bind=engine)

scheduler = BackgroundScheduler()
scheduler.add_job(enviar_leitura_diaria, 'interval', minutes=1)
scheduler.start()
