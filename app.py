import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False   # muestra tildes tal cual en el JSON

# Dirección del servicio vecino, inyectada por variable de entorno (configuración fuera del código).
# En Compose valdrá http://multiplicador:5000, donde "multiplicador" es el NOMBRE DEL SERVICIO.
# El valor por defecto sirve para correr ambos servicios a mano en tu máquina.
MULTIPLICADOR_URL = os.getenv("MULTIPLICADOR_URL", "http://127.0.0.1:5000")
TIMEOUT = float(os.getenv("TIMEOUT_SEGUNDOS", "3"))


class ErrorServicio(Exception):
    def __init__(self, mensaje, status):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status


@app.errorhandler(ErrorServicio)
def manejar_error(e):
    return jsonify(error=e.mensaje), e.status

@app.route('/multiplicar', methods=['GET'])
def multiplicar():
    """Cliente HTTP: delega la multiplicación en el microservicio 'multiplicador'."""
    try:
        a = float(request.args.get('a'))
        b = float(request.args.get('b'))
        resp = requests.get(
            f"{MULTIPLICADOR_URL}/multiplicar",
            params={"a": a, "b": b},
            timeout=TIMEOUT,          # nunca llamar a otro servicio sin timeout
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        # Degradación controlada: si el vecino cae, esta API responde 503 y NO se cae.
        raise ErrorServicio(f"multiplicador no disponible: {e}", 503)

@app.get("/health")
def health():
    return jsonify(estado="ok")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
