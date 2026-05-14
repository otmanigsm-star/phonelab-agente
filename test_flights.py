#!/usr/bin/env python3
# test_flights.py — Prueba rápida de búsqueda de vuelos
# Uso: python test_flights.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.tools import buscar_vuelos_kiwi, buscar_vuelos_skyscanner, buscar_vuelos
from dotenv import load_dotenv

load_dotenv()

def main():
    print("\n" + "="*70)
    print("  PRUEBA DE BÚSQUEDA DE VUELOS")
    print("="*70 + "\n")

    # Parámetros de búsqueda
    origen = "ALC"      # Alicante
    destino = "ORN"     # Oran
    fecha = "2026-05-20"

    print(f"Buscando vuelos: {origen} → {destino}")
    print(f"Fecha: {fecha}\n")

    # Test 1: Kiwi API
    print("-" * 70)
    print("1️⃣  Buscando con KIWI API...")
    print("-" * 70)
    resultado_kiwi = buscar_vuelos_kiwi(origen, destino, fecha)
    print(resultado_kiwi)

    # Test 2: Skyscanner API
    print("\n" + "-" * 70)
    print("2️⃣  Buscando con SKYSCANNER API...")
    print("-" * 70)
    resultado_sky = buscar_vuelos_skyscanner(origen, destino, fecha)
    print(resultado_sky)

    # Test 3: Función combinada
    print("\n" + "-" * 70)
    print("3️⃣  Búsqueda COMBINADA (ambas APIs)...")
    print("-" * 70)
    resultado_combined = buscar_vuelos("Alicante", "Oran", "20 de mayo")
    print(resultado_combined)

    print("\n" + "="*70)
    print("  ✅ PRUEBA COMPLETADA")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
