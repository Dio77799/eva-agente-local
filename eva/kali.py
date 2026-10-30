"""Control de la VM de Kali (VirtualBox) y cuaderno de máquinas de Hack The Box."""
import re
import subprocess
from datetime import date

from .comun import DATOS, bitacora, config
from . import tareas

HTB = DATOS / "htb"


def _vbox(*args):
    k = config()["kali"]
    r = subprocess.run([k["vboxmanage"], *args], capture_output=True, text=True,
                       encoding="utf-8", errors="ignore")
    return r.returncode, (r.stdout + r.stderr).strip()


def estado():
    vm = config()["kali"]["vm"]
    _, encendidas = _vbox("list", "runningvms")
    _, info = _vbox("showvminfo", vm, "--machinereadable")
    snaps = re.findall(r'^SnapshotName[-\d]*="(.+)"', info, re.M)
    return {"vm": vm, "encendida": f'"{vm}"' in encendidas, "snapshots": snaps}


def encender(sin_ventana=False):
    vm = config()["kali"]["vm"]
    if estado()["encendida"]:
        return "La VM ya está encendida."
    codigo, salida = _vbox("startvm", vm, "--type", "headless" if sin_ventana else "gui")
    bitacora("kali_encender", ok=codigo == 0)
    return salida


def apagar():
    """Apagado limpio (como presionar el botón de encendido), no forzado."""
    codigo, salida = _vbox("controlvm", config()["kali"]["vm"], "acpipowerbutton")
    bitacora("kali_apagar", ok=codigo == 0)
    return salida or "Señal de apagado enviada."


def snapshot(nombre=None):
    nombre = nombre or f"antes-htb-{date.today()}"
    codigo, salida = _vbox("snapshot", config()["kali"]["vm"], "take", nombre, "--live")
    bitacora("kali_snapshot", nombre=nombre, ok=codigo == 0)
    return salida


def guia_vpn():
    k = config()["kali"]
    return f"""
GUÍA RÁPIDA: conectarte a la VPN de Hack The Box
-------------------------------------------------
1. Enciende la VM:            python eva.py kali encender
2. Dentro de Kali abre una terminal y ve a donde está el .ovpn:
       cd {k['ovpn_dir']}
       ls *.ovpn
   (Tienes dos: '{k['ovpn']}' y una copia '(1)'. Usa UNA sola: la más
    reciente que descargaste de HTB. Si te da error, vuelve a bajarla.)
3. Conecta (deja esa terminal abierta, si la cierras se cae la VPN):
       sudo openvpn {k['ovpn']}
   Espera a ver: "Initialization Sequence Completed".
4. En OTRA terminal comprueba la interfaz tun0 y tu IP de HTB:
       ip a show tun0
5. En la web de HTB pulsa "Spawn Machine", copia la IP y prueba:
       ping -c 3 <IP_DE_LA_MAQUINA>
6. Para desconectar: Ctrl+C en la terminal de openvpn.

Problemas típicos:
  - "Cannot resolve host" -> la VM no tiene internet (revisa red NAT/puente).
  - Ya hay otra VPN activa -> sudo killall openvpn y reintenta.
  - Dos conexiones a la vez -> HTB solo permite una por usuario.
Consejo: antes de empezar, `python eva.py kali snapshot` para poder volver atrás.
"""


def nueva_maquina(nombre, ip="", dificultad="", sistema=""):
    HTB.mkdir(exist_ok=True)
    slug = re.sub(r"[^a-z0-9_-]", "-", nombre.lower())
    archivo = HTB / f"{slug}.md"
    if not archivo.exists():
        archivo.write_text(f"""# {nombre} (Hack The Box)

- Fecha inicio: {date.today()}
- IP: {ip}
- Dificultad: {dificultad}
- Sistema: {sistema}
- Estado HTB: activa  <!-- cambia a 'retirada' cuando HTB la retire: solo entonces se publica -->

## 1. Reconocimiento
```
nmap -sC -sV -oN nmap.txt {ip or '<IP>'}
```

## 2. Enumeración

## 3. Acceso inicial (foothold)

## 4. Escalada de privilegios

## 5. Flags
- user: (no la publiques)
- root: (no la publiques)

## 6. Lecciones aprendidas / qué contaría en un post
""", encoding="utf-8")
    tareas.agregar(f"HTB: resolver {nombre}", "htb", 2, notas=str(archivo))
    bitacora("htb_nueva", maquina=nombre)
    return archivo


def maquinas():
    if not HTB.exists():
        return []
    salida = []
    for f in sorted(HTB.glob("*.md")):
        m = re.search(r"Estado HTB:\s*(\w+)", f.read_text(encoding="utf-8"))
        salida.append({"maquina": f.stem, "estado": m.group(1) if m else "?", "archivo": str(f)})
    return salida
