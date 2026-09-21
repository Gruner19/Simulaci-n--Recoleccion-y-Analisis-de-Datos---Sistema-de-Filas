"""Interfaz web amigable sobre el sistema de resultados del experimento fatorial 2^3.

Solo usa la biblioteca estándar (http.server) y reutiliza las funciones de
analizar_resultados.py. Sirve un panel con pestañas, tablas, botones de
simulación y exportación con un clic (CSV / Excel / JSON / LaTeX).

Uso:
    python codigo/interfaz.py [--puerto 8000] [--abrir]

o, desde el Makefile:   make interfaz
"""
from __future__ import annotations

import argparse
import json
import queue
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, quote
import tempfile
from io import BytesIO

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
import analizar_resultados as ar
from config import DADOS, RAIZ, SALIDAS

PY = sys.executable
POR_DEFECTO = DADOS / "resultados_fatorial.csv"

_log = queue.Queue()
_estado = {"corriendo": False, "script": "", "progreso": ""}


# ------------------------------------------------------------------ exportación
def _ruta_salida(nombre, formato):
    ext = {"csv": "csv", "xlsx": "xlsx", "json": "json", "latex": "tex"}[formato]
    SALIDAS.mkdir(parents=True, exist_ok=True)
    base = Path(nombre)
    if not base.suffix or base.suffix[1:] != ext:
        base = Path(str(base) + "." + ext)
    return SALIDAS / base.name


def _exportar(df, nombre, formato):
    ruta = _ruta_salida(nombre, formato)
    ar.exportar(df, ruta, formato, str(nombre))
    return ruta


def _listar_entradas():
    candidatos = sorted(DADOS.glob("*.csv"))
    nombres = [str(DADOS / "resultados_fatorial.csv")]
    nombres += [str(c) for c in candidatos if c.name not in ("resultados_fatorial.csv",)]
    return nombres


def _correr(script):
    if _estado["corriendo"]:
        return {"ok": False, "error": "Ya hay una simulación en curso."}
    script = Path(script).name.replace("..", "")
    if not (RAIZ / "codigo" / script).with_suffix(".py").exists():
        return {"ok": False, "error": f"script no encontrado: {script}"}
    if script not in ("verificacion", "piloto", "experimento", "plano"):
        return {"ok": False, "error": f"script no autorizado: {script}"}
    cmd = [PY, str(RAIZ / "codigo" / f"{script}.py")]
    if script == "experimento":
        cmd += ["--force", "--n-procs", str(min(4, __import__("os").cpu_count() or 2))]
    _estado.update(corriendo=True, script=script, progreso="iniciando...")

    def objetivo():
        try:
            proc = subprocess.Popen(cmd, cwd=str(RAIZ), stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, bufsize=1)
            for linea in proc.stdout:
                _log.put(linea.rstrip())
                _estado["progreso"] = linea.rstrip()[-90:]
            proc.wait()
            _estado["progreso"] = "finalizado (rc=%d)" % proc.returncode
        except Exception as e:
            _log.put(f"ERROR: {e}")
            _estado["progreso"] = f"error: {e}"
        finally:
            _estado["corriendo"] = False

    threading.Thread(target=objetivo, daemon=True).start()
    return {"ok": True, "script": script}


