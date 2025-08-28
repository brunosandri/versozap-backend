# -*- coding: utf-8 -*-
"""
Serviço de gerenciamento de conteúdo bíblico para VersoZap
Fornece funcionalidades para obter leituras diárias, versões e planos
"""

from datetime import date
from bible_data import VERSOES_BIBLIA, gerar_plano_completo
import requests
import json
import os

class BibliaService:
    
    def __init__(self):
        self.versoes_disponiveis = VERSOES_BIBLIA
        
    def obter_leitura_do_dia(self, dia_do_ano=None, plano_leitura="cronologico", versao_biblia="ARC"):
        """
        Obtém a leitura bíblica do dia especificado
        
        Args:
            dia_do_ano (int): Dia do ano (1-365). Se None, usa dia atual
            plano_leitura (str): Tipo de plano ("cronologico" ou "livros")
            versao_biblia (str): Versão da Bíblia ("ARC", "NVI", "ACF")
            
        Returns:
            dict: Informações da leitura do dia
        """
        if dia_do_ano is None:
            dia_do_ano = date.today().timetuple().tm_yday
            
        # Ajusta para não exceder 365 dias
        dia_do_ano = ((dia_do_ano - 1) % 365) + 1
        
        plano = gerar_plano_completo(plano_leitura)
        
        if dia_do_ano not in plano:
            # Se o dia não estiver mapeado, usa o último dia disponível
            ultimo_dia = max(plano.keys())
            leitura_info = plano[ultimo_dia]
            texto_final = "Parabéns! Você completou o plano de leitura anual. Reinicie ou escolha um novo plano."
        else:
            leitura_info = plano[dia_do_ano]
            texto_final = self._formatar_texto_leitura(leitura_info, versao_biblia)
            
        return {
            "dia": dia_do_ano,
            "livro": leitura_info["livro"],
            "capitulo": leitura_info["capitulo"],
            "versiculo_inicio": leitura_info.get("versiculo_inicio", 1),
            "versiculo_fim": leitura_info.get("versiculo_fim", 1),
            "referencia": self._formatar_referencia(leitura_info),
            "texto": texto_final,
            "versao": versao_biblia,
            "plano": plano_leitura
        }
    
    def _formatar_referencia(self, leitura_info):
        """Formata a referência bíblica (ex: João 3:16-18)"""
        livro = leitura_info["livro"]
        capitulo = leitura_info["capitulo"]
        v_inicio = leitura_info.get("versiculo_inicio", 1)
        v_fim = leitura_info.get("versiculo_fim", 1)
        
        if v_inicio == v_fim:
            return f"{livro} {capitulo}:{v_inicio}"
        else:
            return f"{livro} {capitulo}:{v_inicio}-{v_fim}"
    
    def _formatar_texto_leitura(self, leitura_info, versao_biblia):
        """
        Formata o texto da leitura bíblica
        Por enquanto retorna uma mensagem padrão, mas pode ser expandido
        para incluir o texto completo da passagem
        """
        referencia = self._formatar_referencia(leitura_info)
        
        # Verifica se temos o texto específico na versão escolhida
        versao_data = self.versoes_disponiveis.get(versao_biblia, self.versoes_disponiveis["ARC"])
        
        # Se tivermos o versículo específico, usa ele
        if referencia in versao_data["versos"]:
            texto = versao_data["versos"][referencia]
            return f'"{texto}"\n\n📖 {referencia} - {versao_data["nome"]}'
        
        # Senão, retorna instrução de leitura
        return f"📖 Leitura de hoje: {referencia}\n\n" + \
               f"Versão: {versao_data['nome']}\n\n" + \
               "Leia esta passagem em sua Bíblia e reflita sobre a mensagem de Deus para sua vida hoje."
    
    def obter_versoes_disponiveis(self):
        """Retorna lista das versões da Bíblia disponíveis"""
        return [
            {
                "codigo": codigo,
                "nome": info["nome"]
            }
            for codigo, info in self.versoes_disponiveis.items()
        ]
    
    def obter_planos_disponiveis(self):
        """Retorna lista dos planos de leitura disponíveis"""
        return [
            {
                "codigo": "cronologico",
                "nome": "Cronológico",
                "descricao": "Leitura da Bíblia em ordem cronológica dos eventos"
            },
            {
                "codigo": "livros", 
                "nome": "Por Livros",
                "descricao": "Leitura por ordem dos livros bíblicos (NT primeiro)"
            }
        ]
    
    def validar_configuracao(self, versao_biblia, plano_leitura):
        """Valida se a configuração escolhida pelo usuário é válida"""
        versoes_validas = list(self.versoes_disponiveis.keys())
        planos_validos = ["cronologico", "livros"]
        
        return {
            "versao_valida": versao_biblia in versoes_validas,
            "plano_valido": plano_leitura in planos_validos,
            "versoes_disponiveis": versoes_validas,
            "planos_disponiveis": planos_validos
        }

# Instância global do serviço
biblia_service = BibliaService()

# Funções auxiliares para compatibilidade com código existente
def obter_trecho_do_dia(plano_leitura="cronologico", versao_biblia="ARC"):
    """Função de compatibilidade com o código existente"""
    leitura = biblia_service.obter_leitura_do_dia(
        plano_leitura=plano_leitura, 
        versao_biblia=versao_biblia
    )
    return leitura["texto"]

def obter_leitura_personalizada(usuario_id, dia_do_ano=None):
    """
    Obtém leitura personalizada baseada nas preferências do usuário
    TODO: Integrar com o banco de dados para buscar preferências do usuário
    """
    # Por enquanto usa configuração padrão
    return biblia_service.obter_leitura_do_dia(dia_do_ano)