# agent/tools.py — Herramientas del agente Phonelab Store
# Generado por AgentKit
# Integración de búsqueda de vuelos (Kiwi + Skyscanner)

import os
import yaml
import logging
import httpx
from datetime import datetime

logger = logging.getLogger("agentkit")


def cargar_info_negocio() -> dict:
    """Carga la información del negocio desde business.yaml."""
    try:
        with open("config/business.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("config/business.yaml no encontrado")
        return {}


def obtener_horario() -> dict:
    """Retorna el horario de atención del negocio."""
    info = cargar_info_negocio()
    return {
        "horario": info.get("negocio", {}).get("horario", "No disponible"),
        "esta_abierto": True,
    }


def buscar_en_knowledge(consulta: str) -> str:
    """
    Busca información relevante en los archivos de /knowledge.
    Retorna el contenido más relevante encontrado.
    """
    resultados = []
    knowledge_dir = "knowledge"

    if not os.path.exists(knowledge_dir):
        return "No hay archivos de conocimiento disponibles."

    for archivo in os.listdir(knowledge_dir):
        ruta = os.path.join(knowledge_dir, archivo)
        if archivo.startswith(".") or not os.path.isfile(ruta):
            continue
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
                if consulta.lower() in contenido.lower():
                    resultados.append(f"[{archivo}]: {contenido[:500]}")
        except (UnicodeDecodeError, IOError):
            continue

    if resultados:
        return "\n---\n".join(resultados)
    return "No encontré información específica sobre eso en mis archivos."


# ════════════════════════════════════════════════════════════════════════════
# APIs DE BÚSQUEDA DE VUELOS — Kiwi.com + Skyscanner
# ════════════════════════════════════════════════════════════════════════════

def buscar_vuelos_kiwi(origen: str, destino: str, fecha_salida: str, fecha_retorno: str = None) -> str:
    """
    Busca vuelos usando Kiwi.com API (o simula si no hay API key).

    Args:
        origen: Código IATA (ej: ALC, MAD)
        destino: Código IATA (ej: ORN, CDG)
        fecha_salida: Formato YYYY-MM-DD
        fecha_retorno: Opcional, formato YYYY-MM-DD

    Returns:
        String con los vuelos encontrados formateado para el usuario
    """
    api_key = os.getenv("KIWI_API_KEY", "")

    # Si no hay API key, usar datos simulados para demostración
    if not api_key:
        logger.info("KIWI_API_KEY no configurada - usando datos simulados")
        return generar_vuelos_simulados_kiwi(origen.upper(), destino.upper(), fecha_salida)

    try:
        params = {
            "fly_from": origen.upper(),
            "fly_to": destino.upper(),
            "date_from": fecha_salida,
            "date_to": fecha_salida,
            "apikey": api_key,
            "limit": 5,
            "sort": "price",
            "asc": 1,
        }

        if fecha_retorno:
            params["return_from"] = fecha_retorno
            params["return_to"] = fecha_retorno

        response = httpx.get(
            "https://tequila-api.kiwi.com/v2/search",
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"Error Kiwi API: {response.status_code}")
            return generar_vuelos_simulados_kiwi(origen.upper(), destino.upper(), fecha_salida)

        data = response.json()
        vuelos = data.get("data", [])

        if not vuelos:
            return generar_vuelos_simulados_kiwi(origen.upper(), destino.upper(), fecha_salida)

        resultado = f"🛫 **Vuelos de {origen} a {destino}** (ordenados por precio - KIWI.COM):\n\n"
        for i, vuelo in enumerate(vuelos, 1):
            precio = vuelo.get("price", "N/A")
            aerolínea = vuelo.get("airlines", ["Unknown"])[0]
            duracion = vuelo.get("duration", {})
            horas = duracion.get("hours", 0)
            minutos = duracion.get("minutes", 0)

            resultado += f"{i}. **${precio}** - {aerolínea}\n"
            resultado += f"   Duración: {horas}h {minutos}m\n"

        return resultado

    except Exception as e:
        logger.error(f"Error en búsqueda Kiwi: {e}")
        return generar_vuelos_simulados_kiwi(origen.upper(), destino.upper(), fecha_salida)


def generar_vuelos_simulados_kiwi(origen: str, destino: str, fecha: str) -> str:
    """Genera datos de vuelos simulados para demostración."""
    vuelos_demo = {
        ("ALC", "ORN"): [
            ("47€", "Vueling", "1h 15m"),
            ("52€", "Air Algérie", "1h 20m"),
            ("65€", "Royal Air Maroc", "2h 45m (escala)"),
            ("78€", "Iberia", "2h 30m (escala)"),
            ("89€", "Air France", "3h 15m (escala)"),
        ],
        ("MAD", "CDG"): [
            ("35€", "Vueling", "2h 05m"),
            ("42€", "Air France", "2h 15m"),
            ("58€", "Iberia", "2h 20m"),
        ]
    }

    clave = (origen, destino)
    vuelos = vuelos_demo.get(clave, [
        ("49€", "Vueling", "1h 30m"),
        ("67€", "Otra Aerolínea", "2h 00m"),
    ])

    resultado = f"✈️ **Vuelos de {origen} a {destino}** ({fecha}) - KIWI.COM\n"
    resultado += "_(Datos simulados - Obtén tus propias API keys para datos reales)_\n\n"

    for i, (precio, aerolinea, duracion) in enumerate(vuelos, 1):
        resultado += f"{i}. **{precio}** - {aerolinea}\n   Duración: {duracion}\n"

    return resultado


def buscar_vuelos_skyscanner(origen: str, destino: str, fecha_salida: str) -> str:
    """
    Busca vuelos usando Skyscanner API (o simula si no hay API key).

    Args:
        origen: Código IATA (ej: ALC)
        destino: Código IATA (ej: ORN)
        fecha_salida: Formato YYYY-MM-DD

    Returns:
        String con los vuelos encontrados formateado para el usuario
    """
    api_key = os.getenv("SKYSCANNER_API_KEY", "")

    # Si no hay API key, usar datos simulados para demostración
    if not api_key:
        logger.info("SKYSCANNER_API_KEY no configurada - usando datos simulados")
        return generar_vuelos_simulados_skyscanner(origen.upper(), destino.upper(), fecha_salida)

    try:
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "skyscanner-api.p.rapidapi.com"
        }

        params = {
            "adults": "1",
            "departure_date": fecha_salida,
            "origin": origen.upper(),
            "destination": destino.upper(),
            "currency": "USD",
        }

        response = httpx.get(
            "https://skyscanner-api.p.rapidapi.com/v1/flights/search",
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"Error Skyscanner API: {response.status_code}")
            return generar_vuelos_simulados_skyscanner(origen.upper(), destino.upper(), fecha_salida)

        data = response.json()
        itinerarios = data.get("itineraries", [])

        if not itinerarios:
            return generar_vuelos_simulados_skyscanner(origen.upper(), destino.upper(), fecha_salida)

        resultado = f"✈️ **Resultados Skyscanner** ({origen} → {destino}, {fecha_salida}):\n\n"
        for i, item in enumerate(itinerarios[:3], 1):
            precio = item.get("price", {}).get("total", "N/A")
            resultado += f"{i}. Precio: **{precio}** USD\n"

        return resultado

    except Exception as e:
        logger.error(f"Error en búsqueda Skyscanner: {e}")
        return generar_vuelos_simulados_skyscanner(origen.upper(), destino.upper(), fecha_salida)


