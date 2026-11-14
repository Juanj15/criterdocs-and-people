"""Las pantallas y sus archivos comunes se sirven bien (CDP-46, CDP-47)."""
from fastapi.testclient import TestClient

from app.api.main import app

cliente = TestClient(app)


def test_la_ficha_del_colaborador_se_muestra():
    respuesta = cliente.get("/ficha")

    assert respuesta.status_code == 200
    assert 'id="datos"' in respuesta.text and 'id="nuevo_proyecto"' in respuesta.text


def test_el_script_comun_tiene_el_selector_de_perfil():
    respuesta = cliente.get("/comun.js")

    assert respuesta.headers["content-type"].startswith("text/javascript")
    assert "function iniciarEncabezado" in respuesta.text


def test_los_estilos_comunes_ocultan_lo_que_no_es_del_perfil():
    respuesta = cliente.get("/comun.css")

    assert respuesta.headers["content-type"].startswith("text/css")
    assert '.solo-auxiliar' in respuesta.text
