from flask import render_template, request, redirect, url_for, session
from models.cliente import Cliente as ClienteModel
from models.cliente import Contacto as ContactoModel
from models.presupuesto import Presupuesto as PresupuestoModel
from models.presupuesto import Presupuesto_Partida
from models.atencion import PresupuestoContacto
from datetime import datetime
from utils.db import db
from flask import Blueprint

presupuestos = Blueprint("presupuestos", __name__)


class Presupuesto:
    def __init__(self, app):
        self.app = app
        self.contador_partidas = 1
        self.rutas()

    def calcular_totales(self, importe):
        # Inicializar las variables de sesión si no existen.
        # Recorremos la lista de claves ["mano_obra", "materiales", "subtotal", "iva", "total"]
        # y para cada clave, verificamos si existe en la sesión. Si no existe, la inicializamos a 0.0
        for clave in ["mano_obra", "materiales", "subtotal", "iva", "total"]:
            if clave not in session:
                session[clave] = 0.0

        # Sumar el importe al subtotal en la sesión.
        # Esto incrementa el valor de "subtotal" en la sesión por el valor de "importe"
        session["subtotal"] += importe

        # Calcular el IVA como el 8% del subtotal y almacenarlo en la sesión.
        # Esto calcula el 8% del "subtotal" y lo almacena en la variable de sesión "iva"
        session["iva"] = session["subtotal"] * 0.08

        # Calcular el total como la suma del subtotal y el IVA y almacenarlo en la sesión.
        # Esto suma el "subtotal" y el "iva" y almacena el resultado en la variable de sesión "total"
        session["total"] = session["subtotal"] + session["iva"]

        # Calcular la mano de obra como el 40% del subtotal y almacenarlo en la sesión.
        # Esto calcula el 40% del "subtotal" y lo almacena en la variable de sesión "mano_obra"
        session["mano_obra"] = session["subtotal"] * 0.4

        # Calcular los materiales como el 60% del subtotal y almacenarlo en la sesión.
        # Esto calcula el 60% del "subtotal" y lo almacena en la variable de sesión "materiales"
        session["materiales"] = session["subtotal"] * 0.6

    def agregar_partidas(self, descripcion, cantidad, precio, importe, material):
        partidas_nueva = session["partidas"]
        partidas_nueva.append(
            {
                "partida": self.contador_partidas,
                "descripcion": descripcion,
                "cantidad": cantidad,
                "precio": precio,
                "importe": importe,
                "material": material,
                "subtotal": session["subtotal"],
                "iva": session["iva"],
                "total": session["total"],
                "mano_obra": session["mano_obra"],
                "materiales": session["materiales"],
            }
        )
        session["partidas"] = partidas_nueva.copy()
        self.contador_partidas += 1

    def recepcion_datos(self):
        fecha = datetime.now()
        if "partidas" not in session:
            session["partidas"] = []
        descripcion = request.form.get("descripcion")
        descripcion = descripcion.upper()
        cantidad = request.form.get("cantidad")
        precio = request.form.get("precio")
        importe = float(request.form.get("importe"))
        material = request.form.get("material")
        material = material.upper()
        cliente_id = request.form.get("cliente_id")
        return fecha, descripcion, cantidad, precio, importe, material, cliente_id

    def index(self):
        listar_clientes = ClienteModel.query.all()
        if request.method == "POST":
            (
                fecha,
                descripcion,
                cantidad,
                precio,
                importe,
                material,
                cliente_id,
            ) = self.recepcion_datos()
            self.calcular_totales(importe)
            self.agregar_partidas(descripcion, cantidad, precio, importe, material)
            self.guardar_partida(fecha, cliente_id)
            return redirect(url_for("index"))

        id_presupuesto = session.get("id_presupuesto")
        presupuesto, partidas = (
            self.obtener_datos_presupuesto(id_presupuesto)
            if id_presupuesto
            else (None, [])
        )
        cliente_id = presupuesto.cliente_id if presupuesto else None
        # llamar a la funcion mostrar_contactos
        contactos = self.mostrar_contactos(cliente_id)
        return render_template(
            "index.html",
            partidas=session.get("partidas", []),
            listar_clientes=listar_clientes,
            presupuesto=presupuesto,
            partidas_db=partidas,
            cliente_id=cliente_id,
            contactos=contactos,
        )

    def crear_presupuesto(
        self, fecha, cliente_id, mano_obra, materiales, subtotal, iva, total
    ):
        presupuesto = PresupuestoModel(
            fecha, cliente_id, mano_obra, materiales, subtotal, iva, total
        )
        db.session.add(presupuesto)
        db.session.flush()
        return presupuesto

    def actualizar_presupuesto(
        self, presupuesto, mano_obra, materiales, subtotal, iva, total
    ):
        presupuesto.mano_obra = mano_obra
        presupuesto.materiales = materiales
        presupuesto.subtotal = subtotal
        presupuesto.iva = iva
        presupuesto.total = total

    def obtener_ultimo_numero_partida(self, presupuesto_id):
        ultima_partida = (
            Presupuesto_Partida.query.filter_by(presupuesto_id=presupuesto_id)
            .order_by(Presupuesto_Partida.partida.desc())
            .first()
        )
        if ultima_partida is None:
            return 0
        else:
            return ultima_partida.partida

    def agregar_partida(self, presupuesto_id, partida):
        partida["partida"] = self.obtener_ultimo_numero_partida(presupuesto_id) + 1
        nueva_partida = Presupuesto_Partida(
            presupuesto_id=presupuesto_id,
            partida=partida["partida"],
            descripcion=partida["descripcion"],
            cantidad=partida["cantidad"],
            precio=partida["precio"],
            importe=partida["importe"],
            material=partida["material"],
        )
        db.session.add(nueva_partida)
        db.session.commit()
        self.recalcular_totales(presupuesto_id)

    def guardar_partida(self, fecha, cliente_id):
        mano_obra = session.get("mano_obra", 0.0)
        materiales = session.get("materiales", 0.0)
        subtotal = session.get("subtotal", 0.0)
        iva = session.get("iva", 0.0)
        total = session.get("total", 0.0)

        if "id_presupuesto" in session:
            presupuesto = PresupuestoModel.query.get(session["id_presupuesto"])
            if presupuesto is None:
                presupuesto = self.crear_presupuesto(
                    fecha, cliente_id, mano_obra, materiales, subtotal, iva, total
                )
                session["id_presupuesto"] = presupuesto.id_presupuesto
            else:
                self.actualizar_presupuesto(
                    presupuesto, mano_obra, materiales, subtotal, iva, total
                )
        else:
            presupuesto = self.crear_presupuesto(
                fecha, cliente_id, mano_obra, materiales, subtotal, iva, total
            )
            session["id_presupuesto"] = presupuesto.id_presupuesto

        for partida in session.get("partidas", []):
            self.agregar_partida(session.get("id_presupuesto", None), partida)

        db.session.commit()
        session["partidas"] = []
        return presupuesto.id_presupuesto

    def obtener_datos_presupuesto(self, id_presupuesto):
        presupuesto = PresupuestoModel.query.get(id_presupuesto)
        partidas = Presupuesto_Partida.query.filter_by(
            presupuesto_id=id_presupuesto
        ).all()
        return presupuesto, partidas

    def agregar_partida_presupuesto(self, presupuesto_id):
        # Obtener los datos del formulario
        descripcion = request.form.get("descripcion")
        descripcion = descripcion.upper()
        cantidad = request.form.get("cantidad")
        precio = request.form.get("precio")
        importe = request.form.get("importe")
        material = request.form.get("material")
        material = material.upper()

        ultima_partida = self.obtener_ultimo_numero_partida(presupuesto_id)
        nueva_partida_numero = ultima_partida + 1
        # Crear una nueva instancia de Presupuesto_Partida
        nueva_partida = Presupuesto_Partida(
            presupuesto_id=presupuesto_id,
            partida=nueva_partida_numero,
            descripcion=descripcion,
            cantidad=cantidad,
            precio=precio,
            importe=importe,
            material=material,
        )

        # Agregar la nueva partida a la base de datos
        db.session.add(nueva_partida)
        db.session.commit()

        # recalcula los totales
        self.recalcular_totales(presupuesto_id)

        # guardar los cambios despues de recalcular los totales
        db.session.commit()

        # Redirigir al usuario a la página del presupuesto
        return redirect(url_for("consultar_presupuesto", id_presupuesto=presupuesto_id))

    def editar_partida(self, id_partida):
        partida = Presupuesto_Partida.query.get(id_partida)
        if partida is None:
            print("No se econtró la partida")
            return redirect(url_for("index"))

        if request.method == "POST":
            partida.descripcion = request.form.get("descripcion")
            partida.descripcion = partida.descripcion.upper()
            partida.cantidad = request.form.get("cantidad")
            partida.precio = request.form.get("precio")
            # SOLUCION TEMPORAL. SEGUIR INVESTIGANDO COMO HACER CALCULO DE IMPORTE
            # DIRECTAMENTE EN EL MODAL
            importe = float(partida.cantidad) * float(partida.precio)
            partida.importe = importe
            partida.material = request.form.get("material")
            partida.material = partida.material.upper()

            presupuesto = partida.presupuesto

            presupuesto.cliente_id = request.form.get("cliente_id")

            db.session.commit()

            self.recalcular_totales(presupuesto.id_presupuesto)

            nuevo_presupuesto = "id_presupuesto" in session
            if nuevo_presupuesto:
                return redirect(url_for("index"))
            else:
                return redirect(
                    url_for(
                        "consultar_presupuesto",
                        id_presupuesto=presupuesto.id_presupuesto,
                    )
                )
        return render_template("form_edicion.html")

    def recalcular_totales(self, presupuesto_id):
        presupuesto = PresupuestoModel.query.get(presupuesto_id)

        presupuesto.subtotal = sum(
            p.importe
            for p in Presupuesto_Partida.query.filter_by(
                presupuesto_id=presupuesto.id_presupuesto
            )
        )
        presupuesto.mano_obra = float(presupuesto.subtotal) * 0.4
        presupuesto.materiales = float(presupuesto.subtotal) * 0.6
        presupuesto.iva = float(presupuesto.subtotal) * 0.08
        presupuesto.total = float(presupuesto.subtotal) + presupuesto.iva
        db.session.commit()

    def mostrar_contactos(self, id_cliente):
        cliente = ClienteModel.query.get(id_cliente)
        if cliente is None:
            print("No se econtró el cliente")
            return []
        contactos = cliente.contactos
        return contactos

    def presupuesto_contactos(self):
        listar_clientes = ClienteModel.query.all()
        id_cliente = request.form.get("cliente")
        if id_cliente:
            cliente = ClienteModel.query.get(id_cliente)
            if cliente is None:
                print("No se encontró el cliente")
                return render_template(
                    "consulta_contacto.html",
                    listar_clientes=listar_clientes,
                    listar_contactos=[],
                )
            contactos = cliente.contactos
            return render_template(
                "consulta_contacto.html",
                listar_clientes=listar_clientes,
                listar_contactos=contactos,
            )
        else:
            return render_template(
                "consulta_contacto.html",
                listar_clientes=listar_clientes,
                listar_contactos=[],
            )

    def atencion(self):
        id_presupuesto = session.get("id_presupuesto")
        contacto_ids = request.form.getlist("contacto_id")
        mensaje = request.form.get("mensaje_correo")
        print(mensaje)
        print(contacto_ids)

        for id_contacto in contacto_ids:
            # Comprueba si el contacto ya está asociado al presupuesto
            existe = (
                db.session.query(PresupuestoContacto)
                .filter_by(presupuesto_id=id_presupuesto, contacto_id=id_contacto)
                .first()
            )

            # Si el contacto no está asociado al presupuesto, lo agrega
            if not existe:
                presupuesto_contacto = PresupuestoContacto(
                    presupuesto_id=id_presupuesto,
                    contacto_id=id_contacto,
                    mensaje=mensaje,
                )
                db.session.add(presupuesto_contacto)

        db.session.commit()

        return redirect(url_for("generar_pdf", presupuesto_id=id_presupuesto))

    def obtener_contactos_presupuesto(self, id_presupuesto):
        presupuesto_contactos = PresupuestoContacto.query.filter_by(presupuesto_id=id_presupuesto).all()
        contactos_asignados = [pc.contacto_id for pc in presupuesto_contactos]
        print (contactos_asignados)
        return contactos_asignados

    def consulta_presupuesto_contacto(self):
        listar_clientes = ClienteModel.query.all()
        id_contacto = request.form.get("contacto")
        contacto = ContactoModel.query.get(id_contacto)
        presupuestos_contacto = PresupuestoContacto.query.filter_by(
            contacto_id=id_contacto
        ).all()
        presupuestos = [pc.presupuesto for pc in presupuestos_contacto]
        return render_template(
            "consulta_contacto.html",
            presupuestos=presupuestos,
            listar_clientes=listar_clientes,
            contacto=contacto,
        )

    def consultar_presupuesto(self, id_presupuesto):
        listar_clientes = ClienteModel.query.all()
        presupuesto, partidas = self.obtener_datos_presupuesto(id_presupuesto)
        cliente_id = presupuesto.cliente_id if presupuesto else None
        # llamar a la funcion mostrar_contactos
        contactos = self.mostrar_contactos(cliente_id)

        # obtener los contactos asignados al presupuesto
        contactos_asignados = self.obtener_contactos_presupuesto(id_presupuesto)

        session["id_presupuesto"] = id_presupuesto

        return render_template(
            "consultar_presupuesto.html",
            listar_clientes=listar_clientes,
            presupuesto=presupuesto,
            partidas_db=partidas,
            cliente_id=cliente_id,
            contactos=contactos,
            contactos_asignados=contactos_asignados,
        )

    def consultas(self):
        page = request.args.get("page", 1, type=int)
        PER_PAGE = 50
        query = PresupuestoModel.query
        fecha_busqueda, query = self.consultasPorFecha(query)
        total_presupuestos = query.count()
        total_pages = (total_presupuestos - 1) // PER_PAGE + 1
        presupuestos = query.paginate(page=page, per_page=PER_PAGE, error_out=False)

        return render_template(
            "consultas.html",
            presupuestos=presupuestos,
            total_pages=total_pages,
            fecha_busqueda=fecha_busqueda,
        )

    def consultasPorFecha(self, query):
        fecha_busqueda = request.args.get("fecha_busqueda")
        if fecha_busqueda:
            year, month = map(int, fecha_busqueda.split("-"))
            fecha_inicio = datetime(year, month, 1)
            if month == 12:
                fecha_fin = datetime(year + 1, 1, 1)
            else:
                fecha_fin = datetime(year, month + 1, 1)
            query = query.filter(
                PresupuestoModel.fecha >= fecha_inicio,
                PresupuestoModel.fecha < fecha_fin,
            )

        return fecha_busqueda, query

    def consulta_cliente(self):
        listar_clientes = ClienteModel.query.all()
        id_cliente = request.form.get("cliente")
        presupuestos = PresupuestoModel.query.filter_by(cliente_id=id_cliente).all()
        cliente_seleccionado = ClienteModel.query.get(id_cliente)
        nombre_cliente = cliente_seleccionado.nombre if cliente_seleccionado else ""
        print(id_cliente)
        return render_template(
            "consulta_cliente.html",
            presupuestos=presupuestos,
            listar_clientes=listar_clientes,
            nombre_cliente=nombre_cliente,
        )

    def cerrar(self):
        session.clear()
        self.contador_partidas = 1
        print("Cerraste el sistema")
        return redirect(url_for("index"))

    def borrar_partida(self, id_partida):
        partida = Presupuesto_Partida.query.get(id_partida)

        # Comprueba si la partida existe
        if partida is None:
            print("No se econtró la partida")
            return redirect(url_for("index"))
        presupuesto_id = partida.presupuesto_id
        db.session.delete(partida)
        db.session.commit()
        self.reordenar_partidas(presupuesto_id)
        self.recalcular_totales(presupuesto_id)

        nuevo_presupuesto = "id_presupuesto" in session
        if nuevo_presupuesto:
            return redirect(url_for("index"))
        else:
            return redirect(
                url_for("consultar_presupuesto", id_presupuesto=presupuesto_id)
            )

    def reordenar_partidas(self, presupuesto_id):
        partidas = Presupuesto_Partida.query.filter_by(
            presupuesto_id=presupuesto_id
        ).all()
        for i, partida in enumerate(partidas, start=1):
            partida.partida = i
        db.session.commit()

    def rutas(self):
        self.app.add_url_rule("/", "index", self.index, methods=["GET", "POST"])

        self.app.add_url_rule("/cerrar", "cerrar", self.cerrar)

        self.app.add_url_rule(
            "/agregar_partida_presupuesto/<int:presupuesto_id>",
            "agregar_partida_presupuesto",
            self.agregar_partida_presupuesto,
            methods=["POST"],
        )

        self.app.add_url_rule(
            "/guardar_partida",
            "guardar_partida",
            self.guardar_partida,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/editar_partida/<int:id_partida>",
            "editar_partida",
            self.editar_partida,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/presupuesto_contactos",
            "presupuesto_contactos",
            self.presupuesto_contactos,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/consulta_presupuesto_contacto",
            "consulta_presupuesto_contacto",
            self.consulta_presupuesto_contacto,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/atencion", "atencion", self.atencion, methods=["GET", "POST"]
        )

        self.app.add_url_rule(
            "/consultas", "consultas", self.consultas, methods=["GET", "POST"]
        )

        self.app.add_url_rule(
            "/consultar_presupuesto/<int:id_presupuesto>",
            "consultar_presupuesto",
            self.consultar_presupuesto,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/consulta_cliente",
            "consulta_cliente",
            self.consulta_cliente,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/borrar_partida/<int:id_partida>",
            "borrar_partida",
            self.borrar_partida,
            methods=["GET"],
        )
