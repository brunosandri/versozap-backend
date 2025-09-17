from flask import Flask, jsonify, request
from flask_cors import CORS
from database import engine, SessionLocal
from models import Base, Usuario, Leitura
from apscheduler.schedulers.background import BackgroundScheduler
from gtts import gTTS
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash, check_password_hash
import jwt, os, re, requests, time
from dotenv import load_dotenv
from bible_service import biblia_service, obter_trecho_do_dia
from auth_service import auth_service
from database_manager import db_manager, initialize_database
from logging_system import versozap_logger, LogCategory, log_info, log_error, log_success

# ---------------------------------------------------------------------------
# Configurações básicas
# ---------------------------------------------------------------------------
load_dotenv()

# Timestamp de inicialização da aplicação
app_start_time = time.time()

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
                "http://localhost:5174",
                "http://localhost:5175",
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
        if origin and origin.startswith(("https://app.versozap.com.br", "http://localhost:517")):
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
            resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return resp

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

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
            # Usa as preferências do usuário para obter a leitura personalizada
            plano_leitura = usuario.plano_leitura or "cronologico"
            versao_biblia = usuario.versao_biblia or "ARC"
            
            # Obtém leitura do dia baseada nas preferências do usuário
            leitura_info = biblia_service.obter_leitura_do_dia(
                plano_leitura=plano_leitura,
                versao_biblia=versao_biblia
            )
            
            nova_leitura = Leitura(
                usuario_id=usuario.id, 
                trecho=leitura_info["referencia"], 
                concluido=False
            )
            db.add(nova_leitura)
            db.commit()
            db.refresh(nova_leitura)

            # Gera áudio com o texto da leitura
            caminho_audio = gerar_audio_versiculo(
                leitura_info["texto"], 
                f"audio_{usuario.id}_{nova_leitura.id}"
            )

            try:
                mensagem = f"🙏 Olá {usuario.nome}, sua leitura bíblica de hoje:\n\n{leitura_info['texto']}"
                requests.post(
                    SENDER_URL,
                    json={
                        "telefone": usuario.telefone,
                        "mensagem": mensagem,
                        "audio": caminho_audio,
                    },
                )
            except Exception as e:
                print(f"[Erro WhatsApp] {usuario.nome}: {e}")
    
    db.close()

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
        referencia = leitura_pendente.trecho
        id_leitura = leitura_pendente.id
        # Para leitura pendente, precisamos buscar o texto completo
        leitura_info = {
            "referencia": referencia,
            "texto": f"📖 {referencia}\n\nConsulte sua Bíblia para ler esta passagem."
        }
    else:
        # Usa as preferências do usuário
        plano_leitura = usuario.plano_leitura or "cronologico"
        versao_biblia = usuario.versao_biblia or "ARC"
        
        leitura_info = biblia_service.obter_leitura_do_dia(
            plano_leitura=plano_leitura,
            versao_biblia=versao_biblia
        )
        
        nova_leitura = Leitura(
            usuario_id=usuario.id, 
            trecho=leitura_info["referencia"], 
            concluido=False
        )
        db.add(nova_leitura)
        db.commit()
        db.refresh(nova_leitura)
        id_leitura = nova_leitura.id

    caminho_audio = gerar_audio_versiculo(
        leitura_info["texto"], 
        f"audio_{usuario.id}_{id_leitura}"
    )

    try:
        mensagem = f"🙏 Olá {usuario.nome}, sua leitura bíblica:\n\n{leitura_info['texto']}"
        requests.post(SENDER_URL, json={
            "telefone": usuario.telefone,
            "mensagem": mensagem,
            "audio": caminho_audio,
        })
    except Exception as e:
        print("Erro ao enviar mensagem via WhatsApp:", e)

    return jsonify({
        "mensagem": "Leitura enviada com sucesso", 
        "referencia": leitura_info["referencia"],
        "texto": leitura_info["texto"],
        "id_leitura": id_leitura
    }), 200

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
    db.close()
    return jsonify(resultado)

