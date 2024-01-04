from app import create_app
from routes.presupuestos import Presupuesto
from routes.clientes import ControladorClientes
from routes.contactos import ControladorContactos
from routes.enviar_correo import Correo
from routes.generar_pdf import Pdf
from routes.remision import Pdf as Remision
from utils.db import db

app = create_app()

with app.app_context():
    db.init_app(app)
    # db.drop_all()
    db.create_all()


presupuesto = Presupuesto(app)
cliente = ControladorClientes(app)
contacto = ControladorContactos(app)
correo = Correo(app)
pdf = Pdf(app)
remision = Remision(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
