# CriterDocs and People

Sistema de gestión de contratación por prestación de servicios y cuentas de cobro (SGPS) para Critertec.
Proyecto de aula de **Ingeniería de Software II** (Institución Universitaria Pascual Bravo).

- **Estudiante:** Juan José Jiménez Ortiz (Grupo 10)
- **Metodología:** Scrum, sprints de una semana, seguimiento en Jira (espacio `CDP`)
- **Diseño de pruebas:** documento RTF3 (pruebas estructurales / caja blanca)

## Estado actual: Sprint 2

| Historia | Estado | Qué hay |
|---|---|---|
| HU-01 Registro de colaborador (CDP-10) | Terminada | `registrar()` con los 7 caminos de la RTF3, `editar()`, `agregar_vinculacion()`, `cambiar_estado()`, API REST y formulario web |
| HU-02 Generación de contratos (CDP-11) | Sprint 2 | Pendiente |
| HU-04 Cuentas de cobro (CDP-12) | Sprint 3 | Pendiente |

Por ahora los datos se guardan en memoria; la base de datos y la carga de documentos llegan con la HU-02.

## Flujo de trabajo con ramas

Cada subtarea de Jira se trabaja en su propia rama `feature/CDP-XX-descripcion`, se abre un Pull
Request hacia `main` y se integra cuando las pruebas y Pylint pasan.

| Rama | Subtarea | Contenido |
|---|---|---|
| `feature/CDP-22-editar-y-vinculaciones` | CDP-22 | `editar()`, `agregar_vinculacion()` y sus endpoints |
| `feature/CDP-21-formulario-registro` | CDP-21 | Formulario web de registro |

## Estructura

```
app/
  dominio/        Entidades (Colaborador, Vinculacion, enumeraciones) y Resultado
  servicios/      Lógica del negocio (ServicioColaborador, ControlAcceso)
  persistencia/   Repositorios (en memoria para el Sprint 1)
  api/            Endpoints FastAPI
tests/            Pruebas unitarias e integración (pytest)
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
| Pruebas | 46 pasan |
| Cobertura de ramas de `ServicioColaborador` | 100 % |
| Cobertura total del proyecto | 100 % |
| Pylint (`app`) | 10.00/10 |

## Convención de commits

`tipo(alcance): descripción (CLAVE-JIRA)`, donde el tipo es `feat`, `test`, `fix`, `refactor`, `docs` o
`chore`. La clave de Jira permite enlazar cada commit con su subtarea.
