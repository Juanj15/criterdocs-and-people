# CriterDocs and People

Sistema de gestión de contratación por prestación de servicios y cuentas de cobro (SGPS) para Critertec.
Proyecto de aula de **Ingeniería de Software II** (Institución Universitaria Pascual Bravo).

- **Estudiante:** Juan José Jiménez Ortiz (Grupo 10)
- **Metodología:** Scrum, sprints de una semana, seguimiento en Jira (espacio `CDP`)
- **Diseño de pruebas:** RTF3 (pruebas estructurales / caja blanca) y RTF4 (pruebas funcionales / caja negra)

## Estado actual: Sprint 3

| Historia | Estado | Qué hay |
|---|---|---|
| HU-01 Registro de colaborador (CDP-10) | Terminada | `registrar()` con los 7 caminos de la RTF3, `editar()`, `agregar_vinculacion()`, `cambiar_estado()`, `consultar()`, API REST y formulario web |
| HU-02 Generación de contratos (CDP-11) | Sprint 3 | Carga de los 4 documentos en PDF, `generar_contrato()` con los 7 caminos de la RTF3, plantillas por forma de pago, PDF con fpdf2, historial y pantalla web |
| HU-04 Cuentas de cobro (CDP-12) | Sprint 3 | Pendiente |

Por ahora los datos y los PDF se guardan en memoria; la base de datos llega en un sprint siguiente.

## Flujo de trabajo con ramas

Cada subtarea de Jira se trabaja en su propia rama `feature/CDP-XX-descripcion`, se abre un Pull
Request hacia `main` y se integra cuando las pruebas y Pylint pasan.

| Rama | Subtarea | Contenido |
|---|---|---|
| `feature/CDP-22-editar-y-vinculaciones` | CDP-22 | `editar()`, `agregar_vinculacion()` y sus endpoints |
| `feature/CDP-21-formulario-registro` | CDP-21 | Formulario web de registro |
| `feature/CDP-43-hallazgos-caja-negra` | CDP-43 | Consulta y cambio de estado por la API (hallazgos de la RTF4) |
| `feature/CDP-41-coleccion-postman` | CDP-41 | Colección Postman de la HU-01 (se ejecuta con Newman) |
| `feature/CDP-42-pruebas-e2e-playwright` | CDP-42 | Pruebas de extremo a extremo del formulario con Playwright |
| `feature/CDP-25-carga-documentos` | CDP-25 | Carga de los documentos de soporte en PDF |
| `feature/CDP-27-contrato-pdf` | CDP-26, CDP-27, CDP-28, CDP-30, CDP-44 | Validación de documentos, contrato en PDF, historial, pantalla y pruebas |

## Estructura

```
app/
  dominio/        Entidades (Colaborador, Vinculacion, enumeraciones) y Resultado
  servicios/      Lógica del negocio (ServicioColaborador, ControlAcceso)
  persistencia/   Repositorios (en memoria para el Sprint 1)
  api/            Endpoints FastAPI
tests/            Pruebas unitarias e integración (pytest)
  funcionales/    Pruebas de caja negra (RTF4): colección Postman y pruebas Playwright
```

La separación en capas es la del diagrama de clases de la RTF3: así cada servicio se prueba solo,
reemplazando el repositorio por un objeto simulado cuando hace falta forzar un error.

## Cómo ejecutarlo

Requisitos: Python 3.10 o superior.

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements-dev.txt

