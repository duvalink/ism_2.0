from flask import render_template, request, redirect, url_for, session, Blueprint
from models.cliente import Cliente as ClienteModel
from utils.db import db

clientes = Blueprint("clientes", __name__)


class ControladorClientes:
    def __init__(self, app):
        self.app = app
        self.rutas()

    def crear_cliente(self):
        listar_clientes = ClienteModel.query.all()
        if request.method == "POST":
            nombre = request.form["nombre"]
            direccion = request.form["direccion"]
            cp = request.form["cp"]
            ciudad = request.form["ciudad"]
            telefono = request.form["telefono"]
            rfc = request.form["rfc"]
            self.agregar_cliente(nombre, direccion, cp, ciudad, telefono, rfc)
            return redirect(url_for("crear_cliente"))
        return render_template("cliente.html", listar_clientes=listar_clientes)

    def agregar_cliente(self, nombre, direccion, cp, ciudad, telefono, rfc):
        nuevo_cliente = ClienteModel(nombre, direccion, cp, ciudad, telefono, rfc)
        db.session.add(nuevo_cliente)
        db.session.commit()

    def editar_cliente(self, id_cliente):
        if request.method == "POST":
            cliente = ClienteModel.query.get(id_cliente)
            cliente.nombre = request.form["nombre"]
            cliente.direccion = request.form["direccion"]
            cliente.cp = request.form["cp"]
            cliente.ciudad = request.form["ciudad"]
            cliente.telefono = request.form["telefono"]
            cliente.rfc = request.form["rfc"]
            db.session.commit()
            return redirect(url_for("crear_cliente"))
        return render_template("modal_cliente.html")

    def borrar_cliente(self, id_cliente):
        cliente = ClienteModel.query.get(id_cliente)
        db.session.delete(cliente)
        db.session.commit()
        return redirect(url_for("crear_cliente"))

    def rutas(self):
        self.app.add_url_rule(
            "/crear_cliente",
            "crear_cliente",
            self.crear_cliente,
            methods=["GET", "POST"],
        )
        self.app.add_url_rule(
            "/editar_cliente/<int:id_cliente>",
            "editar_cliente",
            self.editar_cliente,
            methods=["GET", "POST"],
        )
        self.app.add_url_rule(
            "/borrar_cliente/<int:id_cliente>",
            "borrar_cliente",
            self.borrar_cliente,
            methods=["GET"],
        )
