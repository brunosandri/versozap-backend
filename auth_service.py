# -*- coding: utf-8 -*-
"""
Serviço de autenticação social para VersoZap
Integração com Google OAuth2 e Facebook Login
"""

import os
import requests
import jwt
from datetime import datetime, timedelta
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from dotenv import load_dotenv

load_dotenv()

class AuthService:
    
    def __init__(self):
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.facebook_app_id = os.getenv("FACEBOOK_APP_ID")
        self.facebook_app_secret = os.getenv("FACEBOOK_APP_SECRET")
        self.jwt_secret = os.getenv("SECRET_KEY", "versozap-dev")
        
    def verify_google_token(self, token):
        """
        Verifica token do Google OAuth e retorna informações do usuário
        
        Args:
            token (str): Token ID do Google
            
        Returns:
            dict: Informações do usuário ou None se inválido
        """
        try:
            # Verifica o token com o Google
            idinfo = id_token.verify_oauth2_token(
                token, 
                google_requests.Request(), 
                self.google_client_id
            )
            
            # Verifica se o token é válido
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Token inválido')
            
            return {
                'id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo.get('name', ''),
                'picture': idinfo.get('picture', ''),
                'email_verified': idinfo.get('email_verified', False),
                'provider': 'google'
            }
            
        except ValueError as e:
            print(f"Erro ao verificar token Google: {e}")
            return None
        except Exception as e:
            print(f"Erro inesperado na verificação Google: {e}")
            return None
    
    def verify_facebook_token(self, access_token):
        """
        Verifica token do Facebook e retorna informações do usuário
        
        Args:
            access_token (str): Access token do Facebook
            
        Returns:
            dict: Informações do usuário ou None se inválido
        """
        try:
            # Primeiro, verifica se o token é válido
            debug_url = f"https://graph.facebook.com/debug_token"
            debug_params = {
                'input_token': access_token,
                'access_token': f"{self.facebook_app_id}|{self.facebook_app_secret}"
            }
            
            debug_response = requests.get(debug_url, params=debug_params)
            debug_data = debug_response.json()
            
            if not debug_data.get('data', {}).get('is_valid', False):
                return None
            
            # Se válido, busca informações do usuário
            user_url = "https://graph.facebook.com/me"
            user_params = {
                'access_token': access_token,
                'fields': 'id,name,email,picture'
            }
            
            user_response = requests.get(user_url, params=user_params)
            user_data = user_response.json()
            
            if 'error' in user_data:
                return None
                
            return {
                'id': user_data['id'],
                'email': user_data.get('email', ''),
                'name': user_data.get('name', ''),
                'picture': user_data.get('picture', {}).get('data', {}).get('url', ''),
                'email_verified': True,  # Facebook emails são verificados por padrão
                'provider': 'facebook'
            }
            
        except Exception as e:
            print(f"Erro ao verificar token Facebook: {e}")
            return None
    
    def generate_jwt_token(self, user_id, email, provider='email'):
        """
        Gera token JWT para autenticação
        
        Args:
            user_id (int): ID do usuário no banco
            email (str): Email do usuário
            provider (str): Provedor de autenticação
            
        Returns:
            str: Token JWT
        """
        payload = {
            'sub': user_id,
            'email': email,
            'provider': provider,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=7)
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def validate_jwt_token(self, token):
        """
        Valida token JWT
        
        Args:
            token (str): Token JWT
            
        Returns:
            dict: Payload do token ou None se inválido
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_oauth_urls(self):
        """
        Retorna URLs para iniciar autenticação OAuth
        
        Returns:
            dict: URLs de autenticação
        """
        base_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        backend_url = os.getenv("BACKEND_URL", "http://localhost:5000")
        
        google_url = (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"client_id={self.google_client_id}&"
            f"redirect_uri={backend_url}/api/auth/google/callback&"
            f"scope=openid email profile&"
            f"response_type=code&"
            f"access_type=offline"
        )
        
        facebook_url = (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={self.facebook_app_id}&"
            f"redirect_uri={backend_url}/api/auth/facebook/callback&"
            f"scope=email&"
            f"response_type=code"
        )
        
        return {
            'google': google_url,
            'facebook': facebook_url
        }
    
    def exchange_google_code(self, code):
        """
        Troca código de autorização por token de acesso (Google)
        
        Args:
            code (str): Código de autorização
            
        Returns:
            dict: Informações do usuário ou None
        """
        try:
            backend_url = os.getenv("BACKEND_URL", "http://localhost:5000")
            
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                'client_id': self.google_client_id,
                'client_secret': os.getenv("GOOGLE_CLIENT_SECRET"),
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': f"{backend_url}/api/auth/google/callback"
            }
            
            response = requests.post(token_url, data=token_data)
            tokens = response.json()
            
            if 'id_token' in tokens:
                return self.verify_google_token(tokens['id_token'])
                
            return None
            
        except Exception as e:
            print(f"Erro ao trocar código Google: {e}")
            return None
    
    def exchange_facebook_code(self, code):
        """
        Troca código de autorização por token de acesso (Facebook)
        
        Args:
            code (str): Código de autorização
            
        Returns:
            dict: Informações do usuário ou None
        """
        try:
            backend_url = os.getenv("BACKEND_URL", "http://localhost:5000")
            
            token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
            token_params = {
                'client_id': self.facebook_app_id,
                'client_secret': self.facebook_app_secret,
                'code': code,
                'redirect_uri': f"{backend_url}/api/auth/facebook/callback"
            }
            
            response = requests.get(token_url, params=token_params)
            tokens = response.json()
            
            if 'access_token' in tokens:
                return self.verify_facebook_token(tokens['access_token'])
                
            return None
            
        except Exception as e:
            print(f"Erro ao trocar código Facebook: {e}")
            return None

# Instância global do serviço
auth_service = AuthService()