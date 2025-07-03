from gtts import gTTS
import os
import requests
from flask import Flask, jsonify
from database import engine
from models import Base
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return "VersoZap está funcionando!"

from datetime import date

def gerar_audio_versiculo(texto, nome_arquivo):
    tts = gTTS(text=texto, lang='pt')
    caminho = f"audios/{nome_arquivo}.mp3"
    os.makedirs("audios", exist_ok=True)
    tts.save(caminho)
    return caminho

def enviar_leitura_diaria():
    db = SessionLocal()
    usuarios = db.query(Usuario).all()

    for usuario in usuarios:
        agora = datetime.now().strftime('%H:%M')
        if usuario.horario_envio == agora:
            # Simula o mesmo processo da rota /enviar-leitura
            trecho = obter_trecho_do_dia()
            nova_leitura = Leitura(
                usuario_id=usuario.id,
                trecho=trecho,
                concluido=False
            )
            db.add(nova_leitura)
            db.commit()
            db.refresh(nova_leitura)

            nome_arquivo_audio = f"audio_{usuario.id}_{nova_leitura.id}"
            caminho_audio = gerar_audio_versiculo(trecho, nome_arquivo_audio)

            # Envia pelo venom
            try:
                requests.post("http://localhost:3000/enviar", json={
                    "telefone": usuario.telefone,
                    "mensagem": f"Olá {usuario.nome}, seu versículo de hoje é:",
                    "audio": caminho_audio
                })
            except Exception as e:
                print(f"[Erro WhatsApp] {usuario.nome}: {e}")


# Simulação de trechos bíblicos por dia (exemplo simples)
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

def gerar_audio_versiculo(texto, nome_arquivo):
    tts = gTTS(text=texto, lang='pt')
    caminho = f"audios/{nome_arquivo}.mp3"
    os.makedirs("audios", exist_ok=True)
    tts.save(caminho)
    return caminho

@app.route("/")
def home():
    return "VersoZap está funcionando!"

@app.route("/versiculo")
def versiculo():
    return jsonify({"versiculo": "Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito."})

from flask import request
from database import SessionLocal
from models import Usuario

@app.route("/cadastrar", methods=["POST"])
def cadastrar_usuario():
    data = request.json  # Espera receber um JSON

    db = SessionLocal()

    # Verifica se o telefone já está cadastrado
    if db.query(Usuario).filter_by(telefone=data["telefone"]).first():
        return jsonify({"erro": "Usuário já cadastrado"}), 400

    # Cria novo usuário
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

from models import Leitura

from datetime import datetime, timedelta

@app.route("/enviar-leitura", methods=["POST"])
def enviar_leitura():
    data = request.json
    telefone = data.get("telefone")

    db = SessionLocal()
    usuario = db.query(Usuario).filter_by(telefone=telefone).first()

    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    leitura_pendente = (
        db.query(Leitura)
        .filter(
            Leitura.usuario_id == usuario.id,
            Leitura.concluido == False,
            Leitura.data >= datetime.now() - timedelta(days=2)
        )
        .first()
    )

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
        
        nome_arquivo_audio = f"audio_{usuario.id}_{id_leitura}"
        caminho_audio = gerar_audio_versiculo(trecho, nome_arquivo_audio)

    # Enviar mensagem via WhatsApp
    try:
        whatsapp_payload = {
            "telefone": usuario.telefone,
            "mensagem": f"Olá {usuario.nome}, seu versículo de hoje é:\n{trecho}",
            "audio": caminho_audio
        }

        requests.post("http://localhost:3000/enviar", json=whatsapp_payload)

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

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)

    scheduler = BackgroundScheduler()
    scheduler.add_job(enviar_leitura_diaria, 'interval', minutes=1)  # verifica a cada minuto
    scheduler.start()
    
    app.run(debug=True)

