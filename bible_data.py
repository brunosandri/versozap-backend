# -*- coding: utf-8 -*-
"""
Sistema de conteúdo bíblico para VersoZap
Contém planos de leitura e versões da Bíblia
"""

# Plano de Leitura Anual (365 dias) - Cronológico
PLANO_CRONOLOGICO = {
    1: {"livro": "Gênesis", "capitulo": 1, "versiculo_inicio": 1, "versiculo_fim": 31},
    2: {"livro": "Gênesis", "capitulo": 2, "versiculo_inicio": 1, "versiculo_fim": 25},
    3: {"livro": "Gênesis", "capitulo": 3, "versiculo_inicio": 1, "versiculo_fim": 24},
    4: {"livro": "Gênesis", "capitulo": 4, "versiculo_inicio": 1, "versiculo_fim": 26},
    5: {"livro": "Gênesis", "capitulo": 5, "versiculo_inicio": 1, "versiculo_fim": 32},
    6: {"livro": "Gênesis", "capitulo": 6, "versiculo_inicio": 1, "versiculo_fim": 22},
    7: {"livro": "Gênesis", "capitulo": 7, "versiculo_inicio": 1, "versiculo_fim": 24},
    8: {"livro": "Gênesis", "capitulo": 8, "versiculo_inicio": 1, "versiculo_fim": 22},
    9: {"livro": "Gênesis", "capitulo": 9, "versiculo_inicio": 1, "versiculo_fim": 29},
    10: {"livro": "Gênesis", "capitulo": 10, "versiculo_inicio": 1, "versiculo_fim": 32},
    11: {"livro": "Gênesis", "capitulo": 11, "versiculo_inicio": 1, "versiculo_fim": 32},
    12: {"livro": "Gênesis", "capitulo": 12, "versiculo_inicio": 1, "versiculo_fim": 20},
    13: {"livro": "Gênesis", "capitulo": 13, "versiculo_inicio": 1, "versiculo_fim": 18},
    14: {"livro": "Gênesis", "capitulo": 14, "versiculo_inicio": 1, "versiculo_fim": 24},
    15: {"livro": "Gênesis", "capitulo": 15, "versiculo_inicio": 1, "versiculo_fim": 21},
    16: {"livro": "Gênesis", "capitulo": 16, "versiculo_inicio": 1, "versiculo_fim": 16},
    17: {"livro": "Gênesis", "capitulo": 17, "versiculo_inicio": 1, "versiculo_fim": 27},
    18: {"livro": "Gênesis", "capitulo": 18, "versiculo_inicio": 1, "versiculo_fim": 33},
    19: {"livro": "Gênesis", "capitulo": 19, "versiculo_inicio": 1, "versiculo_fim": 38},
    20: {"livro": "Gênesis", "capitulo": 20, "versiculo_inicio": 1, "versiculo_fim": 18},
    21: {"livro": "Gênesis", "capitulo": 21, "versiculo_inicio": 1, "versiculo_fim": 34},
    22: {"livro": "Gênesis", "capitulo": 22, "versiculo_inicio": 1, "versiculo_fim": 24},
    23: {"livro": "Gênesis", "capitulo": 23, "versiculo_inicio": 1, "versiculo_fim": 20},
    24: {"livro": "Gênesis", "capitulo": 24, "versiculo_inicio": 1, "versiculo_fim": 67},
    25: {"livro": "Gênesis", "capitulo": 25, "versiculo_inicio": 1, "versiculo_fim": 34},
    # Continuar até dia 365...
    # Para demonstração, vou adicionar alguns marcos importantes
    30: {"livro": "Gênesis", "capitulo": 30, "versiculo_inicio": 1, "versiculo_fim": 43},
    50: {"livro": "Êxodo", "capitulo": 1, "versiculo_inicio": 1, "versiculo_fim": 22},
    100: {"livro": "Levítico", "capitulo": 1, "versiculo_inicio": 1, "versiculo_fim": 17},
    150: {"livro": "Números", "capitulo": 1, "versiculo_inicio": 1, "versiculo_fim": 54},
    200: {"livro": "Deuteronômio", "capitulo": 1, "versiculo_inicio": 1, "versiculo_fim": 46},
    250: {"livro": "1 Samuel", "capitulo": 1, "versiculo_inicio": 1, "versiculo_fim": 28},
    300: {"livro": "Salmos", "capitulo": 1, "versiculo_inicio": 1, "versiculo_fim": 6},
    350: {"livro": "Mateus", "capitulo": 1, "versiculo_inicio": 1, "versiculo_fim": 25},
    365: {"livro": "Apocalipse", "capitulo": 22, "versiculo_inicio": 1, "versiculo_fim": 21}
}