# ------------------------------------------------------------------ gráficos + config
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def _graficos(tipo, entrada=str(POR_DEFECTO)):
    try:
        df = ar.leer_resultados(entrada)
        df["resposta"] = pd.to_numeric(df["resposta"], errors="coerce")
    except Exception:
        df = None
    import tempfile
    ruta_png = Path(tempfile.gettempdir()) / (f"fig_{tipo}.png")
    plt.rcParams.update({"font.size": 9, "figure.dpi": 120, "figure.facecolor": "#0d1117",
                         "axes.facecolor": "#161b22", "text.color": "#c9d1d9",
                         "axes.edgecolor": "#30363d", "axes.labelcolor": "#c9d1d9",
                         "xtick.color": "#c9d1d9", "ytick.color": "#c9d1d9"})
    if tipo == "hist" and df is not None:
        fig, ax = plt.subplots(figsize=(7, 3.5))
        ax.hist(df["resposta"].dropna(), bins=15, color="#58a6ff", edgecolor="#30363d", alpha=.9)
        ax.set_xlabel("Respuesta (min)"); ax.set_ylabel("Frecuencia")
        ax.set_title("Distribución de respuestas — Experimento 2³ (r=10)", fontsize=10)
        fig.tight_layout()
        fig.savefig(ruta_png, bbox_inches="tight")
        plt.close(fig)
    elif tipo == "efectos" and df is not None:
        out = ar.factorial_df(df, False)
        fig, ax = plt.subplots(figsize=(7, 4))
        colores = ["#58a6ff" if abs(v) > 0 else "#8b949e" for v in out["magnitud"]]
        ax.barh(out["efecto"], out["magnitud"], color=colores, height=.6)
        ax.axvline(0, color="#8b949e", lw=.8)
        ax.set_xlabel("Magnitud"); ax.set_title("Efectos factoriales 2³ (escala unidades)")
        fig.tight_layout()
        fig.savefig(ruta_png, bbox_inches="tight")
        plt.close(fig)
    elif tipo == "celula" and df is not None:
        agg = ar.agregar_df(df, ["celula"])
        fig, ax = plt.subplots(figsize=(7, 3.5))
        ax.bar(agg["celula"].astype(str), agg["media"], color="#58a6ff", edgecolor="#30363d")
        ax.set_ylabel("Respuesta media (min)"); ax.set_title("Respuesta por célula (8 células, r=10)")
        fig.tight_layout()
        fig.savefig(ruta_png, bbox_inches="tight")
        plt.close(fig)
    else:
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.text(.5, .5, "Sin datos\npara este gráfico", ha="center", va="center")
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(ruta_png, bbox_inches="tight")
        plt.close(fig)
    return ruta_png


def _leer_config():
    # muestra valores actuales desde config.py (como texto)
    import inspect, config as cfg_mod
    datos = {}
    for k in dir(cfg_mod):
        if not k.startswith("_") and isinstance(getattr(cfg_mod, k), (int, float, str, bool, list, tuple)):
            datos[k] = getattr(cfg_mod, k)
    return datos


