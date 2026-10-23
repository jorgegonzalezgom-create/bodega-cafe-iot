// tablero.js: pide las lecturas a /api/lecturas cada 5 segundos y pinta el tablero.

const U = JSON.parse(document.getElementById("umbrales").textContent);
const REFRESCO_MS = 5000;     // cada cuanto se piden datos nuevos
const SIN_SENAL_S = 30;       // el ESP32 envia cada 10 s: 30 s sin datos = algo pasa
const LIMITE = 60;            // lecturas para las graficas (60 x 10 s = 10 minutos)

const $ = (id) => document.getElementById(id);
const num = new Intl.NumberFormat("es-CO", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const fechaHora = new Intl.DateTimeFormat("es-CO", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23", timeZone: "America/Bogota" });
const soloHora = new Intl.DateTimeFormat("es-CO", { hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23", timeZone: "America/Bogota" });
const relativo = new Intl.RelativeTimeFormat("es", { numeric: "auto" });

const tempFuera = (t) => t < U.temp_min || t > U.temp_max;
const humFuera = (h) => h < U.hum_min || h > U.hum_max;
const css = (nombre) => getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();

// Explica en palabras por que una lectura esta en ALERTA
function motivos(l) {
  const m = [];
  if (l.temperatura > U.temp_max) m.push(`temperatura alta (${num.format(l.temperatura)} °C, máx. ${U.temp_max} °C)`);
  if (l.temperatura < U.temp_min) m.push(`temperatura baja (${num.format(l.temperatura)} °C, mín. ${U.temp_min} °C)`);
  if (l.humedad > U.hum_max) m.push(`humedad alta: riesgo de moho (${num.format(l.humedad)} %, máx. ${U.hum_max} %)`);
  if (l.humedad < U.hum_min) m.push(`el grano se reseca: humedad baja (${num.format(l.humedad)} %, mín. ${U.hum_min} %)`);
  return m;
}

function haceCuanto(segundos) {
  if (segundos < 60) return relativo.format(-Math.round(segundos), "second");
  if (segundos < 3600) return relativo.format(-Math.round(segundos / 60), "minute");
  if (segundos < 86400) return relativo.format(-Math.round(segundos / 3600), "hour");
  return relativo.format(-Math.round(segundos / 86400), "day");
}

function icono(id) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
  use.setAttribute("href", "#" + id);
  svg.append(use);
  return svg;
}

// ---------- Indicador de conexion (arriba a la derecha) ----------
function conexion(estado, texto) {
  $("conexion").dataset.estado = estado;
  $("conexion-texto").textContent = texto;
}

// ---------- Estado general ----------
function pintarEstado(ultima, segundos) {
  const caja = $("estado");
  caja.dataset.estado = ultima.estado;
  $("estado-uso").setAttribute("href", ultima.estado === "OK" ? "#i-ok" : "#i-alerta");
  if (ultima.estado === "OK") {
    $("estado-titulo").textContent = "Condiciones seguras";
    $("estado-detalle").textContent = "Temperatura y humedad dentro del rango para café pergamino.";
  } else {
    const m = motivos(ultima);
    $("estado-titulo").textContent = "Alerta en la bodega";
    $("estado-detalle").textContent = m.length ? m[0][0].toUpperCase() + m.join(" · ").slice(1) + "." : "Lectura fuera de rango.";
  }
  // Si el ESP32 dejo de enviar, el estado mostrado ya no es el actual: se avisa
  const hora = $("estado-hora");
  hora.toggleAttribute("data-viejo", segundos > SIN_SENAL_S);
  hora.textContent = segundos > SIN_SENAL_S
    ? `Sin datos nuevos: última lectura ${haceCuanto(segundos)}. Revisa el ESP32.`
    : `Última lectura ${haceCuanto(segundos)}`;
}

// ---------- Tarjetas de temperatura / humedad ----------
function pintarIndicador(clave, valor, anterior, fuera, escalaMax) {
  $(`${clave}-valor`).textContent = num.format(valor);
  document.querySelector(`.indicador[data-var="${clave}"]`).dataset.fuera = fuera ? "si" : "no";

  let v = "&nbsp;";
  if (anterior !== undefined) {
    const d = valor - anterior;
    v = Math.abs(d) < 0.05 ? "Sin cambio desde la lectura anterior"
      : `${d > 0 ? "▲" : "▼"} ${num.format(Math.abs(d))} desde la lectura anterior`;
  }
  $(`${clave}-variacion`).innerHTML = v;

  const medidor = $(`${clave}-medidor`);
  medidor.style.setProperty("--pos", Math.min(Math.max(valor / escalaMax * 100, 0), 100) + "%");
  medidor.dataset.listo = "";
}

function pintarResumen(lecturas) {
  const alertas = lecturas.filter((l) => l.estado === "ALERTA").length;
  $("res-alertas").textContent = alertas;
  $("res-total").textContent = alertas === 1 ? "alerta" : "alertas";
  const pct = Math.round(alertas / lecturas.length * 100);
  $("res-porcentaje").textContent = `en las últimas ${lecturas.length} lecturas (${pct} %)`;
  $("res-dispositivo").textContent = lecturas[0].dispositivo;
}

// ---------- Tabla ----------
function pintarTabla(lecturas) {
  const filas = lecturas.slice(0, 20).map((l) => {
    const tr = document.createElement("tr");
    const celda = (texto, clase) => {
      const td = document.createElement("td");
      td.textContent = texto;   // textContent: nunca se interpreta como HTML
      if (clase) td.className = clase;
      return td;
    };
    const estado = document.createElement("td");
    const pastilla = document.createElement("span");
    pastilla.className = "pastilla " + l.estado;
    pastilla.append(icono(l.estado === "OK" ? "i-ok" : "i-alerta"), l.estado);
    estado.append(pastilla);
    tr.append(
      celda(fechaHora.format(new Date(l.fecha))),
      celda(l.dispositivo),
      celda(num.format(l.temperatura), "num" + (tempFuera(l.temperatura) ? " fuera" : "")),
      celda(num.format(l.humedad), "num" + (humFuera(l.humedad) ? " fuera" : "")),
      estado,
    );
    return tr;
  });
  $("filas").replaceChildren(...filas);
}

// ---------- Graficas (Chart.js) ----------
// Plugin propio: pinta la franja verde del rango seguro detras de la linea
const franja = {
  id: "franja",
  beforeDatasetsDraw(chart, _args, o) {
    const { ctx, chartArea: a, scales: { y } } = chart;
    const arriba = Math.max(y.getPixelForValue(o.max), a.top);
    const abajo = Math.min(y.getPixelForValue(o.min), a.bottom);
    ctx.save();
    ctx.fillStyle = css("--franja");
    ctx.fillRect(a.left, arriba, a.right - a.left, abajo - arriba);
    ctx.restore();
  },
};

const graficas = {};

function crearGrafica(id, color, min, max, fuera, unidad, rangoVisible) {
  return new Chart($(id), {
    type: "line",
    plugins: [franja],
    data: { labels: [], datasets: [{
      data: [],
      borderColor: () => css(color),
      borderWidth: 2,
      tension: 0.3,
      // Los puntos en alerta se ven como triangulos rojos (no solo por color)
      pointStyle: (c) => (fuera(c.raw) ? "triangle" : "circle"),
      pointRadius: (c) => (fuera(c.raw) ? 5 : 0),
      pointHoverRadius: 5,
      pointBackgroundColor: (c) => (fuera(c.raw) ? css("--alerta") : css(color)),
      pointBorderColor: (c) => (fuera(c.raw) ? css("--alerta") : css(color)),
    }] },
    options: {
      animation: false,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        franja: { min, max },
        tooltip: { callbacks: { label: (c) => ` ${num.format(c.raw)} ${unidad}${fuera(c.raw) ? " · ALERTA" : ""}` } },
      },
      scales: {
        x: { ticks: { maxTicksLimit: 6, maxRotation: 0, color: () => css("--tenue") }, grid: { display: false } },
        y: { suggestedMin: rangoVisible[0], suggestedMax: rangoVisible[1],
             ticks: { color: () => css("--tenue") }, grid: { color: () => css("--rejilla") } },
      },
    },
  });
}

function pintarGraficas(lecturas) {
  if (typeof Chart === "undefined") return;   // sin internet no carga Chart.js: el resto sigue funcionando
  Chart.defaults.font.family = css("--fuente");
  if (!graficas.temp) {
    graficas.temp = crearGrafica("grafica-temp", "--temp", U.temp_min, U.temp_max, tempFuera, "°C", [U.temp_min - 5, U.temp_max + 5]);
    graficas.hum = crearGrafica("grafica-hum", "--hum", U.hum_min, U.hum_max, humFuera, "%", [U.hum_min - 10, U.hum_max + 10]);
  }
  const orden = [...lecturas].reverse();   // de la mas vieja a la mas nueva
  const horas = orden.map((l) => soloHora.format(new Date(l.fecha)));
  for (const [clave, campo, nombre, unidad] of [["temp", "temperatura", "Temperatura", "°C"], ["hum", "humedad", "Humedad", "%"]]) {
    const g = graficas[clave];
    const datos = orden.map((l) => l[campo]);
    g.data.labels = horas;
    g.data.datasets[0].data = datos;
    g.update();
    g.canvas.setAttribute("aria-label",
      `${nombre} de las últimas ${datos.length} lecturas: entre ${num.format(Math.min(...datos))} y ${num.format(Math.max(...datos))} ${unidad}`);
  }
}

// ---------- Ciclo principal ----------
async function refrescar() {
  let lecturas;
  try {
    const r = await fetch(`/api/lecturas?limite=${LIMITE}`, { cache: "no-store" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    lecturas = await r.json();
  } catch (e) {
    conexion("error", "Sin conexión con el servidor");
    return;
  }

  if (!lecturas.length) {
    conexion("sin-senal", "Esperando datos del ESP32");
    return;
  }

  const ultima = lecturas[0];
  const segundos = Math.max((Date.now() - new Date(ultima.fecha)) / 1000, 0);
  if (segundos > SIN_SENAL_S) conexion("sin-senal", `Sin datos del ESP32 ${haceCuanto(segundos)}`);
  else conexion("vivo", `En vivo · ${soloHora.format(new Date())}`);

  pintarEstado(ultima, segundos);
  pintarIndicador("temp", ultima.temperatura, lecturas[1]?.temperatura, tempFuera(ultima.temperatura), 40);
  pintarIndicador("hum", ultima.humedad, lecturas[1]?.humedad, humFuera(ultima.humedad), 100);
  pintarResumen(lecturas);
  pintarTabla(lecturas);
  pintarGraficas(lecturas);
}

refrescar();
setInterval(() => { if (!document.hidden) refrescar(); }, REFRESCO_MS);
document.addEventListener("visibilitychange", () => { if (!document.hidden) refrescar(); });
// Si cambia el modo claro/oscuro, se redibujan las graficas con los colores nuevos
matchMedia("(prefers-color-scheme: light)").addEventListener("change", () => {
  Object.values(graficas).forEach((g) => g.update());
});
