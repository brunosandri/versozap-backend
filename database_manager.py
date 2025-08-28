# -*- coding: utf-8 -*-
"""
Gerenciador de banco de dados e sistema de migrations para VersoZap
"""

import os
import sqlite3
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from database import Base, engine, SessionLocal
from models import Usuario, Leitura
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    
    def __init__(self, database_url=None):
        self.database_url = database_url or os.getenv("DATABASE_URL", "sqlite:///versozap.db")
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def create_migrations_table(self):
        """Cria tabela de controle de migrations se não existir"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_name TEXT NOT NULL UNIQUE,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT
                )
            """))
            conn.commit()
    
    def get_executed_migrations(self):
        """Retorna lista de migrations já executadas"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT migration_name FROM migrations 
                WHERE success = TRUE 
                ORDER BY executed_at
            """))
            return [row[0] for row in result.fetchall()]
    
    def record_migration(self, migration_name, success=True, error_message=None):
        """Registra a execução de uma migration"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO migrations (migration_name, success, error_message) 
                VALUES (:name, :success, :error)
            """), {
                "name": migration_name,
                "success": success,
                "error": error_message
            })
            conn.commit()
    
    def execute_migration(self, migration_name, migration_sql):
        """Executa uma migration específica"""
        try:
            logger.info(f"Executando migration: {migration_name}")
            
            with self.engine.connect() as conn:
                # Executa as queries da migration
                for query in migration_sql.split(';'):
                    query = query.strip()
                    if query:
                        conn.execute(text(query))
                conn.commit()
            
            # Registra sucesso
            self.record_migration(migration_name, success=True)
            logger.info(f"✅ Migration {migration_name} executada com sucesso")
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Erro na migration {migration_name}: {error_msg}")
            self.record_migration(migration_name, success=False, error_message=error_msg)
            return False
    
    def run_migrations(self):
        """Executa todas as migrations pendentes"""
        self.create_migrations_table()
        executed_migrations = self.get_executed_migrations()
        
        # Lista de migrations na ordem de execução
        migrations = self.get_all_migrations()
        
        pending_migrations = [
            name for name in migrations.keys() 
            if name not in executed_migrations
        ]
        
        if not pending_migrations:
            logger.info("✅ Todas as migrations já foram executadas")
            return True
        
        logger.info(f"📦 Executando {len(pending_migrations)} migration(s) pendente(s)")
        
        success_count = 0
        for migration_name in pending_migrations:
            migration_sql = migrations[migration_name]
            if self.execute_migration(migration_name, migration_sql):
                success_count += 1
            else:
                logger.error(f"❌ Falha na migration {migration_name}. Parando execução.")
                break
        
        logger.info(f"✅ {success_count}/{len(pending_migrations)} migrations executadas com sucesso")
        return success_count == len(pending_migrations)
    
    def get_all_migrations(self):
        """Define todas as migrations do sistema"""
        return {
            "001_initial_schema": """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT,
                    telefone TEXT UNIQUE,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    versao_biblia TEXT DEFAULT 'ARC',
                    plano_leitura TEXT DEFAULT 'cronologico',
                    tipo_ordem TEXT DEFAULT 'normal',
                    horario_envio TEXT DEFAULT '08:00',
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trecho TEXT,
                    concluido BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                );
            """,
            
            "002_add_user_indexes": """
                CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
                CREATE INDEX IF NOT EXISTS idx_usuarios_telefone ON usuarios(telefone);
                CREATE INDEX IF NOT EXISTS idx_leituras_usuario_id ON leituras(usuario_id);
                CREATE INDEX IF NOT EXISTS idx_leituras_data ON leituras(data);
            """,
            
            "003_add_system_logs": """
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES usuarios (id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
                CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
                CREATE INDEX IF NOT EXISTS idx_system_logs_category ON system_logs(category);
            """,
            
            "004_add_user_preferences": """
                ALTER TABLE usuarios ADD COLUMN tema_preferido TEXT DEFAULT 'claro';
                ALTER TABLE usuarios ADD COLUMN notificacoes_ativas BOOLEAN DEFAULT TRUE;
                ALTER TABLE usuarios ADD COLUMN ultimo_acesso TIMESTAMP;
                ALTER TABLE usuarios ADD COLUMN status TEXT DEFAULT 'ativo';
            """,
            
            "005_add_reading_statistics": """
                CREATE TABLE IF NOT EXISTS reading_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    mes INTEGER NOT NULL,
                    ano INTEGER NOT NULL,
                    leituras_completadas INTEGER DEFAULT 0,
                    sequencia_dias INTEGER DEFAULT 0,
                    maior_sequencia INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
                    UNIQUE(usuario_id, mes, ano)
                );
                
                CREATE INDEX IF NOT EXISTS idx_reading_stats_usuario ON reading_stats(usuario_id);
                CREATE INDEX IF NOT EXISTS idx_reading_stats_period ON reading_stats(ano, mes);
            """,
            
            "006_add_message_queue": """
                CREATE TABLE IF NOT EXISTS message_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    telefone TEXT NOT NULL,
                    mensagem TEXT NOT NULL,
                    audio_path TEXT,
                    status TEXT DEFAULT 'pending',
                    tentativas INTEGER DEFAULT 0,
                    max_tentativas INTEGER DEFAULT 3,
                    agendado_para TIMESTAMP,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    enviado_em TIMESTAMP,
                    erro TEXT,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_message_queue_status ON message_queue(status);
                CREATE INDEX IF NOT EXISTS idx_message_queue_agendado ON message_queue(agendado_para);
            """
        }
    
    def backup_database(self, backup_path=None):
        """Cria backup do banco de dados"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_versozap_{timestamp}.db"
        
        try:
            # Para SQLite, copiamos o arquivo
            if self.database_url.startswith('sqlite'):
                db_file = self.database_url.replace('sqlite:///', '')
                import shutil
                shutil.copy2(db_file, backup_path)
                logger.info(f"✅ Backup criado: {backup_path}")
                return backup_path
            else:
                logger.warning("Backup automático disponível apenas para SQLite")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar backup: {e}")
            return None
    
    def get_database_info(self):
        """Retorna informações sobre o banco de dados"""
        inspector = inspect(self.engine)
        
        info = {
            "database_url": self.database_url,
            "tables": inspector.get_table_names(),
            "migrations_executed": len(self.get_executed_migrations()),
            "created_at": datetime.now().isoformat()
        }
        
        # Informações específicas das tabelas
        for table_name in info["tables"]:
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    info[f"{table_name}_count"] = count
            except Exception as e:
                info[f"{table_name}_count"] = f"Erro: {e}"
        
        return info
    
    def cleanup_old_data(self, days_old=90):
        """Remove dados antigos para manter o banco otimizado"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            with self.engine.connect() as conn:
                # Remove logs antigos
                result = conn.execute(text("""
                    DELETE FROM system_logs 
                    WHERE timestamp < :cutoff_date 
                    AND level != 'ERROR'
                """), {"cutoff_date": cutoff_date})
                
                deleted_logs = result.rowcount
                
                # Remove leituras muito antigas (mantém estatísticas)
                result = conn.execute(text("""
                    DELETE FROM leituras 
                    WHERE data < :cutoff_date 
                    AND concluido = TRUE
                """), {"cutoff_date": cutoff_date})
                
                deleted_readings = result.rowcount
                
                conn.commit()
            
            logger.info(f"🧹 Limpeza concluída: {deleted_logs} logs e {deleted_readings} leituras removidas")
            return {"logs_removed": deleted_logs, "readings_removed": deleted_readings}
            
        except Exception as e:
            logger.error(f"❌ Erro na limpeza: {e}")
            return None
    
    def optimize_database(self):
        """Otimiza o banco de dados (VACUUM para SQLite)"""
        try:
            if self.database_url.startswith('sqlite'):
                with self.engine.connect() as conn:
                    conn.execute(text("VACUUM"))
                    conn.commit()
                logger.info("✅ Banco de dados otimizado (VACUUM executado)")
                return True
            else:
                logger.warning("Otimização automática disponível apenas para SQLite")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro na otimização: {e}")
            return False

# Instância global
db_manager = DatabaseManager()

def initialize_database():
    """Função principal para inicializar o banco de dados"""
    logger.info("🗄️ Inicializando banco de dados...")
    
    # Executa migrations
    if db_manager.run_migrations():
        logger.info("✅ Banco de dados inicializado com sucesso")
        return True
    else:
        logger.error("❌ Falha na inicialização do banco de dados")
        return False

if __name__ == "__main__":
    # Executa inicialização quando chamado diretamente
    initialize_database()
    
    # Mostra informações do banco
    info = db_manager.get_database_info()
    print("\n📊 Informações do Banco de Dados:")
    for key, value in info.items():
        print(f"  {key}: {value}")