# ---------------------------------------------------------------------------
# Novas rotas para conteúdo bíblico
# ---------------------------------------------------------------------------

@app.get("/api/versoes-biblia")
def obter_versoes_biblia():
    """Retorna as versões da Bíblia disponíveis"""
    versoes = biblia_service.obter_versoes_disponiveis()
    return jsonify({"versoes": versoes})

@app.get("/api/planos-leitura") 
def obter_planos_leitura():
    """Retorna os planos de leitura disponíveis"""
    planos = biblia_service.obter_planos_disponiveis()
    return jsonify({"planos": planos})

@app.get("/api/leitura-hoje")
def obter_leitura_hoje():
    """Obtém a leitura bíblica do dia atual"""
    versao = request.args.get("versao", "ARC")
    plano = request.args.get("plano", "cronologico")
    
    # Valida a configuração
    validacao = biblia_service.validar_configuracao(versao, plano)
    if not validacao["versao_valida"] or not validacao["plano_valido"]:
        return jsonify({
            "erro": "Configuração inválida",
            "detalhes": validacao
        }), 400
    
    leitura = biblia_service.obter_leitura_do_dia(
        plano_leitura=plano,
        versao_biblia=versao
    )
    
    return jsonify({"leitura": leitura})

@app.get("/api/leitura-dia/<int:dia>")
def obter_leitura_dia_especifico(dia):
    """Obtém a leitura bíblica de um dia específico (1-365)"""
    if dia < 1 or dia > 365:
        return jsonify({"erro": "Dia deve estar entre 1 e 365"}), 400
    
    versao = request.args.get("versao", "ARC")
    plano = request.args.get("plano", "cronologico")
    
    leitura = biblia_service.obter_leitura_do_dia(
        dia_do_ano=dia,
        plano_leitura=plano,
        versao_biblia=versao
    )
    
    return jsonify({"leitura": leitura})

@app.post("/api/atualizar-preferencias")
def atualizar_preferencias_usuario():
    """Atualiza as preferências bíblicas do usuário"""
    data = request.get_json() or {}
    user_id = data.get("user_id")
    versao_biblia = data.get("versao_biblia")
    plano_leitura = data.get("plano_leitura")
    
    if not user_id:
        return jsonify({"erro": "ID do usuário é obrigatório"}), 400
    
    # Valida as preferências
    validacao = biblia_service.validar_configuracao(versao_biblia, plano_leitura)
    if not validacao["versao_valida"] or not validacao["plano_valido"]:
        return jsonify({
            "erro": "Preferências inválidas",
            "detalhes": validacao
        }), 400
    
    db = SessionLocal()
    usuario = db.query(Usuario).filter_by(id=user_id).first()
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    
    # Atualiza as preferências
    if versao_biblia:
        usuario.versao_biblia = versao_biblia
    if plano_leitura:
        usuario.plano_leitura = plano_leitura
    
    db.commit()
    db.close()
    
    return jsonify({
        "mensagem": "Preferências atualizadas com sucesso",
        "versao_biblia": usuario.versao_biblia,
        "plano_leitura": usuario.plano_leitura
    })

# ---------------------------------------------------------------------------
# Autenticação Social (Google e Facebook)
# ---------------------------------------------------------------------------

@app.get("/api/auth/urls")
def obter_urls_oauth():
    """Retorna URLs para iniciar autenticação OAuth"""
    urls = auth_service.get_oauth_urls()
    return jsonify({"urls": urls})

