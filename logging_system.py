# -*- coding: utf-8 -*-
"""
Sistema de logging estruturado para VersoZap
Fornece logging centralizado com diferentes níveis e categorias
"""

import os
import json
import logging
import traceback
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import SessionLocal

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    AUTH = "AUTH"
    MESSAGE = "MESSAGE"
    WHATSAPP = "WHATSAPP"
    BIBLE = "BIBLE"
    SYSTEM = "SYSTEM"
    USER = "USER"
    API = "API"
    DATABASE = "DATABASE"

class VersoZapLogger:
    
    def __init__(self):
        self.setup_file_logging()
        self.db_logging_enabled = True
        
    def setup_file_logging(self):
        """Configura logging para arquivo"""
        # Cria diretório de logs se não existir
        os.makedirs("logs", exist_ok=True)
        
        # Configuração do logger Python padrão
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/versozap.log', encoding='utf-8'),
                logging.StreamHandler()  # Console
            ]
        )
        
        self.logger = logging.getLogger('VersoZap')
    
    def log(self, 
            level: LogLevel, 
            category: LogCategory, 
            message: str, 
            details: Optional[Dict[str, Any]] = None,
            user_id: Optional[int] = None,
            error: Optional[Exception] = None):
        """
        Log principal do sistema
        
        Args:
            level: Nível do log (INFO, ERROR, etc.)
            category: Categoria do log (AUTH, MESSAGE, etc.)
            message: Mensagem principal
            details: Detalhes adicionais em formato dict
            user_id: ID do usuário relacionado (opcional)
            error: Exception capturada (opcional)
        """
        
        # Preparar dados do log
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "category": category.value,
            "message": message,
            "details": details or {},
            "user_id": user_id
        }
        
        # Adicionar informações de erro se fornecido
        if error:
            log_data["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            }
        
        # Log no arquivo/console
        log_message = f"[{category.value}] {message}"
        if details:
            log_message += f" | Details: {json.dumps(details, ensure_ascii=False)}"
        
        python_level = self._get_python_log_level(level)
        self.logger.log(python_level, log_message)
        
        # Log no banco de dados
        if self.db_logging_enabled:
            self._log_to_database(log_data)
    
    def _get_python_log_level(self, level: LogLevel) -> int:
        """Converte nosso LogLevel para nível do Python logging"""
        mapping = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.SUCCESS: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        return mapping.get(level, logging.INFO)
    
    def _log_to_database(self, log_data: Dict[str, Any]):
        """Salva log no banco de dados"""
        try:
            db = SessionLocal()
            
            # Converte details para JSON
            details_json = json.dumps(log_data["details"], ensure_ascii=False) if log_data["details"] else None
            
            # Usa SQL direto para evitar dependência de models
            db.execute(text("""
                INSERT INTO system_logs (timestamp, level, category, message, details, user_id)
                VALUES (:timestamp, :level, :category, :message, :details, :user_id)
            """), {
                "timestamp": log_data["timestamp"],
                "level": log_data["level"],
                "category": log_data["category"],
                "message": log_data["message"],
                "details": details_json,
                "user_id": log_data["user_id"]
            })
            
            db.commit()
            db.close()
            
        except Exception as e:
            # Se não conseguir logar no banco, pelo menos loga no arquivo
            self.logger.error(f"Erro ao salvar log no banco: {e}")
    
    # Métodos de conveniência para cada nível
    def debug(self, category: LogCategory, message: str, **kwargs):
        self.log(LogLevel.DEBUG, category, message, **kwargs)
    
    def info(self, category: LogCategory, message: str, **kwargs):
        self.log(LogLevel.INFO, category, message, **kwargs)
    
    def success(self, category: LogCategory, message: str, **kwargs):
        self.log(LogLevel.SUCCESS, category, message, **kwargs)
    
    def warning(self, category: LogCategory, message: str, **kwargs):
        self.log(LogLevel.WARNING, category, message, **kwargs)
    
    def error(self, category: LogCategory, message: str, **kwargs):
        self.log(LogLevel.ERROR, category, message, **kwargs)
    
    def critical(self, category: LogCategory, message: str, **kwargs):
        self.log(LogLevel.CRITICAL, category, message, **kwargs)
    
    # Métodos específicos por categoria
    def log_auth(self, message: str, user_id: Optional[int] = None, **kwargs):
        """Log específico para autenticação"""
        self.info(LogCategory.AUTH, message, user_id=user_id, **kwargs)
    
    def log_auth_error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log de erro de autenticação"""
        self.error(LogCategory.AUTH, message, error=error, **kwargs)
    
    def log_message_sent(self, telefone: str, user_id: int, trecho: str, **kwargs):
        """Log de mensagem enviada com sucesso"""
        details = {
            "telefone": telefone,
            "trecho": trecho,
            **kwargs.get("details", {})
        }
        self.success(LogCategory.MESSAGE, 
                    f"Mensagem enviada para {telefone}", 
                    details=details, 
                    user_id=user_id)
    
    def log_message_failed(self, telefone: str, user_id: int, error: Exception, **kwargs):
        """Log de falha no envio de mensagem"""
        details = {
            "telefone": telefone,
            **kwargs.get("details", {})
        }
        self.error(LogCategory.MESSAGE, 
                  f"Falha ao enviar mensagem para {telefone}", 
                  details=details, 
                  user_id=user_id, 
                  error=error)
    
    def log_whatsapp_status(self, status: str, **kwargs):
        """Log de mudança de status do WhatsApp"""
        self.info(LogCategory.WHATSAPP, 
                 f"Status do WhatsApp alterado: {status}", 
                 details=kwargs.get("details"))
    
    def log_whatsapp_error(self, message: str, error: Exception, **kwargs):
        """Log de erro do WhatsApp"""
        self.error(LogCategory.WHATSAPP, message, error=error, **kwargs)
    
    def log_user_action(self, user_id: int, action: str, **kwargs):
        """Log de ação do usuário"""
        self.info(LogCategory.USER, 
                 f"Usuário {user_id}: {action}", 
                 user_id=user_id, 
                 details=kwargs.get("details"))
    
    def log_bible_reading(self, user_id: int, trecho: str, **kwargs):
        """Log de leitura bíblica"""
        details = {
            "trecho": trecho,
            **kwargs.get("details", {})
        }
        self.info(LogCategory.BIBLE, 
                 f"Leitura carregada: {trecho}", 
                 user_id=user_id, 
                 details=details)
    
    def log_api_request(self, endpoint: str, method: str, user_id: Optional[int] = None, **kwargs):
        """Log de requisição da API"""
        details = {
            "endpoint": endpoint,
            "method": method,
            **kwargs.get("details", {})
        }
        self.info(LogCategory.API, 
                 f"{method} {endpoint}", 
                 user_id=user_id, 
                 details=details)
    
    def log_system_event(self, event: str, **kwargs):
        """Log de evento do sistema"""
        self.info(LogCategory.SYSTEM, event, **kwargs)
    
    def log_system_error(self, message: str, error: Exception, **kwargs):
        """Log de erro do sistema"""
        self.error(LogCategory.SYSTEM, message, error=error, **kwargs)
    
    def get_recent_logs(self, limit: int = 100, level: Optional[str] = None, category: Optional[str] = None):
        """Recupera logs recentes do banco de dados"""
        try:
            db = SessionLocal()
            
            query = "SELECT * FROM system_logs WHERE 1=1"
            params = {}
            
            if level:
                query += " AND level = :level"
                params["level"] = level
                
            if category:
                query += " AND category = :category"
                params["category"] = category
            
            query += " ORDER BY timestamp DESC LIMIT :limit"
            params["limit"] = limit
            
            result = db.execute(text(query), params)
            
            logs = []
            for row in result.fetchall():
                log_dict = {
                    "id": row[0],
                    "timestamp": row[1],
                    "level": row[2],
                    "category": row[3],
                    "message": row[4],
                    "details": json.loads(row[5]) if row[5] else None,
                    "user_id": row[6]
                }
                logs.append(log_dict)
            
            db.close()
            return logs
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar logs: {e}")
            return []
    
    def get_stats(self):
        """Retorna estatísticas dos logs"""
        try:
            db = SessionLocal()
            
            # Count por nível
            level_stats = {}
            for level in LogLevel:
                result = db.execute(text("""
                    SELECT COUNT(*) FROM system_logs 
                    WHERE level = :level 
                    AND timestamp >= datetime('now', '-24 hours')
                """), {"level": level.value})
                level_stats[level.value] = result.scalar()
            
            # Count por categoria
            category_stats = {}
            for category in LogCategory:
                result = db.execute(text("""
                    SELECT COUNT(*) FROM system_logs 
                    WHERE category = :category 
                    AND timestamp >= datetime('now', '-24 hours')
                """), {"category": category.value})
                category_stats[category.value] = result.scalar()
            
            # Total de logs
            result = db.execute(text("SELECT COUNT(*) FROM system_logs"))
            total_logs = result.scalar()
            
            db.close()
            
            return {
                "total_logs": total_logs,
                "last_24h_by_level": level_stats,
                "last_24h_by_category": category_stats,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar estatísticas: {e}")
            return None

# Instância global do logger
versozap_logger = VersoZapLogger()

# Funções de conveniência para importação fácil
def log_info(category: LogCategory, message: str, **kwargs):
    versozap_logger.info(category, message, **kwargs)

def log_error(category: LogCategory, message: str, error: Exception = None, **kwargs):
    versozap_logger.error(category, message, error=error, **kwargs)

def log_success(category: LogCategory, message: str, **kwargs):
    versozap_logger.success(category, message, **kwargs)

def log_warning(category: LogCategory, message: str, **kwargs):
    versozap_logger.warning(category, message, **kwargs)