# Plano de Leitura por Livros (365 dias)
PLANO_POR_LIVROS = {
    1: {"livro": "Mateus", "capitulo": 1, "versiculo_inicio": 1, "versiculo_fim": 25},
    2: {"livro": "Mateus", "capitulo": 2, "versiculo_inicio": 1, "versiculo_fim": 23},
    3: {"livro": "Mateus", "capitulo": 3, "versiculo_inicio": 1, "versiculo_fim": 17},
    4: {"livro": "Mateus", "capitulo": 4, "versiculo_inicio": 1, "versiculo_fim": 25},
    5: {"livro": "Mateus", "capitulo": 5, "versiculo_inicio": 1, "versiculo_fim": 48},
    # Continuar com todo o Novo Testamento primeiro
    # Depois Salmos, Provérbios e Antigo Testamento
    30: {"livro": "João", "capitulo": 1, "versiculo_inicio": 1, "versiculo_fim": 51},
    100: {"livro": "Romanos", "capitulo": 1, "versiculo_inicio": 1, "versiculo_fim": 32},
    200: {"livro": "Salmos", "capitulo": 1, "versiculo_inicio": 1, "versiculo_fim": 6},
    300: {"livro": "Gênesis", "capitulo": 1, "versiculo_inicio": 1, "versiculo_fim": 31},
    365: {"livro": "Malaquias", "capitulo": 4, "versiculo_inicio": 1, "versiculo_fim": 6}
}

# Versões da Bíblia - Versículos de exemplo para as principais passagens
VERSOES_BIBLIA = {
    "ARC": {
        "nome": "Almeida Revista e Corrigida",
        "versos": {
            "João 3:16": "Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito, para que todo aquele que nele crê não pereça, mas tenha a vida eterna.",
            "Salmos 23:1": "O Senhor é o meu pastor; nada me faltará.",
            "Romanos 8:28": "E sabemos que todas as coisas contribuem juntamente para o bem daqueles que amam a Deus, daqueles que são chamados segundo o seu propósito.",
            "Filipenses 4:13": "Posso todas as coisas em Cristo que me fortalece.",
            "Jeremias 29:11": "Porque eu bem sei os pensamentos que tenho a vosso respeito, diz o Senhor; pensamentos de paz, e não de mal, para vos dar o fim que esperais."
        }
    },
    "NVI": {
        "nome": "Nova Versão Internacional", 
        "versos": {
            "João 3:16": "Porque Deus tanto amou o mundo que deu o seu Filho Unigênito, para que todo o que nele crer não pereça, mas tenha a vida eterna.",
            "Salmos 23:1": "O Senhor é o meu pastor; nada me faltará.",
            "Romanos 8:28": "Sabemos que Deus age em todas as coisas para o bem daqueles que o amam, dos que foram chamados de acordo com o seu propósito.",
            "Filipenses 4:13": "Tudo posso naquele que me fortalece.",
            "Jeremias 29:11": "Porque eu bem sei os planos que tenho para vocês', diz o Senhor, 'planos de fazê-los prosperar e não de causar dano, planos de dar a vocês esperança e um futuro."
        }
    },
    "ACF": {
        "nome": "Almeida Corrigida Fiel",
        "versos": {
            "João 3:16": "Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito, para que todo aquele que nele crê não pereça, mas tenha a vida eterna.",
            "Salmos 23:1": "O SENHOR é o meu pastor, nada me faltará.",
            "Romanos 8:28": "E sabemos que todas as coisas contribuem juntamente para o bem daqueles que amam a Deus, daqueles que são chamados por seu decreto.",
            "Filipenses 4:13": "Posso todas as coisas em Cristo que me fortalece.",
            "Jeremias 29:11": "Porque eu bem sei os pensamentos que tenho a vosso respeito, diz o SENHOR; pensamentos de paz e não de mal, para vos dar o fim que esperais."
        }
    }
}

# Função auxiliar para gerar plano completo (placeholder para expansão futura)
def gerar_plano_completo(tipo_plano="cronologico"):
    """
    Gera plano de leitura completo de 365 dias
    TODO: Implementar geração automática baseada na estrutura bíblica
    """
    if tipo_plano == "cronologico":
        return PLANO_CRONOLOGICO
    elif tipo_plano == "livros":
        return PLANO_POR_LIVROS
    else:
        return PLANO_CRONOLOGICO

# Função para expandir automaticamente os planos (para implementação futura)
def expandir_plano_automatico():
    """
    TODO: Implementar lógica para preencher os 365 dias automaticamente
    baseado na estrutura completa da Bíblia
    """
    pass