@app.post("/api/auth/google")
def auth_google():
    """Autentica usuário via token Google"""
    data = request.get_json() or {}
    token = data.get("token")
    
    if not token:
        return jsonify({"erro": "Token é obrigatório"}), 400
    
    # Verifica token com Google
    user_info = auth_service.verify_google_token(token)
    if not user_info:
        return jsonify({"erro": "Token Google inválido"}), 401
    
    # Procura ou cria usuário
    db = SessionLocal()
    usuario = db.query(Usuario).filter_by(email=user_info["email"]).first()
    
    if not usuario:
        # Cria novo usuário
        usuario = Usuario(
            nome=user_info["name"],
            email=user_info["email"],
            versao_biblia="ARC",
            plano_leitura="cronologico",
            horario_envio="08:00"
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    
    # Gera token JWT
    jwt_token = auth_service.generate_jwt_token(
        usuario.id, 
        usuario.email, 
        "google"
    )
    
    db.close()
    
    return jsonify({
        "token": jwt_token,
        "user": {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "provider": "google"
        }
    }), 200

@app.post("/api/auth/facebook")
def auth_facebook():
    """Autentica usuário via token Facebook"""
    data = request.get_json() or {}
    access_token = data.get("access_token")
    
    if not access_token:
        return jsonify({"erro": "Access token é obrigatório"}), 400
    
    # Verifica token com Facebook
    user_info = auth_service.verify_facebook_token(access_token)
    if not user_info:
        return jsonify({"erro": "Token Facebook inválido"}), 401
    
    # Procura ou cria usuário
    db = SessionLocal()
    usuario = db.query(Usuario).filter_by(email=user_info["email"]).first()
    
    if not usuario:
        # Cria novo usuário
        usuario = Usuario(
            nome=user_info["name"],
            email=user_info["email"],
            versao_biblia="ARC",
            plano_leitura="cronologico",
            horario_envio="08:00"
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    
    # Gera token JWT
    jwt_token = auth_service.generate_jwt_token(
        usuario.id, 
        usuario.email, 
        "facebook"
    )
    
    db.close()
    
    return jsonify({
        "token": jwt_token,
        "user": {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "provider": "facebook"
        }
    }), 200

@app.get("/api/auth/google/callback")
def google_callback():
    """Callback do Google OAuth (para fluxo de autorização)"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return f"<script>window.location.href='{frontend_url}/login?error={error}'</script>"
    
    if not code:
        return jsonify({"erro": "Código de autorização não fornecido"}), 400
    
    # Troca código por token
    user_info = auth_service.exchange_google_code(code)
    if not user_info:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return f"<script>window.location.href='{frontend_url}/login?error=auth_failed'</script>"
    
    # Processa usuário e redireciona para o frontend com token
    db = SessionLocal()
    usuario = db.query(Usuario).filter_by(email=user_info["email"]).first()
    
    if not usuario:
        usuario = Usuario(
            nome=user_info["name"],
            email=user_info["email"],
            versao_biblia="ARC",
            plano_leitura="cronologico",
            horario_envio="08:00"
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    
    jwt_token = auth_service.generate_jwt_token(
        usuario.id, 
        usuario.email, 
        "google"
    )
    
    db.close()
    
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    return f"<script>window.location.href='{frontend_url}/sucesso?token={jwt_token}'</script>"

@app.get("/api/auth/facebook/callback")
def facebook_callback():
    """Callback do Facebook OAuth (para fluxo de autorização)"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return f"<script>window.location.href='{frontend_url}/login?error={error}'</script>"
    
    if not code:
        return jsonify({"erro": "Código de autorização não fornecido"}), 400
    
    # Troca código por token
    user_info = auth_service.exchange_facebook_code(code)
    if not user_info:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return f"<script>window.location.href='{frontend_url}/login?error=auth_failed'</script>"
    
    # Processa usuário e redireciona para o frontend com token
    db = SessionLocal()
    usuario = db.query(Usuario).filter_by(email=user_info["email"]).first()
    
    if not usuario:
        usuario = Usuario(
            nome=user_info["name"],
            email=user_info["email"],
            versao_biblia="ARC",
            plano_leitura="cronologico",
            horario_envio="08:00"
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    
    jwt_token = auth_service.generate_jwt_token(
        usuario.id, 
        usuario.email, 
        "facebook"
    )
    
    db.close()
    
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    return f"<script>window.location.href='{frontend_url}/sucesso?token={jwt_token}'</script>"

@app.post("/api/auth/validate")
def validar_token():
    """Valida token JWT"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"erro": "Token não fornecido"}), 401
    
    token = auth_header.split(' ')[1]
    payload = auth_service.validate_jwt_token(token)
    
    if not payload:
        return jsonify({"erro": "Token inválido ou expirado"}), 401
    
    return jsonify({"valid": True, "user_id": payload["sub"], "email": payload["email"]})

@app.post("/api/user/update-profile")
def atualizar_perfil_usuario():
    """Atualiza perfil do usuário com telefone e preferências"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"erro": "Token não fornecido"}), 401

    token = auth_header.split(' ')[1]
    payload = auth_service.validate_jwt_token(token)

    if not payload:
        return jsonify({"erro": "Token inválido"}), 401

    data = request.get_json() or {}
    user_id = payload["sub"]

    db = SessionLocal()
    usuario = db.query(Usuario).filter_by(id=user_id).first()
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    # Atualiza campos se fornecidos
    if data.get("telefone"):
        usuario.telefone = data["telefone"]
    if data.get("versao_biblia"):
        usuario.versao_biblia = data["versao_biblia"]
    if data.get("plano_leitura"):
        usuario.plano_leitura = data["plano_leitura"]
    if data.get("horario_envio"):
        usuario.horario_envio = data["horario_envio"]

    db.commit()
    db.close()

    return jsonify({
        "mensagem": "Perfil atualizado com sucesso",
        "usuario": {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "telefone": usuario.telefone,
            "versao_biblia": usuario.versao_biblia,
            "plano_leitura": usuario.plano_leitura,
            "horario_envio": usuario.horario_envio
        }
    })

# ---------------------------------------------------------------------------
# Rotas de Administração (Logs e Database)
# ---------------------------------------------------------------------------

@app.get("/admin/logs")
def admin_get_logs():
    """Retorna logs do sistema para o painel admin"""
    try:
        limit = request.args.get('limit', 100, type=int)
        level = request.args.get('level')
        category = request.args.get('category')
        
        logs = versozap_logger.get_recent_logs(
            limit=min(limit, 500),  # Máximo 500 logs
            level=level,
            category=category
        )
        
        return jsonify({
            "logs": logs,
            "total": len(logs),
            "filters": {"level": level, "category": category, "limit": limit}
        })
        
    except Exception as e:
        log_error(LogCategory.SYSTEM, "Erro ao buscar logs", error=e)
        return jsonify({"erro": "Erro ao buscar logs"}), 500

@app.get("/admin/logs/stats")
def admin_get_log_stats():
    """Retorna estatísticas dos logs"""
    try:
        stats = versozap_logger.get_stats()
        if stats:
            return jsonify(stats)
        else:
            return jsonify({"erro": "Erro ao gerar estatísticas"}), 500
            
    except Exception as e:
        log_error(LogCategory.SYSTEM, "Erro ao gerar estatísticas de logs", error=e)
        return jsonify({"erro": "Erro ao gerar estatísticas"}), 500

@app.get("/admin/database/info")
def admin_get_database_info():
    """Retorna informações do banco de dados"""
    try:
        info = db_manager.get_database_info()
        return jsonify(info)
        
    except Exception as e:
        log_error(LogCategory.DATABASE, "Erro ao obter informações do banco", error=e)
        return jsonify({"erro": "Erro ao obter informações do banco"}), 500

@app.post("/admin/database/backup")
def admin_create_backup():
    """Cria backup do banco de dados"""
    try:
        backup_path = db_manager.backup_database()
        if backup_path:
            log_success(LogCategory.DATABASE, f"Backup criado: {backup_path}")
            return jsonify({
                "mensagem": "Backup criado com sucesso",
                "arquivo": backup_path,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"erro": "Falha ao criar backup"}), 500
            
    except Exception as e:
        log_error(LogCategory.DATABASE, "Erro ao criar backup", error=e)
        return jsonify({"erro": "Erro ao criar backup"}), 500

@app.post("/admin/database/cleanup")
def admin_cleanup_database():
    """Limpa dados antigos do banco"""
    try:
        days_old = request.json.get('days_old', 90)
        result = db_manager.cleanup_old_data(days_old)
        
        if result:
            log_success(LogCategory.DATABASE, f"Limpeza concluída: {result}")
            return jsonify({
                "mensagem": "Limpeza concluída",
                "resultado": result,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"erro": "Falha na limpeza"}), 500
            
    except Exception as e:
        log_error(LogCategory.DATABASE, "Erro na limpeza do banco", error=e)
        return jsonify({"erro": "Erro na limpeza"}), 500

@app.post("/admin/database/optimize")
def admin_optimize_database():
    """Otimiza o banco de dados"""
    try:
        success = db_manager.optimize_database()
        if success:
            log_success(LogCategory.DATABASE, "Banco de dados otimizado")
            return jsonify({
                "mensagem": "Banco de dados otimizado com sucesso",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"erro": "Falha na otimização"}), 500
            
    except Exception as e:
        log_error(LogCategory.DATABASE, "Erro na otimização do banco", error=e)
        return jsonify({"erro": "Erro na otimização"}), 500

@app.get("/admin/system/status")
def admin_get_system_status():
    """Retorna status geral do sistema"""
    try:
        # Status do banco
        db_info = db_manager.get_database_info()
        
        # Status do WhatsApp sender
        whatsapp_status = "unknown"
        try:
            response = requests.get(f"{SENDER_URL}/status", timeout=5)
            if response.status_code == 200:
                whatsapp_data = response.json()
                whatsapp_status = whatsapp_data.get("whatsappStatus", "unknown")
        except:
            whatsapp_status = "disconnected"
        
        # Estatísticas dos logs
        log_stats = versozap_logger.get_stats()
        
        return jsonify({
            "database": {
                "status": "connected",
                "tables": len(db_info.get("tables", [])),
                "total_users": db_info.get("usuarios_count", 0)
            },
            "whatsapp": {
                "status": whatsapp_status
            },
            "logs": log_stats,
            "uptime": {
                "seconds": time.time() - app_start_time if 'app_start_time' in globals() else 0
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        log_error(LogCategory.SYSTEM, "Erro ao obter status do sistema", error=e)
        return jsonify({"erro": "Erro ao obter status"}), 500

# ---------------------------------------------------------------------------
# Inicialização do banco e sistema
# ---------------------------------------------------------------------------

# Inicializa sistema de logs
log_info(LogCategory.SYSTEM, "Iniciando VersoZap Backend")

# Inicializa banco de dados com migrations
if not initialize_database():
    log_error(LogCategory.DATABASE, "Falha na inicialização do banco de dados")
    exit(1)

# Fallback para SQLAlchemy (compatibilidade)
Base.metadata.create_all(bind=engine)

log_success(LogCategory.SYSTEM, "VersoZap Backend inicializado com sucesso")

if __name__ == "__main__":
    try:
        port = int(os.getenv("PORT", 5000))
        debug_mode = os.getenv("FLASK_ENV", "development") == "development"
        
        log_info(LogCategory.SYSTEM, f"Iniciando servidor Flask na porta {port}")
        log_info(LogCategory.SYSTEM, f"Modo debug: {debug_mode}")
        
        app.run(
            debug=debug_mode, 
            port=port, 
            host='0.0.0.0'  # Permite acesso externo em produção
        )
    except KeyboardInterrupt:
        log_info(LogCategory.SYSTEM, "Servidor interrompido pelo usuário")
    except Exception as e:
        log_error(LogCategory.SYSTEM, "Erro fatal no servidor", error=e)
        raise
