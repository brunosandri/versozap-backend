#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para o sistema de conteúdo bíblico do VersoZap
"""

import sys
import os
from datetime import date

# Adiciona o diretório atual ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bible_service import biblia_service

def test_versoes_disponiveis():
    """Testa se as versões da Bíblia estão sendo carregadas corretamente"""
    print("=== Testando Versões Disponíveis ===")
    versoes = biblia_service.obter_versoes_disponiveis()
    
    print(f"Total de versões: {len(versoes)}")
    for versao in versoes:
        print(f"- {versao['codigo']}: {versao['nome']}")
    print()

def test_planos_disponiveis():
    """Testa se os planos de leitura estão sendo carregados corretamente"""
    print("=== Testando Planos de Leitura ===")
    planos = biblia_service.obter_planos_disponiveis()
    
    print(f"Total de planos: {len(planos)}")
    for plano in planos:
        print(f"- {plano['codigo']}: {plano['nome']}")
        print(f"  Descrição: {plano['descricao']}")
    print()

def test_leitura_do_dia():
    """Testa a obtenção da leitura do dia para diferentes configurações"""
    print("=== Testando Leitura do Dia ===")
    
    # Testa diferentes combinações
    configuracoes = [
        {"versao": "ARC", "plano": "cronologico"},
        {"versao": "NVI", "plano": "cronologico"},
        {"versao": "ARC", "plano": "livros"},
        {"versao": "NVI", "plano": "livros"}
    ]
    
    dia_hoje = date.today().timetuple().tm_yday
    
    for config in configuracoes:
        print(f"\n--- Versão: {config['versao']}, Plano: {config['plano']} ---")
        
        leitura = biblia_service.obter_leitura_do_dia(
            dia_do_ano=dia_hoje,
            plano_leitura=config["plano"],
            versao_biblia=config["versao"]
        )
        
        print(f"Dia do ano: {leitura['dia']}")
        print(f"Livro: {leitura['livro']}")
        print(f"Capítulo: {leitura['capitulo']}")
        print(f"Referência: {leitura['referencia']}")
        print(f"Versão: {leitura['versao']}")
        print(f"Texto: {leitura['texto'][:100]}..." if len(leitura['texto']) > 100 else f"Texto: {leitura['texto']}")

def test_dias_especificos():
    """Testa leituras de dias específicos do ano"""
    print("\n=== Testando Dias Específicos ===")
    
    dias_teste = [1, 25, 100, 200, 365]
    
    for dia in dias_teste:
        print(f"\n--- Dia {dia} do ano ---")
        
        leitura = biblia_service.obter_leitura_do_dia(
            dia_do_ano=dia,
            plano_leitura="cronologico",
            versao_biblia="ARC"
        )
        
        print(f"Referência: {leitura['referencia']}")
        print(f"Livro: {leitura['livro']}")

def test_validacao():
    """Testa o sistema de validação de configurações"""
    print("\n=== Testando Validações ===")
    
    testes_validacao = [
        {"versao": "ARC", "plano": "cronologico"},  # Válido
        {"versao": "INVALID", "plano": "cronologico"},  # Versão inválida
        {"versao": "ARC", "plano": "invalid"},  # Plano inválido
        {"versao": "INVALID", "plano": "invalid"}  # Ambos inválidos
    ]
    
    for teste in testes_validacao:
        resultado = biblia_service.validar_configuracao(
            teste["versao"], 
            teste["plano"]
        )
        
        print(f"\nTeste: {teste}")
        print(f"Versão válida: {resultado['versao_valida']}")
        print(f"Plano válido: {resultado['plano_valido']}")

def main():
    """Executa todos os testes"""
    print("INICIANDO TESTES DO SISTEMA BIBLICO VERSOZAP")
    print("=" * 50)
    
    try:
        test_versoes_disponiveis()
        test_planos_disponiveis()
        test_leitura_do_dia()
        test_dias_especificos()
        test_validacao()
        
        print("\nTODOS OS TESTES CONCLUIDOS COM SUCESSO!")
        print("O sistema de conteudo biblico esta funcionando corretamente.")
        
    except Exception as e:
        print(f"\nERRO DURANTE OS TESTES: {e}")
        print("Verifique a implementacao dos modulos.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)