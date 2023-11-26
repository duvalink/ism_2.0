from flask import render_template, request, redirect, url_for, Blueprint
from models.cliente import Contacto as ContactoModel
from models.cliente import Cliente as ClienteModel
from utils.db import db

contactos = Blueprint("contactos", __name__)


class ControladorContactos:
    def __init__(self, app):
        self.app = app
        self.rutas()

    def crear_contacto(self):
        listar_clientes = ClienteModel.query.all()
        listar_contactos = ContactoModel.query.all()
        if request.method == "POST":
            contacto = request.form["nombre_contacto"]
            correo = request.form["correo"]
            cliente_id = int(request.form["cliente"])
            print(cliente_id)
            self.agregar_contacto(contacto, correo, int(cliente_id))
            return redirect(url_for("crear_contacto"))
        return render_template(
            "contacto.html",
            listar_clientes=listar_clientes,
            listar_contactos=listar_contactos,
        )

    def agregar_contacto(self, contacto, correo, cliente_id):
        nuevo_contacto = ContactoModel(contacto, correo, int(cliente_id))
        db.session.add(nuevo_contacto)
        db.session.commit()

    def editar_contacto(self, id_contacto):
        listar_clientes = ClienteModel.query.all()
        if request.method == "POST":
            contacto = ContactoModel.query.get(id_contacto)
            contacto.contacto = request.form["nombre_contacto"]
            contacto.correo = request.form["correo"]
            contacto.cliente_id = request.form["cliente"]
            print(request.form["cliente"])
            db.session.commit()
            return redirect(url_for("crear_contacto"))
        contacto = ContactoModel.query.get(id_contacto)
        return render_template("modal_contacto.html", listar_clientes=listar_clientes)

    def borrar_contacto(self, id_contacto):
        contacto = ContactoModel.query.get(id_contacto)
        db.session.delete(contacto)
        db.session.commit()
        return redirect(url_for("crear_contacto"))

    def rutas(self):
        self.app.add_url_rule(
            "/crear_contacto",
            "crear_contacto",
            self.crear_contacto,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/editar_contacto/<int:id_contacto>",
            "editar_contacto",
            self.editar_contacto,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/borrar_contacto/<int:id_contacto>",
            "borrar_contacto",
            self.borrar_contacto,
            methods=["GET"],
        )
