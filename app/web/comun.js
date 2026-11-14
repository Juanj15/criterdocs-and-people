// Funciones que comparten las pantallas de CriterDocs and People (CDP-47).
//
// Mientras no exista el inicio de sesión, el usuario escoge su perfil en el
// encabezado. La pantalla oculta lo que ese perfil no puede hacer; el servidor
// vuelve a revisar el rol en cada petición, como segunda barrera.

const PERFILES = { ADMINISTRATIVO: "Auxiliar administrativo", DIRECCION: "Dirección" };

// Nombres que ve el usuario para cada campo, iguales en todas las pantallas.
const ETIQUETAS = {
  nombre_completo: "Nombre completo", numero_documento: "Número de documento", correo: "Correo",
  banco: "Banco", numero_cuenta: "Número de cuenta", proyecto: "Proyecto", cargo: "Cargo",
  fecha_inicio: "Fecha de inicio", fecha_fin: "Fecha de fin", forma_pago: "Forma de pago",
  valor_mensual: "Valor mensual", valor_total: "Valor total", numero_meses: "Número de meses",
  estado: "Estado", tipo: "Tipo de documento", archivo: "Archivo",
};

function perfil() {
  try { return sessionStorage.getItem("perfil") || ""; } catch (e) { return ""; }
}

function esAuxiliar() { return perfil() === "ADMINISTRATIVO"; }

// Todo lo que viene del servidor se escapa antes de ponerlo en la página (CP-57).
function esc(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

async function api(ruta, opciones = {}) {
  const respuesta = await fetch(ruta, {
    ...opciones, headers: { "X-Rol": perfil(), ...(opciones.headers || {}) },
  });
  return { ok: respuesta.ok, cuerpo: await respuesta.json() };
}

function textoError(cuerpo) {
  const detalle = (Array.isArray(cuerpo.detalle) ? cuerpo.detalle : []).map((d) => ETIQUETAS[d] || d);
  return `${cuerpo.mensaje || "No fue posible completar la acción"}${detalle.length ? ": " + detalle.join(", ") : ""}`;
}

// El mismo recuadro en todas las pantallas: verde si salió bien, rojo si no.
function avisar(ok, texto) {
  const mensaje = document.getElementById("mensaje");
  mensaje.className = ok ? "ok" : "error";
  mensaje.textContent = texto;
}

function limpiarAviso() { document.getElementById("mensaje").className = ""; }

// Marca en rojo los campos que el servidor dice que faltan.
function marcarCampos(contenedor, cuerpo) {
  contenedor.querySelectorAll(".error").forEach((campo) => campo.classList.remove("error"));
  (Array.isArray(cuerpo.detalle) ? cuerpo.detalle : []).forEach((nombre) => {
    const campo = contenedor.querySelector(`[name="${nombre}"]`);
    if (campo) campo.classList.add("error");
  });
}

// Encabezado común: título, menú y selector de perfil.
function iniciarEncabezado(subtitulo, alCambiarPerfil) {
  const encabezado = document.querySelector("header");
  encabezado.innerHTML = `
    <div>
      <h1>CriterDocs and People</h1>
      <p>${esc(subtitulo)}</p>
      <nav>
        <a href="/" class="solo-auxiliar">Registrar colaborador</a>
        <a href="/ficha">Ficha del colaborador</a>
        <a href="/contratos">Documentos y contratos</a>
      </nav>
    </div>
    <label class="perfil">Perfil
      <select id="perfil" aria-label="Perfil">
        <option value="">Seleccione su perfil…</option>
        <option value="ADMINISTRATIVO">${PERFILES.ADMINISTRATIVO}</option>
        <option value="DIRECCION">${PERFILES.DIRECCION}</option>
      </select>
    </label>`;
  const selector = document.getElementById("perfil");
  selector.value = perfil();
  document.body.dataset.perfil = perfil();
  selector.addEventListener("change", () => {
    try { sessionStorage.setItem("perfil", selector.value); } catch (e) { /* sin almacenamiento */ }
    document.body.dataset.perfil = selector.value;
    limpiarAviso();
    if (alCambiarPerfil) alCambiarPerfil();
  });
}
