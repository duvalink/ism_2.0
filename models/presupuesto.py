from utils.db import db
from models.cliente import Cliente


class Presupuesto(db.Model):
    id_presupuesto = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date)
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id_cliente"))
    materiales = db.Column(db.Float(10, 2))
    mano_obra = db.Column(db.Float(10, 2))
    subtotal = db.Column(db.Float(10, 2))
    iva = db.Column(db.Float(10, 2))
    total = db.Column(db.Float(10, 2))
    cliente = db.relationship(Cliente, backref="presupuestos")

    def __init__(self, fecha, cliente_id, materiales, mano_obra, subtotal, iva, total):
        self.fecha = fecha
        self.cliente_id = cliente_id
        self.materiales = materiales
        self.mano_obra = mano_obra
        self.subtotal = subtotal
        self.iva = iva
        self.total = total


class Presupuesto_Partida(db.Model):
    id_partida = db.Column(db.Integer, primary_key=True)
    presupuesto_id = db.Column(db.Integer, db.ForeignKey("presupuesto.id_presupuesto"))
    partida = db.Column(db.Integer)
    descripcion = db.Column(db.String(1000))
    cantidad = db.Column(db.Integer)
    precio = db.Column(db.Float(10, 2))
    importe = db.Column(db.Float(10, 2))
    material = db.Column(db.String(100))
    presupuesto = db.relationship("Presupuesto", backref="presupuesto_partida")

    def __init__(
        self, presupuesto_id, partida, descripcion, cantidad, precio, importe, material):
        self.presupuesto_id = presupuesto_id
        self.partida = partida
        self.descripcion = descripcion
        self.cantidad = cantidad
        self.precio = precio
        self.importe = importe
        self.material = material

class Presupuesto_Remision(db.model):
    id_remision = db.Column(db.Integer, primary_key=True)
    presupuesto_id=db>column(db.Integer, db.ForeignKey("presupuesto.id_presupuesto"))
    fecha = db.Column(db.Date)