# ------------------------------------------------------------------ request handler
class Handler(BaseHTTPRequestHandler):
    server_version = "ExperimentUFOP/1.0"

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"))

    def _html(self):
        self._send(200, PAGINA.encode("utf-8"), "text/html; charset=utf-8")

    def _params(self):
        q = parse_qs(self.path.split("?", 1)[1]) if "?" in self.path else {}
        return {k: unquote(v[0]) for k, v in q.items()}

    def _ejecutar(self, p):
        comando = p.get("cmd", "resumen")
        entrada = p.get("entrada", str(POR_DEFECTO))
        df = ar.leer_resultados(entrada)
        if comando == "resumen":
            return {"ok": True, "titulo": "Resumen del dataset",
                    "tabla": _df_json(ar.resumen_df(df)), "n": len(df),
                    "archivo": Path(entrada).name}
        if comando == "filtrar":
            sub = ar.filtrar_df(df, p.get("donde", ""))
            return {"ok": True, "titulo": f"Filtro: {(p.get('donde') or '(sin filtro)')}",
                    "tabla": _df_json(sub), "n": len(sub), "archivo": Path(entrada).name}
        if comando == "agregar":
            por = [x.strip() for x in p.get("por", "celula").split(",") if x.strip()]
            out = ar.agregar_df(df, por)
            return {"ok": True, "titulo": "Agrupación por " + ", ".join(por) or "celula",
                    "tabla": _df_json(out), "n": len(out), "archivo": Path(entrada).name}
        if comando == "factorial":
            log = p.get("log") == "1"
            out = ar.factorial_df(df, log)
            return {"ok": True, "titulo": f"Efectos del fatorial 2³ (escala {'ln' if log else 'unidades'})",
                    "tabla": _df_json(out), "n": len(out), "archivo": Path(entrada).name}
        if comando == "anova":
            log = p.get("log") == "1"
            tabla, r2 = ar.anova_df(df, log)
            return {"ok": True, "titulo": f"ANOVA OLS (escala {'ln' if log else 'unidades'}) — R² = {r2:.4f}",
                    "tabla": _df_json(tabla), "n": len(tabla), "archivo": Path(entrada).name}
        return {"ok": False, "error": f"comando desconocido: {comando}"}

    def do_GET(self):
        ruta = self.path.split("?", 1)[0]
        p = self._params()
        try:
            if ruta == "/":
                return self._html()
            if ruta == "/favicon.ico":
                return self._send(204, b"")
            if ruta == "/api/estado":
                return self._json({"estado": _estado})
            if ruta == "/api/log":
                filas = []
                while not _log.empty():
                    filas.append(_log.get())
                return self._json({"lineas": filas})
            if ruta == "/api/listar_archivos":
                return self._json({"archivos": _listar_entradas()})
            if ruta == "/api/graficos":
                ruta_img = _graficos(p.get("tipo", "hist"), p.get("entrada", str(POR_DEFECTO)))
                cuerpo = ruta_img.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(cuerpo)))
                self.end_headers()
                self.wfile.write(cuerpo)
                return
            if ruta == "/api/config":
                return self._json({"ok": True, "config": _leer_config()})
            if ruta == "/api/columnas":
                df = ar.leer_resultados(p.get("entrada", str(POR_DEFECTO)))
                return self._json({"columnas": [str(c) for c in df.columns]})
            if ruta == "/api/entrada":
                self._send(200, ar.leer_resultados(p.get("entrada", str(POR_DEFECTO)))
                           .to_csv(index=False).encode("utf-8"), "text/csv")
                return
            if ruta == "/api/simular":
                return self._json(_correr(p.get("script", "")))
            if ruta == "/api/ejecutar":
                return self._json(self._ejecutar(p))
            if ruta == "/descargar":
                return self._descargar(p.get("f", ""))
        except Exception as e:
            self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 400)
        return self._send(404, b"Not found")

    def _descargar(self, nombre):
        try:
            ruta = (SALIDAS / Path(nombre).name).resolve()
            if not str(ruta).startswith(str(SALIDAS.resolve())) or not ruta.exists():
                return self._send(404, b"no encontrado")
            cuerpo = ruta.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{quote(ruta.name)}"')
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)
        except Exception as e:
            self._json({"ok": False, "error": str(e)}, 400)

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/exportar":
            return self._send(404, b"Not found")
        l = int(self.headers.get("Content-Length", 0))
        try:
            datos = json.loads(self.rfile.read(l) or b"{}")
        except Exception as e:
            return self._json({"ok": False, "error": f"JSON inválido: {e}"}, 400)
        try:
            df = ar._df_from_json(datos["df"])
            ruta = _exportar(df, datos["nombre"], datos["formato"])
            return self._json({"ok": True, "ruta": str(ruta), "mensaje": f"Exportado a {ruta.name}",
                               "descarga": "/descargar?f=" + quote(ruta.name)})
        except Exception as e:
            return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 400)


