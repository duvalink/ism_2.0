from utils.db import db
from models.presupuesto import Presupuesto
from models.cliente import Contacto


class PresupuestoContacto(db.Model):
    id_presupuesto_contacto = db.Column(db.Integer, primary_key=True)
    presupuesto_id = db.Column(db.Integer, db.ForeignKey("presupuesto.id_presupuesto"))
    contacto_id = db.Column(db.Integer, db.ForeignKey("contacto.id_contacto"))
    mensaje = db.Column(db.String(1000))
    presupuesto = db.relationship(Presupuesto, backref="presupuesto_contacto")
    contacto = db.relationship(Contacto, backref="presupuesto_contacto")

    def __init__(self, presupuesto_id, contacto_id, mensaje):
        self.presupuesto_id = presupuesto_id
        self.contacto_id = contacto_id
        self.mensaje = mensaje
