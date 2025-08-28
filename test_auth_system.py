#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para o sistema de autenticação social do VersoZap
"""

import sys
import os
import requests
import json
from datetime import datetime

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth_service import auth_service

def test_auth_service_initialization():
    """Testa se o serviço de autenticação foi inicializado corretamente"""
    print("=== Testando Inicialização do AuthService ===")
    
    print(f"Google Client ID configurado: {'Sim' if auth_service.google_client_id else 'Não'}")
    print(f"Facebook App ID configurado: {'Sim' if auth_service.facebook_app_id else 'Não'}")
    print(f"JWT Secret configurado: {'Sim' if auth_service.jwt_secret else 'Não'}")
    print()

def test_jwt_token_generation():
    """Testa geração e validação de tokens JWT"""
    print("=== Testando Tokens JWT ===")
    
    # Gera token
    user_id = 123
    email = "teste@exemplo.com"
    provider = "google"
    
    token = auth_service.generate_jwt_token(user_id, email, provider)
    print(f"Token gerado: {token[:50]}...")
    
    # Valida token
    payload = auth_service.validate_jwt_token(token)
    
    if payload:
        print("Token válido!")
        print(f"User ID: {payload['sub']}")
        print(f"Email: {payload['email']}")
        print(f"Provider: {payload['provider']}")
        return True
    else:
        print("Erro: Token inválido")
        return False

def test_oauth_urls():
    """Testa geração de URLs OAuth"""
    print("\n=== Testando URLs OAuth ===")
    
    urls = auth_service.get_oauth_urls()
    
    print(f"URL Google: {urls.get('google', 'Não gerada')[:100]}...")
    print(f"URL Facebook: {urls.get('facebook', 'Não gerada')[:100]}...")
    
    return 'google' in urls and 'facebook' in urls

def test_invalid_tokens():
    """Testa validação de tokens inválidos"""
    print("\n=== Testando Tokens Inválidos ===")
    
    # Token inválido
    invalid_token = "token_completamente_invalido"
    result = auth_service.validate_jwt_token(invalid_token)
    
    if result is None:
        print("Token invalido rejeitado corretamente")
        return True
    else:
        print("Erro: Token invalido foi aceito")
        return False

def test_backend_endpoints():
    """Testa endpoints do backend (requer Flask rodando)"""
    print("\n=== Testando Endpoints do Backend ===")
    
    base_url = "http://localhost:5000"
    
    try:
        # Testa endpoint de URLs OAuth
        response = requests.get(f"{base_url}/api/auth/urls", timeout=5)
        if response.status_code == 200:
            print("Endpoint /api/auth/urls funcionando")
            urls = response.json()
            print(f"URLs retornadas: {list(urls.get('urls', {}).keys())}")
        else:
            print(f"Endpoint /api/auth/urls retornou {response.status_code}")
            return False
            
        # Testa endpoint de versões da Bíblia (para verificar se o server está rodando)
        response = requests.get(f"{base_url}/api/versoes-biblia", timeout=5)
        if response.status_code == 200:
            print("Backend esta respondendo corretamente")
            return True
        else:
            print(f"Backend retornou {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Backend nao esta rodando (ConnectionError)")
        print("   Para testar completamente, execute: python app.py")
        return False
    except requests.exceptions.Timeout:
        print("Backend nao respondeu em tempo habil")
        return False
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return False

def test_token_validation_endpoint():
    """Testa endpoint de validação de token"""
    print("\n=== Testando Validação de Token via API ===")
    
    base_url = "http://localhost:5000"
    
    try:
        # Gera um token válido
        token = auth_service.generate_jwt_token(123, "teste@exemplo.com", "test")
        
        # Testa validação
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(f"{base_url}/api/auth/validate", headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('valid'):
                print("Validacao de token via API funcionando")
                print(f"User ID retornado: {data.get('user_id')}")
                return True
            else:
                print("Token valido foi rejeitado pela API")
                return False
        else:
            print(f"API de validacao retornou {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Backend nao esta rodando")
        return False
    except Exception as e:
        print(f"Erro: {e}")
        return False

def generate_test_report():
    """Gera relatório final dos testes"""
    print("\n" + "="*60)
    print("RELATÓRIO FINAL - SISTEMA DE AUTENTICAÇÃO SOCIAL")
    print("="*60)
    
    tests = [
        ("Inicialização do AuthService", test_auth_service_initialization),
        ("Geração/Validação JWT", test_jwt_token_generation),
        ("URLs OAuth", test_oauth_urls),
        ("Tokens Inválidos", test_invalid_tokens),
        ("Endpoints Backend", test_backend_endpoints),
        ("Validação via API", test_token_validation_endpoint)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            print()
        except Exception as e:
            print(f"ERRO em {name}: {e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("RESUMO DOS TESTES:")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "PASSOU" if result else "FALHOU"
        print(f"{name:<30} {status}")
        if result:
            passed += 1
    
    print(f"\nRESULTADO: {passed}/{total} testes passaram")
    
    if passed == total:
        print("TODOS OS TESTES PASSARAM! Sistema de autenticacao social pronto.")
        return True
    else:
        print(f"{total - passed} teste(s) falharam. Verifique a configuracao.")
        return False

def main():
    """Executa todos os testes do sistema de autenticação"""
    print("INICIANDO TESTES DO SISTEMA DE AUTENTICACAO SOCIAL")
    print("="*60)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    return generate_test_report()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)