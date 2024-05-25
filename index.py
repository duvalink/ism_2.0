from app import create_app
from routes.presupuestos import Presupuesto
from routes.clientes import ControladorClientes
from routes.contactos import ControladorContactos
from routes.enviar_correo import Correo
from routes.generar_pdf import Pdf
from routes.remision import Pdf as Remision
from routes.orden_produccion import Pdf as ordenProduccion
from utils.db import db
import webbrowser

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
orden_produccion = ordenProduccion(app)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

    # webbrowser.open_new("http://localhost:5000")
    # app.run(debug=True)