def _df_json(df):
    df = df.copy()
    for c in df.columns:
        if hasattr(df[c], "dtype") and str(df[c].dtype) in ("float64", "float32", "int64"):
            df[c] = df[c].round(4)
    return {"columnas": [str(c) for c in df.columns],
            "filas": df.astype(object).where(df.notna(), None).values.tolist()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--abrir", action="store_true", help="abre el navegador automáticamente")
    args = ap.parse_args()

    if not POR_DEFECTO.exists():
        print("Aviso: aún no hay datos/resultados_fatorial.csv.\n"
              "Ejecuta  make experimento  o usa la pestaña 'Simular' de la interfaz.")

    httpd = ThreadingHTTPServer((args.host, args.puerto), Handler)
    url = f"http://localhost:{args.puerto}"
    print("=" * 58)
    print(f"  Panel de simulación y análisis disponible en:")
    print(f"      {url}")
    print("  (Ctrl+C para salir)")
    print("=" * 58)
    if args.abrir:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nInterfaz cerrada.")


# =============================================================== HTML/JS =====
PAGINA = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Panel — Experimento Fatorial 2³</title>
<style>
:root{--f:#1f4e79;--bg:#f4f6f8;--b:#dfe3e8;--txt:#222;--ok:#1e7e34;--err:#b3261e}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:15px/1.5 system-ui,sans-serif}
header{background:var(--f);color:#fff;padding:14px 22px;display:flex;justify-content:space-between;align-items:center}
header h1{font-size:19px;margin:0}header .estado{font-size:13px}
#tabnav{position:sticky;top:0;background:#fff;border-bottom:1px solid var(--b);display:flex;gap:4px;padding:8px 22px;z-index:5}
#tabnav button{border:1px solid var(--b);background:#fff;padding:8px 14px;border-radius:8px;cursor:pointer;font-weight:600}
#tabnav button.act{background:var(--f);color:#fff;border-color:var(--f)}
main{padding:22px;max-width:1180px;margin:auto}
.caja{background:#fff;border:1px solid var(--b);border-radius:10px;padding:16px 18px;margin:14px 0}
label{display:block;margin:6px 0 2px;font-weight:600;font-size:13px}
input,select,textarea{width:100%;padding:8px;border:1px solid var(--b);border-radius:7px;font:inherit}
select{width:100%}
.mini{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.accion{background:var(--f);color:#fff;border:0;padding:10px 16px;border-radius:8px;cursor:pointer;font-weight:600}
.accion:disabled{opacity:.5;cursor:not-allowed}
.sec{border:1px solid var(--b);background:#fff;border-radius:8px;padding:8px 12px;cursor:pointer}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:10px}
th,td{border:1px solid var(--b);padding:6px 9px;text-align:right}th{background:var(--f);color:#fff;text-align:center}
th:first-child,td:first-child{text-align:left}
.tag{display:inline-block;background:#eef2f7;color:var(--f);border-radius:20px;padding:2px 12px;font-size:12px}
.alert{display:block;background:var(--ok);color:#fff;padding:8px 11px;border-radius:8px;margin-top:8px}
.alert.err{background:var(--err)}
.logf{font-family:ui-monospace,monospace;background:#0d1117;color:#c9d1d9;border-radius:8px;padding:10px;
  white-space:pre-wrap;max-height:260px;overflow:auto;font-size:12px}
::selection{background:var(--f);color:#fff}
::-webkit-scrollbar{width:9px}
</style>
</head>
<body>
<header><h1>Sistema de simulación y análisis — Fatorial 2³ (r&nbsp;=&nbsp;10)</h1>
<div class="estado" id="cabeza">● listo</div></header>

<div id="tabnav">
  <button data-t="resumen" class="act">Resumen</button>
  <button data-t="agregar">Agrupar</button>
  <button data-t="factorial">Efectos</button>
  <button data-t="anova">ANOVA</button>
  <button data-t="filtrar">Filtrar</button>
  <button data-t="simular">Simular</button>
  <button data-t="graficos">Gráficos</button>
  <button data-t="configurar">Configurar</button>
</div>

<main>
<div class="caja">
  <div class="mini">
    <div><label>Archivo de entrada</label><select id="entrada"></select></div>
    <div><label>Operación actual</label><span id="titulo" class="tag">—</span></div>
  </div>
</div>

<section id="v-resumen" style="display:block"><div class="caja"><h3>Resumen del dataset</h3>
  <div id="t-resumen"></div><div id="ex-resumen"></div></div></section>

<section id="v-agregar" style="display:none"><div class="caja"><h3>Agrupar por factores</h3>
  <label>Factores de agrupación (separados por coma): A, B, C, celula</label>
  <input id="ag-por" value="celula">
  <button class="accion" onclick="correr('agregar',{por:gv('#ag-por')})">Agrupar</button>
  <div id="t-agregar"></div><div id="ex-agregar"></div></div></section>

<section id="v-factorial" style="display:none"><div class="caja"><h3>Efectos del fatorial 2³</h3>
  <label><input type="checkbox" id="fac-log"> Usar escala logarítmica (ln)</label>
  <button class="accion" onclick="correr('factorial',{log:(gvC('#fac-log')?'1':'0')})">Calcular efectos</button>
  <div id="t-factorial"></div><div id="ex-factorial"></div></div></section>

<section id="v-anova" style="display:none"><div class="caja"><h3>Tabla ANOVA (OLS)</h3>
  <label><input type="checkbox" id="an-log"> Usar escala logarítmica (ln)</label>
  <button class="accion" onclick="correr('anova',{log:(gvC('#an-log')?'1':'0')})">Ajustar modelo</button>
  <div id="t-anova"></div><div id="ex-anova"></div></div></section>

<section id="v-filtrar" style="display:none"><div class="caja"><h3>Filtrar filas</h3>
  <label>Expresión (pandas):</label>
  <input id="fi-donde" value='celula==2 & replica>=5'>
  <button class="accion" onclick="correr('filtrar',{donde:gv('#fi-donde')})">Filtrar</button>
  <div id="t-filtrar"></div><div id="ex-filtrar"></div>
  <hr><button class="sec" onclick="descargarEntrada()">⬇ Descargar dataset completo (CSV)</button></div></section>

<section id="v-simular" style="display:none"><div class="caja"><h3>Ejecutar simulaciones</h3>
  <p>Lanza los scripts del proyecto (verificación, plano, piloto y el fatorial de 80 corridas).
  Algunos tardan varios minutos; el log se actualiza solo.</p>
  <div class="mini">
    <button class="accion" onclick="simular('verificacion')">Verificación (vs. teoría)</button>
    <button class="accion" onclick="simular('plano')">Plano experimental</button>
  </div>
  <div class="mini" style="margin-top:10px">
    <button class="accion" onclick="simular('piloto')">Piloto / AED</button>
    <button class="accion" onclick="simular('experimento')">Experimento (80 corridas)</button>
  </div>
  <p id="sim-estado"></p><div class="logf" id="sim-log">(log en vivo)</div></div></section>

<section id="v-graficos" style="display:none"><div class="caja"><h3>Gráficos generados</h3>
  <p>Visualiza los datos del experimento con vistas rápidas generadas por la interfaz.</p>
  <div class="mini">
    <button class="accion" onclick="mostrarGraf('hist')">📊 Histograma de respuestas</button>
    <button class="accion" onclick="mostrarGraf('efectos')">📈 Efectos factoriales</button>
    <button class="accion" onclick="mostrarGraf('celula')">📉 Medias por célula</button>
  </div>
  <div style="margin-top:12px"><img id="img-graf" style="max-width:100%;border:1px solid var(--b);border-radius:8px;display:none;" alt="gráfico"></div>
  <p style="font-size:12px;color:#666;margin-top:4px">Nota: los archivos originales en <code>figuras/</code> se generan con `make datos`.</p>
</div></section>

<section id="v-configurar" style="display:none"><div class="caja"><h3>Configurar variables del experimento</h3>
  <p>Modifica los parámetros del experimento y guárdalos en un archivo de configuración temporal.</p>
  <div class="mini">
    <div><label>Número de servidores (A - bajo / A + alto)</label><input id="cfg-c-minus" value="1"><input id="cfg-c-plus" value="2"></div>
    <div><label>Tasa de llegada λ (B - bajo / B + alto)</label><input id="cfg-lam-minus" value="0.5"><input id="cfg-lam-plus" value="0.9"></div>
  </div>
  <div class="mini" style="margin-top:8px">
    <label>Servicio (C): exp o const</label>
    <input id="cfg-serv" value="exp">
  </div>
  <div class="mini" style="margin-top:8px">
    <label>Réplicas (r)</label><input id="cfg-r" value="10">
    <label>Clientes por corrida</label><input id="cfg-n" value="50000">
    <label>Aquecimiento</label><input id="cfg-w" value="1000">
  </div>
  <button class="accion" onclick="verConfig()">🔍 Ver config actual</button>
  <button class="sec" onclick="mostrarGraf('hist')">Ver gráfico de referencia</button>
  <div id="t-config"></div></div></section>
</main>

<script>
var datos={}, pestActual='resumen';
function gv(s){var e=document.querySelector(s);return e?e.value:''}
function gvC(s){var e=document.querySelector(s);return e?e.checked:false}
function esc(x){return String(x==null?'—':x).replace(/&/g,'&amp;').replace(/</g,'&lt;')}

// estado en el encabezado
setInterval(function(){fetch('/api/estado').then(r=>r.json()).then(j=>{
  var c=document.querySelector('#cabeza');
  if(j.estado.corriendo){c.textContent='⏳ '+j.estado.script+': '+j.estado.progreso;c.style.fontWeight='700'}
  else{c.textContent='● listo';c.style.fontWeight='normal'}
}).catch(function(){})},1500);

// pestañas
document.querySelectorAll('#tabnav button').forEach(function(b){
  b.addEventListener('click',function(){
    document.querySelectorAll('#tabnav button').forEach(x=>x.classList.remove('act'));
    document.querySelectorAll('main section').forEach(x=>x.style.display='none');
    b.classList.add('act');pestActual=b.dataset.t;
    document.getElementById('v-'+b.dataset.t).style.display='block';
  });
});

function cargarEntradas(){
  fetch('/api/listar_archivos').then(r=>r.json()).then(j=>{
    var sel=document.querySelector('#entrada');sel.innerHTML='';
    j.archivos.forEach(function(a){var o=document.createElement('option');o.value=a;
      o.textContent=a.split('/').pop();if(a.endsWith('resultados_fatorial.csv'))o.selected=true;
      sel.appendChild(o);});
  });
}

function pintar(pest,res){
  var cont=document.querySelector('#t-'+pest);
  if(!res.ok){cont.innerHTML='<div class="alert err">⚠ '+esc(res.error)+'</div>';return}
  document.querySelector('#titulo').textContent=res.titulo+' — '+res.n+' filas';
  var head=res.tabla.columnas.map(c=>'<th>'+esc(c)+'</th>').join('');
  var body=res.tabla.filas.map(f=>'<tr>'+f.map((c,i)=>'<td'+(i?' class="num"':'')+'>'+esc(c)+'</td>').join('')+'</tr>').join('');
  cont.innerHTML='<table><thead><tr>'+head+'</tr></thead><tbody>'+body+'</tbody></table>';
  datos[pest]=res;
  document.querySelector('#ex-'+pest).innerHTML='<div class="export">'
   +['csv','xlsx','json','latex'].map(f=>'<button class="sec" onclick="exportar(\''+pest+'\',\''+f+'\')">⬇ exportar '+f+'</button>').join('')
   +'</div>';
}

function correr(cmd,extra){
  var e=Object.assign({cmd:cmd,entrada:gv('#entrada')},extra||{});
  fetch('/api/ejecutar?'+new URLSearchParams(e)).then(r=>r.json()).then(res=>pintar(cmd,res))
    .catch(function(e){document.querySelector('#t-'+cmd).innerHTML='<div class="alert err">⚠ red: '+esc(e)+'</div>'});
}

function exportar(pest,formato){
  var res=datos[pest];if(!res)return;
  var nombre=prompt('Nombre base del archivo (sin extensión):',pest);
  if(!nombre)return;
  fetch('/api/exportar',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({df:res.tabla,nombre:nombre,formato:formato})})
    .then(r=>r.json()).then(function(j){
      if(j.ok){var a=document.createElement('a');a.href=j.descarga;a.download='';a.click();
        alert('✔ '+j.mensaje)}
      else alert('❌ '+j.error);
    });
}
function descargarEntrada(){
  fetch('/api/entrada?entrada='+encodeURIComponent(gv('#entrada')))
    .then(r=>r.text()).then(function(t){
      var a=document.createElement('a');
      a.href=URL.createObjectURL(new Blob([t],{type:'text/csv'}));
      a.download=gv('#entrada').split('/').pop();a.click();
    });
}
function simular(script){
  fetch('/api/simular?script='+script).then(r=>r.json()).then(function(j){
    document.querySelector('#sim-estado').innerHTML=j.ok
      ?'<span class="tag">Lanzado: '+script+'</span>'
      :'<div class="alert err">⚠ '+esc(j.error)+'</div>'
  }).then(verLog);
}
function verLog(){
  fetch('/api/log').then(r=>r.json()).then(function(j){
    if(j.lineas.length){var l=document.querySelector('#sim-log');
      l.textContent=(l.textContent==='(log en vivo)'?'':l.textContent)+'\n'+j.lineas.join('\n');
      l.scrollTop=l.scrollHeight}
  });
}
function mostrarGraf(tipo){
  var img=document.querySelector('#img-graf');
  img.style.display='inline';img.src='/api/graficos?tipo='+tipo+'&entrada='+encodeURIComponent(gv('#entrada'));
}
function verConfig(){
  fetch('/api/config').then(r=>r.json()).then(function(j){
    var html='<table><thead><tr><th>Variable</th><th>Valor</th></tr></thead><tbody>';
    for(var k in j.config){html+='<tr><td>'+esc(k)+'</td><td>'+esc(j.config[k])+'</td></tr>'}
    html+='</tbody></table>';
    document.querySelector('#t-config').innerHTML='<div class="caja" style="margin-top:10px">'+html+'</div>';
  }).catch(function(e){document.querySelector('#t-config').innerHTML='<div class="alert err">⚠ '+esc(e)+'</div>';});
}
setInterval(verLog,1500);
cargarEntradas();
correr('resumen');
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()