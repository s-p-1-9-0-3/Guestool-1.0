"""
Funciones de procesamiento de datos para Rentabileitor PRO
"""
from difflib import SequenceMatcher


def fuzzy_match(nombre_app, lista_excel, threshold=0.6):
    """
    Busca coincidencias fuzzy en la lista de alojamientos.
    Retorna lista de (nombre_excel, score) ordenada por score descendente.
    """
    matches = []
    nombre_app_lower = nombre_app.lower()
    
    for nombre_excel in lista_excel:
        nombre_excel_lower = nombre_excel.lower()
        # Calcular similitud
        ratio = SequenceMatcher(None, nombre_app_lower, nombre_excel_lower).ratio()
        if ratio >= threshold:
            matches.append((nombre_excel, ratio))
    
    # Ordenar por score descendente
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


def filtrar_apartamentos_por_empresa(apartamentos_app, lista_excel_en_excels):
    """
    Filtra lista de apartamentos en excels para que coincidan con los de la empresa.
    Retorna lista filtrada si hay coincidencias, sino lista original.
    """
    lista_excel_de_empresa = sorted(list(apartamentos_app.keys()))
    lista_excel_filtrada = []
    
    for apt_repo in lista_excel_de_empresa:
        for apt_excel in lista_excel_en_excels:
            ratio = SequenceMatcher(None, apt_repo.lower(), apt_excel.lower()).ratio()
            if ratio >= 0.5:  # threshold bajo para encontrar variaciones
                if apt_excel not in lista_excel_filtrada:
                    lista_excel_filtrada.append(apt_excel)
    
    # Si no encuentra coincidencias, usar solo la lista de la empresa
    return sorted(lista_excel_filtrada) if lista_excel_filtrada else lista_excel_de_empresa
