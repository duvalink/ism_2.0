from utils.db import db


class Cliente(db.Model):
    id_cliente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    direccion = db.Column(db.String(80))
    cp = db.Column(db.String(20))
    ciudad = db.Column(db.String(50))
    telefono = db.Column(db.String(20))
    rfc = db.Column(db.String(15))

    def __init__(self, nombre, direccion, cp, ciudad, telefono, rfc):
        self.nombre = nombre
        self.direccion = direccion
        self.cp = cp
        self.ciudad = ciudad
        self.telefono = telefono
        self.rfc = rfc

class Contacto(db.Model):
    id_contacto = db.Column(db.Integer, primary_key=True)
    contacto = db.Column(db.String(50))
    correo = db.Column(db.String(50))
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id_cliente"))
    cliente = db.relationship("Cliente", backref="contactos")
    # En caso de que queramos que en la tabla, aparezca el nombre del cliente, en lugar
    # del cliente_id (id_cliente), en nuestra tabla usamos la siguiente sintaxis:
    # {{nombre_variable.cliente.nombre}}

    def __init__(self, contacto, correo, cliente_id):
        self.contacto = contacto
        self.correo = correo
        self.cliente_id = cliente_id
