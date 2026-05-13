# agent/main.py — Servidor FastAPI + Webhook de WhatsApp

import os
import time
import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from agent.brain import generar_respuesta
from agent.memory import inicializar_db, guardar_mensaje, obtener_historial
from agent.providers import obtener_proveedor

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
log_level = logging.DEBUG if ENVIRONMENT == "development" else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger("agentkit")

proveedor = obtener_proveedor()
PORT = int(os.getenv("PORT", 8000))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
MAX_MESSAGE_LENGTH = 1000

# Rate limiting : max 10 messages par numéro par minute
_rate_buckets: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT = 10
RATE_WINDOW = 60


def _is_rate_limited(telefono: str) -> bool:
    now = time.time()
    _rate_buckets[telefono] = [t for t in _rate_buckets[telefono] if now - t < RATE_WINDOW]
    if len(_rate_buckets[telefono]) >= RATE_LIMIT:
        return True
    _rate_buckets[telefono].append(now)
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    await inicializar_db()
    logger.info(f"Serveur démarré sur le port {PORT} — Proveedor: {proveedor.__class__.__name__}")
    yield


app = FastAPI(
    title="AgentKit — Support Phonelab Store",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)


@app.get("/")
async def health_check():
    return {"status": "ok"}


@app.get("/webhook")
async def webhook_verificacion(request: Request):
    resultado = await proveedor.validar_webhook(request)
    if resultado is not None:
        return PlainTextResponse(str(resultado))
    return {"status": "ok"}


@app.post("/webhook")
async def webhook_handler(request: Request):
    # Vérification du secret webhook si configuré
    if WEBHOOK_SECRET:
        token = request.headers.get("X-Webhook-Secret", "")
        if token != WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        mensajes = await proveedor.parsear_webhook(request)

        for msg in mensajes:
            if msg.es_propio or not msg.texto:
                continue

            # Rate limiting par numéro
            if _is_rate_limited(msg.telefono):
                logger.warning(f"Rate limit dépassé pour {msg.telefono[-4:]}")
                continue

            # Limite taille du message
            texto = msg.texto[:MAX_MESSAGE_LENGTH]

            logger.info(f"Message reçu de ...{msg.telefono[-4:]}")

            historial = await obtener_historial(msg.telefono)
            respuesta = await generar_respuesta(texto, historial)

            await guardar_mensaje(msg.telefono, "user", texto)
            await guardar_mensaje(msg.telefono, "assistant", respuesta)

            await proveedor.enviar_mensaje(msg.telefono, respuesta)

        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur webhook: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Erreur interne")