uvicorn app.api.main:app --reload
```

El formulario de registro queda en http://127.0.0.1:8000/ y la documentación interactiva de la API
en http://127.0.0.1:8000/docs. Para probar el registro, envíe el
encabezado `X-Rol: ADMINISTRATIVO` (el inicio de sesión llega en un sprint posterior).

## Endpoints

| Método y ruta | Qué hace | Rol |
|---|---|---|
| `POST /colaboradores` | Registra un colaborador con su primer proyecto | ADMINISTRATIVO |
| `GET /colaboradores/{id}` | Consulta el colaborador (cuenta bancaria enmascarada) | ADMINISTRATIVO o DIRECCION |
| `PATCH /colaboradores/{id}` | Edita datos personales o bancarios | ADMINISTRATIVO |
| `POST /colaboradores/{id}/vinculaciones` | Agrega otro proyecto | ADMINISTRATIVO |
| `POST /colaboradores/{id}/documentos` | Carga un documento en PDF (form-data: `tipo`, `archivo`) | ADMINISTRATIVO |
| `GET /colaboradores/{id}/documentos` | Documentos cargados y los que faltan | ADMINISTRATIVO o DIRECCION |
| `POST /colaboradores/{id}/vinculaciones/{id_v}/contrato` | Genera el contrato en PDF de un proyecto | ADMINISTRATIVO |
| `GET /colaboradores/{id}/contratos` | Historial de contratos | ADMINISTRATIVO o DIRECCION |
| `GET /contratos/{id}/pdf` | Descarga el PDF | ADMINISTRATIVO o DIRECCION |

Pantallas: registro en http://127.0.0.1:8000/ y documentos y contratos en http://127.0.0.1:8000/contratos.
| `PATCH /colaboradores/{id}/estado` | Activa o desactiva (`{"estado": "INACTIVO"}`) | ADMINISTRATIVO |

## Pruebas funcionales (caja negra, RTF4)

Estas pruebas no miran el código: envían datos a la aplicación que está corriendo y revisan lo que
responde. Cada caso lleva el ID de la matriz del documento RTF4 (`CP-01`, `CP-02`, ...).

```bash
pip install -r requirements-funcionales.txt
playwright install chromium

# 1. Formulario en el navegador (Playwright levanta la aplicación solo)
pytest -m funcional tests/funcionales

# 2. API con la colección de Postman (con la aplicación corriendo en otra terminal)
uvicorn app.api.main:app
npx newman run tests/funcionales/postman/hu01_registro_colaborador.postman_collection.json
npx newman run tests/funcionales/postman/hu02_contratos.postman_collection.json
```

La colección también se puede importar en Postman (Import -> archivo) y correr con el *Collection Runner*.
Las pruebas funcionales están marcadas con `funcional` y no corren con el `pytest` normal, porque necesitan
el navegador.

Hallazgo abierto: el correo no valida su formato (CP-14). Está marcado como `xfail` en Playwright y
registrado en Jira (CDP-43).

## Pruebas y calidad

```bash
# Pruebas unitarias con cobertura de ramas
pytest --cov --cov-report=term-missing

# Reporte HTML de cobertura (queda en htmlcov/index.html)
pytest --cov --cov-report=html

# Análisis estático
pylint app
pylint tests --disable=missing-function-docstring,redefined-outer-name,too-many-arguments,too-many-positional-arguments
```

Cada prueba de `tests/test_hu01_registro_colaborador.py` lleva en el nombre el camino del grafo de flujo
de la RTF3 que recorre (`test_c1_...` a `test_c7_...`). Las de edición y nuevos proyectos están en
`tests/test_hu01_editar_y_vinculaciones.py`.

| Indicador | Resultado |
|---|---|
| Pruebas unitarias e integración | 99 pasan |
| Pruebas funcionales Playwright | 10 pasan, 1 hallazgo abierto (xfail) |
| Colecciones Postman (Newman) | HU-01: 26 peticiones, 61 aserciones; HU-02: 27 peticiones, 60 aserciones; 0 fallas |
| Cobertura de ramas de `ServicioColaborador` | 100 % |
| Cobertura de ramas de `ServicioContrato` y `ServicioDocumentos` | 100 % |
| Cobertura total del proyecto | 100 % |
| Pylint (`app`) | 10.00/10 |

## Convención de commits

`tipo(alcance): descripción (CLAVE-JIRA)`, donde el tipo es `feat`, `test`, `fix`, `refactor`, `docs` o
`chore`. La clave de Jira permite enlazar cada commit con su subtarea.