def generar_vuelos_simulados_skyscanner(origen: str, destino: str, fecha: str) -> str:
    """Genera datos de vuelos simulados para demostración."""
    vuelos_demo = {
        ("ALC", "ORN"): [
            "$55 USD",
            "$62 USD",
            "$78 USD",
        ],
        ("MAD", "CDG"): [
            "$48 USD",
            "$55 USD",
            "$72 USD",
        ]
    }

    clave = (origen, destino)
    precios = vuelos_demo.get(clave, ["$52 USD", "$68 USD", "$85 USD"])

    resultado = f"🔍 **Skyscanner Results** ({origen} → {destino}, {fecha})\n"
    resultado += "_(Demo mode - Get your API key for real-time prices)_\n\n"

    for i, precio in enumerate(precios, 1):
        resultado += f"{i}. {precio}\n"

    return resultado


def buscar_vuelos(origen: str, destino: str, fecha: str) -> str:
    """
    Busca vuelos usando ambas APIs (Kiwi como principal, Skyscanner como alternativa).

    Args:
        origen: Ciudad o código IATA (ej: "Alicante" o "ALC")
        destino: Ciudad o código IATA (ej: "Oran" o "ORN")
        fecha: Fecha en formato YYYY-MM-DD o descripción (ej: "mañana", "20 de mayo")

    Returns:
        Resultado combinado de ambas APIs
    """
    # Mapeo simple de ciudades a códigos IATA
    ciudades = {
        "alicante": "ALC", "alicante ": "ALC",
        "oran": "ORN", "oran ": "ORN",
        "madrid": "MAD", "barcelona": "BCN", "sevilla": "SVQ",
        "paris": "CDG", "london": "LHR", "berlin": "TXL",
    }

    origen_iata = ciudades.get(origen.lower().strip(), origen.upper())
    destino_iata = ciudades.get(destino.lower().strip(), destino.upper())

    # Procesar fecha (si es "20 de mayo" → convertir a 2026-05-20)
    try:
        if len(fecha) == 10 and fecha[4] == "-":
            fecha_str = fecha
        else:
            # Intenta parsear "20 de mayo" → 2026-05-20
            meses = {
                "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
                "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
                "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
            }

            # Busca patrón "DD de NOMBREMES"
            partes = fecha.lower().split()
            if len(partes) >= 3 and partes[1] == "de":
                dia = int(partes[0])
                mes_nombre = partes[2].strip()
                mes = meses.get(mes_nombre, None)
                if mes:
                    fecha_str = f"2026-{mes:02d}-{dia:02d}"
                else:
                    fecha_str = datetime.now().strftime("%Y-%m-%d")
            else:
                fecha_str = datetime.now().strftime("%Y-%m-%d")
    except:
        fecha_str = datetime.now().strftime("%Y-%m-%d")

    # Buscar con ambas APIs
    resultado_kiwi = buscar_vuelos_kiwi(origen_iata, destino_iata, fecha_str)
    resultado_sky = buscar_vuelos_skyscanner(origen_iata, destino_iata, fecha_str)

    return f"{resultado_kiwi}\n\n{resultado_sky}"
