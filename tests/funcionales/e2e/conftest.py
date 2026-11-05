"""Arranca la aplicación real en un hilo para que Playwright la use como un usuario."""
import threading
import time

import pytest
import uvicorn

from app.api.main import app

PUERTO = 8765


@pytest.fixture(scope="session")
def url_aplicacion():
    """Levanta uvicorn una sola vez para todas las pruebas de extremo a extremo."""
    configuracion = uvicorn.Config(app, host="127.0.0.1", port=PUERTO, log_level="warning")
    servidor = uvicorn.Server(configuracion)
    hilo = threading.Thread(target=servidor.run, daemon=True)
    hilo.start()
    while not servidor.started:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{PUERTO}"
    servidor.should_exit = True
    hilo.join()


@pytest.fixture
def cedula_nueva():
    """Cédula distinta en cada prueba, porque el repositorio en memoria se comparte."""
    return "30" + str(time.time_ns())[-8:]
