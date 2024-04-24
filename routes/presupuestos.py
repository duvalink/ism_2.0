from flask import render_template, request, redirect, url_for, session
from models.cliente import Cliente as ClienteModel
from models.cliente import Contacto as ContactoModel
from models.presupuesto import Presupuesto as PresupuestoModel
from models.presupuesto import Presupuesto_Partida
from models.atencion import PresupuestoContacto
from datetime import datetime
from utils.db import db
from flask import Blueprint
import keyboard

presupuestos = Blueprint("presupuestos", __name__)


class Presupuesto:
    def __init__(self, app):
        self.app = app
        self.contador_partidas = 1
        self.rutas()

    def calcular_totales(self, importe, iva_porcentaje):
        """
        Calcula los totales para la sesión actual.

        Esta función toma un importe, lo suma al subtotal de la sesión, y luego calcula el IVA, el total, la mano de obra y los materiales basándose en el subtotal.

        El IVA se calcula como el 8% del subtotal, el total se calcula como la suma del subtotal y el IVA, la mano de obra se calcula como el 40% del subtotal, y los materiales se calculan como el 60% del subtotal.

        Si alguna de las claves no está en la sesión, la función la inicializa a 0.0.

        Args:
            importe (float): El importe a sumar al subtotal.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> presupuestos.calcular_totales(100.0)
        """
        iva_porcentaje = float(iva_porcentaje)
        for clave in ["mano_obra", "materiales", "subtotal", "iva", "total"]:
            if clave not in session:
                session[clave] = 0.0
        session["subtotal"] += importe

        session["iva"] = session["subtotal"] * iva_porcentaje

        session["total"] = session["subtotal"] + session["iva"]

        session["mano_obra"] = session["subtotal"] * 0.4

        session["materiales"] = session["subtotal"] * 0.6

    def agregar_partidas(self, descripcion, cantidad, precio, importe, material):
        """
        Agrega una nueva partida a la lista de partidas de la sesión actual.

        Esta función toma varios valores, crea un nuevo diccionario con esos valores y los valores actuales de la sesión, y lo agrega a la lista de partidas de la sesión.

        Los valores que se utilizan para crear la partida son la descripción, la cantidad, el precio, el importe, el material, el subtotal, el IVA, el total, la mano de obra y los materiales.

        Después de agregar la partida a la lista, la función actualiza la lista de partidas de la sesión con la nueva lista y aumenta el contador de partidas.

        Args:
            descripcion (str): La descripción de la nueva partida.
            cantidad (float): La cantidad de la nueva partida.
            precio (float): El precio de la nueva partida.
            importe (float): El importe de la nueva partida.
            material (str): El material de la nueva partida.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> presupuestos.agregar_partidas("DESCRIPCION", 1, 100.0, 100.0, "MATERIAL")
        """
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
        """
        Recibe los datos de una nueva partida desde el formulario de la página de inicio.

        Esta función obtiene los valores de los campos del formulario de la página de inicio, los procesa si es necesario, y los devuelve.

        Los valores que se obtienen son la fecha actual, la descripción, la cantidad, el precio, el importe, el material y el ID del cliente.

        Si la descripción o el material están en minúsculas, la función los convierte a mayúsculas.

        Si la lista de partidas no está en la sesión, la función la inicializa.

        Returns:
            tuple: Un tuple que contiene la fecha, la descripción, la cantidad, el precio, el importe, el material y el ID del cliente.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> datos = presupuestos.recepcion_datos()
        """
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
        iva_porcentaje = float(request.form.get("iva_porcentaje")) / 100
        session["iva_porcentaje"] = iva_porcentaje

        return (
            fecha,
            descripcion,
            cantidad,
            precio,
            importe,
            material,
            cliente_id,
            iva_porcentaje,
        )

    def index(self):
        """
        Controlador para la página de inicio.

        Esta función se encarga de manejar las solicitudes GET y POST para la página de inicio.

        En una solicitud GET, la función obtiene una lista de todos los clientes y los datos del presupuesto y las partidas de la sesión actual, y renderiza la plantilla de la página de inicio con estos datos.

        En una solicitud POST, la función recibe los datos de una nueva partida, calcula los totales, agrega la partida a la lista de partidas de la sesión actual, guarda la partida en la base de datos, y redirige al usuario a la página de inicio.

        Returns:
            str: El HTML de la página de inicio.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> presupuestos.index()
        """
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
                iva_porcentaje,
            ) = self.recepcion_datos()
            self.calcular_totales(importe, iva_porcentaje)
            print("IVA PORCENTAJE: ", iva_porcentaje)
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
        """
        Crea un nuevo presupuesto y lo agrega a la base de datos.

        Esta función toma varios valores, crea un nuevo objeto de presupuesto con esos valores, y lo agrega a la base de datos.

        Los valores que se utilizan para crear el presupuesto son la fecha, el ID del cliente, la mano de obra, los materiales, el subtotal, el IVA y el total.

        Después de agregar el presupuesto a la base de datos, la función realiza un flush para obtener el ID del presupuesto.

        Finalmente, la función devuelve el objeto de presupuesto.

        Args:
            fecha (date): La fecha para el nuevo presupuesto.
            cliente_id (int): El ID del cliente para el nuevo presupuesto.
            mano_obra (float): El valor de la mano de obra para el nuevo presupuesto.
            materiales (float): El valor de los materiales para el nuevo presupuesto.
            subtotal (float): El subtotal para el nuevo presupuesto.
            iva (float): El valor del IVA para el nuevo presupuesto.
            total (float): El total para el nuevo presupuesto.

        Returns:
            PresupuestoModel: El objeto de presupuesto creado.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> nuevo_presupuesto = presupuestos.crear_presupuesto(date.today(), 1, 100.0, 200.0, 300.0, 30.0, 330.0)
        """
        presupuesto = PresupuestoModel(
            fecha, cliente_id, mano_obra, materiales, subtotal, iva, total
        )
        db.session.add(presupuesto)
        db.session.flush()
        return presupuesto

    def actualizar_presupuesto(
        self, presupuesto, mano_obra, materiales, subtotal, iva, total
    ):
        """
        Actualiza los valores de un presupuesto.

        Esta función toma un objeto de presupuesto y varios valores, y actualiza los valores del presupuesto con los valores proporcionados.

        Los valores que se actualizan son la mano de obra, los materiales, el subtotal, el IVA y el total.

        Args:
            presupuesto (PresupuestoModel): El objeto de presupuesto para actualizar.
            mano_obra (float): El nuevo valor para la mano de obra del presupuesto.
            materiales (float): El nuevo valor para los materiales del presupuesto.
            subtotal (float): El nuevo valor para el subtotal del presupuesto.
            iva (float): El nuevo valor para el IVA del presupuesto.
            total (float): El nuevo valor para el total del presupuesto.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> presupuesto = presupuestos.obtener_datos_presupuesto(1)[0]
        >>> presupuestos.actualizar_presupuesto(presupuesto, 100.0, 200.0, 300.0, 30.0, 330.0)
        """
        presupuesto.mano_obra = mano_obra
        presupuesto.materiales = materiales
        presupuesto.subtotal = subtotal
        presupuesto.iva = iva
        presupuesto.total = total

    def obtener_ultimo_numero_partida(self, presupuesto_id):
        """
        Obtiene el número de la última partida de un presupuesto.

        Esta función toma un ID de presupuesto y realiza una consulta a la base de datos para obtener la última partida del presupuesto.
        La consulta filtra las partidas por el ID del presupuesto, las ordena en orden descendente por el número de partida, y obtiene la primera partida.

        Si no se encuentra ninguna partida, la función devuelve 0.
        Si se encuentra una partida, la función devuelve el número de la partida.

        Args:
            presupuesto_id (int): El ID del presupuesto para obtener el número de la última partida.

        Returns:
            int: El número de la última partida, o 0 si no se encuentra ninguna partida.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> ultimo_numero_partida = presupuestos.obtener_ultimo_numero_partida(1)
        """
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
        """
        Agrega una nueva partida a un presupuesto.

        Esta función toma un ID de presupuesto y un diccionario de partida, y crea una nueva partida para el presupuesto.
        Primero, obtiene el número de la última partida del presupuesto y crea un nuevo número de partida incrementándolo en uno.
        Luego, crea una nueva instancia de Presupuesto_Partida con los datos de la partida y el nuevo número de partida,
        y la agrega a la base de datos.

        Después de confirmar los cambios en la base de datos, la función recalcula los totales del presupuesto.

        Args:
            presupuesto_id (int): El ID del presupuesto para agregar la partida.
            partida (dict): Un diccionario que contiene los datos de la partida.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> partida = {
        >>>     "descripcion": "Partida de prueba",
        >>>     "cantidad": 1,
        >>>     "precio": 100.0,
        >>>     "importe": 100.0,
        >>>     "material": "Material de prueba"
        >>> }
        >>> presupuestos.agregar_partida(1, partida)
        """
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
        self.recalcular_totales(presupuesto_id, session["iva_porcentaje"])

    def guardar_partida(self, fecha, cliente_id):
        """
        Guarda una partida en un presupuesto.

        Esta función toma una fecha y un ID de cliente, y recupera varios valores de la sesión, como la mano de obra, los materiales, el subtotal, el IVA y el total.

        Si la sesión contiene un ID de presupuesto, la función intenta obtener el presupuesto de la base de datos.
        Si no se encuentra el presupuesto, crea uno nuevo con los valores de la sesión y lo guarda en la base de datos.
        Si se encuentra el presupuesto, lo actualiza con los valores de la sesión.

        Si la sesión no contiene un ID de presupuesto, la función crea un nuevo presupuesto con los valores de la sesión y lo guarda en la base de datos.

        A continuación, para cada partida en la sesión, la función agrega la partida al presupuesto.

        Después de confirmar los cambios en la base de datos, la función vacía la lista de partidas en la sesión.

        Finalmente, devuelve el ID del presupuesto.

        Args:
            fecha (date): La fecha para el presupuesto.
            cliente_id (int): El ID del cliente para el presupuesto.

        Returns:
            int: El ID del presupuesto.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> id_presupuesto = presupuestos.guardar_partida(date.today(), 1)
        """
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
        """
        Obtiene los datos de un presupuesto y sus partidas.

        Esta función toma un ID de presupuesto y realiza dos consultas a la base de datos:
        una para obtener el presupuesto y otra para obtener todas las partidas asociadas a ese presupuesto.

        Finalmente, devuelve el presupuesto y las partidas como una tupla.

        Args:
            id_presupuesto (int): El ID del presupuesto para obtener los datos.

        Returns:
            tuple: Una tupla que contiene el presupuesto y las partidas.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> presupuesto, partidas = presupuestos.obtener_datos_presupuesto(1)
        """
        presupuesto = PresupuestoModel.query.get(id_presupuesto)
        partidas = Presupuesto_Partida.query.filter_by(
            presupuesto_id=id_presupuesto
        ).all()
        return presupuesto, partidas

    def agregar_partida_presupuesto(self, presupuesto_id):
        """
        Agrega una nueva partida a un presupuesto.

        Esta función toma un ID de presupuesto y los datos del formulario de la solicitud para crear una nueva partida.
        Primero, obtiene los datos del formulario y los convierte a mayúsculas si es necesario.
        Luego, obtiene el número de la última partida del presupuesto y crea un nuevo número de partida incrementándolo en uno.

        A continuación, crea una nueva instancia de Presupuesto_Partida con los datos del formulario y el nuevo número de partida,
        y la agrega a la base de datos.

        Después de confirmar los cambios en la base de datos, la función recalcula los totales del presupuesto y confirma los cambios de nuevo.

        Finalmente, redirige al usuario a la página de consulta del presupuesto.

        Args:
            presupuesto_id (int): El ID del presupuesto para agregar la partida.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> presupuestos.agregar_partida_presupuesto(1)
        """
        # Obtener los datos del formulario
        descripcion = request.form.get("descripcion")
        descripcion = descripcion.upper()
        cantidad = request.form.get("cantidad")
        precio = request.form.get("precio")
        importe = request.form.get("importe")
        material = request.form.get("material")
        material = material.upper()
        iva_porcentaje = float(request.form.get("iva_porcentaje")) / 100

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
        self.recalcular_totales(presupuesto_id, iva_porcentaje)

        # guardar los cambios despues de recalcular los totales
        db.session.commit()

        # Redirigir al usuario a la página del presupuesto
        return redirect(url_for("consultar_presupuesto", id_presupuesto=presupuesto_id))

    def editar_partida(self, id_partida):
        """
        Edita una partida de un presupuesto.

        Esta función toma un ID de partida y realiza una consulta a la base de datos para obtener la partida.
        Si no se encuentra la partida, la función imprime un mensaje de error y redirige al índice.

        Si se encuentra la partida y el método de la solicitud es POST, la función actualiza los campos de la partida con los valores del formulario de la solicitud.
        Luego, calcula el importe multiplicando la cantidad por el precio, y actualiza el campo de importe de la partida.

        A continuación, obtiene el presupuesto asociado a la partida y actualiza el ID del cliente con el valor del formulario de la solicitud.

        Después de confirmar los cambios en la base de datos, la función recalcula los totales del presupuesto.

        Finalmente, si la sesión contiene un ID de presupuesto, la función redirige al índice. Si no, redirige a la consulta del presupuesto.

        Args:
            id_partida (int): El ID de la partida para editar.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> presupuestos.editar_partida(1)
        """
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
            iva_porcentaje = float(request.form.get("iva_porcentaje")) / 100

            presupuesto = partida.presupuesto

            presupuesto.cliente_id = request.form.get("cliente_id")

            db.session.commit()

            self.recalcular_totales(presupuesto.id_presupuesto, iva_porcentaje)

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

    def recalcular_totales(self, presupuesto_id, iva_porcentaje):
        """
        Recalcula los totales para un presupuesto específico.

        Esta función toma un ID de presupuesto y realiza una consulta a la base de datos para obtener el presupuesto.
        Luego, recalcula el subtotal sumando los importes de todas las partidas asociadas al presupuesto.

        A continuación, calcula la mano de obra y los materiales como porcentajes del subtotal (40% y 60% respectivamente),
        y el IVA como el 8% del subtotal.

        Finalmente, calcula el total sumando el subtotal y el IVA, y confirma los cambios en la base de datos.

        Args:
            presupuesto_id (int): El ID del presupuesto para recalcular los totales.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> presupuestos.recalcular_totales(1)
        """
        presupuesto = PresupuestoModel.query.get(presupuesto_id)

        presupuesto.subtotal = sum(
            p.importe
            for p in Presupuesto_Partida.query.filter_by(
                presupuesto_id=presupuesto.id_presupuesto
            )
        )
        presupuesto.mano_obra = float(presupuesto.subtotal) * 0.4
        presupuesto.materiales = float(presupuesto.subtotal) * 0.6
        presupuesto.iva = float(presupuesto.subtotal) * iva_porcentaje
        presupuesto.total = float(presupuesto.subtotal) + presupuesto.iva
        db.session.commit()

    def mostrar_contactos(self, id_cliente):
        """
        Muestra los contactos asociados a un cliente específico.

        Esta función toma un ID de cliente y realiza una consulta a la base de datos para obtener el cliente.
        Si no se encuentra al cliente, la función imprime un mensaje de error y devuelve una lista vacía.

        Si se encuentra al cliente, la función obtiene los contactos del cliente y los devuelve.

        Args:
            id_cliente (int): El ID del cliente para obtener los contactos.

        Returns:
            list of ContactoModel: Una lista de los contactos asociados al cliente.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> contactos = presupuestos.mostrar_contactos(1)
        >>> print(contactos)
        [<ContactoModel 1>, <ContactoModel 2>, <ContactoModel 3>]
        """
        cliente = ClienteModel.query.get(id_cliente)
        if cliente is None:
            print("No se econtró el cliente")
            return []
        contactos = cliente.contactos
        return contactos

    def presupuesto_contactos(self):
        """
        Gestiona la consulta de contactos para un presupuesto.

        Esta función obtiene una lista de clientes y contactos utilizando la función `obtener_clientes_y_contactos`.
        Luego, obtiene el ID del cliente del formulario de la solicitud.

        Si se proporciona un ID de cliente, la función busca al cliente en la base de datos. Si no se encuentra al cliente,
        la función imprime un mensaje de error y devuelve una plantilla con una lista de clientes y listas vacías para los contactos y presupuestos.

        Si se encuentra al cliente, la función obtiene los contactos del cliente y devuelve una plantilla con una lista de clientes,
        los contactos del cliente y una lista vacía para los presupuestos.

        Si no se proporciona un ID de cliente, la función devuelve una plantilla con una lista de clientes y listas vacías para los contactos y presupuestos.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> presupuestos.presupuesto_contactos()
        """
        listar_clientes, contacto = self.obtener_clientes_y_contactos()
        id_cliente = request.form.get("cliente")
        if id_cliente:
            cliente = ClienteModel.query.get(id_cliente)
            if cliente is None:
                print("No se encontró el cliente")
                return render_template(
                    "consulta_contacto.html",
                    listar_clientes=listar_clientes,
                    listar_contactos=[],
                    presupuestos=[],
                )
            contacto = cliente.contactos
            return render_template(
                "consulta_contacto.html",
                listar_clientes=listar_clientes,
                listar_contactos=contacto,
                presupuestos=[],
            )
        else:
            return render_template(
                "consulta_contacto.html",
                listar_clientes=listar_clientes,
                listar_contactos=[],
                presupuestos=[],
            )

    def atencion(self):
        """
        Gestiona la atención a los contactos para un presupuesto específico.

        Esta función obtiene el ID del presupuesto de la sesión y el mensaje del formulario de la solicitud.
        Luego, confirma los contactos para el presupuesto y obtiene los IDs de los contactos asignados al presupuesto.

        Para cada ID de contacto, la función comprueba si el contacto ya está asociado al presupuesto. Si no lo está, crea un nuevo
        objeto PresupuestoContacto y lo agrega a la sesión de la base de datos.

        Finalmente, la función confirma los cambios en la base de datos y redirige al usuario a la página de generación de PDF para el presupuesto.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> presupuestos.atencion()
        """
        id_presupuesto = session.get("id_presupuesto")
        # contacto_ids = request.form.getlist("contacto_id")
        mensaje = request.form.get("mensaje_correo")

        self.confirmar_contactos_presupuesto(id_presupuesto)
        contacto_ids = self.obtener_contactos_presupuesto(id_presupuesto)

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
        """
            Obtiene los contactos asignados a un presupuesto específico.

        Esta función toma un ID de presupuesto y realiza una consulta a la base de datos para obtener los presupuestos de contacto
        asociados a ese presupuesto. Luego, crea una lista de los IDs de los contactos asignados a ese presupuesto.

        La función imprime la lista de IDs de los contactos asignados y luego la devuelve.

        Args:
            id_presupuesto (int): El ID del presupuesto para obtener los contactos.

        Returns:
            list of int: Una lista de los IDs de los contactos asignados al presupuesto.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> contactos_asignados = presupuestos.obtener_contactos_presupuesto(1)
        >>> print(contactos_asignados)
        [1, 2, 3]
        """
        presupuesto_contactos = PresupuestoContacto.query.filter_by(
            presupuesto_id=id_presupuesto
        ).all()
        contactos_asignados = [pc.contacto_id for pc in presupuesto_contactos]
        print(contactos_asignados)
        return contactos_asignados

    def confirmar_contactos_presupuesto(self, id_presupuesto):
        """
            Confirma los contactos para un presupuesto específico.

        Esta función toma un ID de presupuesto y luego obtiene los contactos seleccionados y el mensaje del formulario de la solicitud.
        Luego, obtiene los contactos que ya están asignados al presupuesto.

        La función determina qué contactos se han agregado y cuáles se han eliminado comparando los contactos seleccionados con los contactos asignados.

        Para cada contacto agregado, la función crea un nuevo objeto PresupuestoContacto y lo agrega a la sesión de la base de datos.

        Para cada contacto eliminado, la función busca el objeto PresupuestoContacto correspondiente en la base de datos y lo elimina de la sesión.

        Finalmente, la función confirma los cambios en la base de datos.

        Args:
            id_presupuesto (int): El ID del presupuesto a confirmar los contactos.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> presupuestos.confirmar_contactos_presupuesto(1)
        """
        contactos_seleccionados = request.form.getlist("contacto_id")
        mensaje = request.form.get("mensaje_correo")

        contactos_asignados = self.obtener_contactos_presupuesto(id_presupuesto)

        contactos_agregados = [
            id for id in contactos_seleccionados if id not in contactos_asignados
        ]
        contactos_eliminados = [
            id for id in contactos_asignados if id not in contactos_seleccionados
        ]

        for id in contactos_agregados:
            nuevo_contacto = PresupuestoContacto(
                presupuesto_id=id_presupuesto, contacto_id=id, mensaje=mensaje
            )
            db.session.add(nuevo_contacto)

        for id in contactos_eliminados:
            contacto_a_eliminar = PresupuestoContacto.query.filter_by(
                presupuesto_id=id_presupuesto, contacto_id=id
            ).first()
            if contacto_a_eliminar:
                db.session.delete(contacto_a_eliminar)

        db.session.commit()

    def consulta_mensajes_contacto(self, presupuesto_contacto_ids):
        """
            Consulta los mensajes de presupuesto de contacto para una lista de IDs de presupuesto de contacto.

        Esta función toma una lista de IDs de presupuesto de contacto, realiza una consulta a la base de datos para obtener
        los presupuestos de contacto correspondientes, y luego crea un diccionario que mapea cada ID de presupuesto de contacto
        a su objeto de presupuesto de contacto correspondiente.

        Args:
            presupuesto_contacto_ids (list of int): La lista de IDs de presupuesto de contacto a consultar.

        Returns:
            dict of {int: PresupuestoContacto}: Un diccionario que mapea cada ID de presupuesto de contacto a su objeto de presupuesto de contacto correspondiente.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> presupuesto_contacto_dict = presupuestos.consulta_mensajes_contacto([1, 2, 3])
        >>> print(presupuesto_contacto_dict)
        {1: <PresupuestoContacto 1>, 2: <PresupuestoContacto 2>, 3: <PresupuestoContacto 3>}
        """
        presupuesto_contacto = PresupuestoContacto.query.filter(
            PresupuestoContacto.id_presupuesto_contacto.in_(presupuesto_contacto_ids)
        ).all()
        presupuesto_contacto_dict = {
            pc.id_presupuesto_contacto: pc for pc in presupuesto_contacto
        }
        return presupuesto_contacto_dict

    def consulta_presupuesto_contacto(self):
        """
        Consulta los presupuestos de un contacto específico y renderiza una plantilla con los detalles.

        Esta función obtiene los clientes y los contactos, y luego determina el ID del contacto basándose en si la solicitud es POST o GET.
        Luego, realiza una consulta a la base de datos para obtener los presupuestos asociados a ese contacto y los pagina.

        La función también obtiene un diccionario de mensajes para cada presupuesto de contacto.

        Finalmente, la función renderiza una plantilla con los presupuestos, los clientes, el contacto, el número total de páginas,
        el ID del contacto y los mensajes de presupuesto de contacto.

        Returns:
            str: El HTML renderizado de la plantilla "consulta_contacto.html".

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> html = presupuestos.consulta_presupuesto_contacto()
        >>> print(html)
        "<!DOCTYPE html>..."
        """
        listar_clientes, contacto = self.obtener_clientes_y_contactos()
        if request.method == "POST":
            id_contacto = request.form.get("contacto", type=int)
        else:
            id_contacto = request.args.get("contacto", type=int)
        page = request.args.get("page", 1, type=int)
        query = PresupuestoContacto.query.filter_by(contacto_id=id_contacto)
        presupuestos = query.paginate(page=page, per_page=10)
        presupuesto_contacto_ids = [
            p.id_presupuesto_contacto for p in presupuestos.items
        ]
        presupuesto_contacto_dict = self.consulta_mensajes_contacto(
            presupuesto_contacto_ids
        )

        return render_template(
            "consulta_contacto.html",
            presupuestos=presupuestos,  # Pasa el objeto paginado a tu plantilla
            listar_clientes=listar_clientes,
            contacto=contacto,
            total_pages=presupuestos.pages,
            id_contacto=id_contacto,
            presupuesto_contacto=presupuesto_contacto_dict,
        )

    def consultar_presupuesto(self, id_presupuesto):
        """
        Consulta un presupuesto específico y renderiza una plantilla con los detalles.

        Esta función toma un ID de presupuesto, consulta el presupuesto y sus partidas asociadas en la base de datos,
        y luego obtiene el ID del cliente asociado al presupuesto.

        La función también obtiene los contactos del cliente y los contactos asignados al presupuesto.

        Finalmente, la función guarda el ID del presupuesto en la sesión y renderiza una plantilla con los detalles del presupuesto,
        los clientes, las partidas, el ID del cliente, los contactos y los contactos asignados.

        Args:
            id_presupuesto (int): El ID del presupuesto a consultar.

        Returns:
            str: El HTML renderizado de la plantilla "consultar_presupuesto.html".

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> html = presupuestos.consultar_presupuesto(1)
        >>> print(html)
        "<!DOCTYPE html>..."
        """
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

    def query_paginado(self, query, per_page):
        """
        Pagina una consulta de presupuestos.

        Esta función toma una consulta y un número de presupuestos por página, y luego pagina la consulta. La página actual
        se obtiene de la solicitud.

        La función también calcula el número total de páginas.

        Args:
            query (flask_sqlalchemy.BaseQuery): La consulta a paginar.
            per_page (int): El número de presupuestos por página.

        Returns:
            flask_sqlalchemy.Pagination, int: Los presupuestos paginados y el número total de páginas.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> query = PresupuestoModel.query.order_by(PresupuestoModel.id_presupuesto.desc())
        >>> paginado, total_pages = presupuestos.query_paginado(query, 25)
        >>> print(paginado)
        <flask_sqlalchemy.Pagination object at 0x7f8c1c2d3a90>
        >>> print(total_pages)
        4
        """
        page = request.args.get("page", 1, type=int)
        total_presupuestos = query.count()
        total_pages = (total_presupuestos - 1) // per_page + 1
        presupuestos = query.paginate(page=page, per_page=per_page, error_out=False)
        return presupuestos, total_pages

    def consultas(self):
        """
        Realiza una consulta de presupuestos y renderiza una plantilla con los resultados.

        Esta función realiza una consulta a la base de datos para obtener todos los presupuestos, ordenados en orden descendente
        por ID de presupuesto. Luego, filtra los presupuestos por fecha y los pagina.

        La función también obtiene un diccionario de mensajes para cada presupuesto.

        Finalmente, la función renderiza una plantilla con los resultados de la consulta, la fecha de búsqueda, el total de páginas
        y la información de contacto del presupuesto.

        Returns:
            str: El HTML renderizado de la plantilla "consultas.html".

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> html = presupuestos.consultas()
        >>> print(html)
        "<!DOCTYPE html>..."
        """
        query = PresupuestoModel.query.order_by(PresupuestoModel.id_presupuesto.desc())
        fecha_busqueda, query = self.consultasPorFecha(query)
        presupuestos, total_pages = self.query_paginado(query, 25)

        presupuesto_ids = [p.id_presupuesto for p in presupuestos.items]
        presupuesto_contacto_dict = self.consulta_mensajes(presupuesto_ids)

        return render_template(
            "consultas.html",
            presupuestos=presupuestos,
            fecha_busqueda=fecha_busqueda,
            total_pages=total_pages,
            presupuesto_contacto=presupuesto_contacto_dict,
        )

    def consulta_mensajes(self, presupuesto_ids):
        """
        Realiza una consulta de mensajes para una lista de presupuestos.

        Esta función toma una lista de IDs de presupuestos y realiza una consulta a la base de datos para obtener
        todos los mensajes asociados a esos presupuestos. Los resultados se devuelven en un diccionario donde las
        claves son los IDs de los presupuestos y los valores son las instancias de PresupuestoContacto.

        Args:
            presupuesto_ids (list): Una lista de IDs de presupuestos.

        Returns:
            dict: Un diccionario donde las claves son los IDs de los presupuestos y los valores son las instancias
                  de PresupuestoContacto.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> presupuesto_ids = [1, 2, 3]
        >>> mensajes = presupuestos.consulta_mensajes(presupuesto_ids)
        >>> print(mensajes)
        {1: <PresupuestoContacto 1>, 2: <PresupuestoContacto 2>, 3: <PresupuestoContacto 3>}
        """
        presupuesto_contacto = PresupuestoContacto.query.filter(
            PresupuestoContacto.presupuesto_id.in_(presupuesto_ids)
        ).all()
        presupuesto_contacto_dict = {
            pc.presupuesto_id: pc for pc in presupuesto_contacto
        }
        return presupuesto_contacto_dict

    def consultasPorFecha(self, query):
        """
        Filtra una consulta de presupuestos por fecha.

        Esta función toma una consulta SQLAlchemy y añade un filtro para limitar los resultados a los presupuestos
        que tienen una fecha dentro de un mes específico. El mes se especifica en el parámetro "fecha_busqueda" de
        la solicitud, que debe ser una cadena en el formato "YYYY-MM".

        Si "fecha_busqueda" no está presente en la solicitud, la función devuelve la consulta sin modificar.

        Args:
            query (sqlalchemy.orm.query.Query): La consulta a filtrar.

        Returns:
            tuple: Una tupla que contiene dos elementos:
                - La fecha de búsqueda como una cadena en el formato "YYYY-MM", o None si "fecha_busqueda" no está
                  presente en la solicitud.
                - La consulta filtrada, o la consulta original si "fecha_busqueda" no está presente en la solicitud.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> query = PresupuestoModel.query
        >>> fecha_busqueda, query_filtrada = presupuestos.consultasPorFecha(query)
        >>> print(fecha_busqueda)
        "2022-01"
        >>> print(query_filtrada)
        SELECT * FROM presupuestos WHERE fecha >= '2022-01-01' AND fecha < '2022-02-01'
        """
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
        """
        Realiza una consulta de presupuestos para un cliente específico y renderiza una plantilla con los resultados.

        Esta función obtiene el ID del cliente de la solicitud o de la sesión, y luego realiza una consulta a la base de datos
        para obtener todos los presupuestos para ese cliente. Los presupuestos se ordenan en orden descendente por ID de presupuesto.

        La función también obtiene una lista de todos los clientes y un diccionario de mensajes para cada presupuesto.

        Finalmente, la función renderiza una plantilla con los resultados de la consulta y la información del cliente.

        Returns:
            str: El HTML renderizado de la plantilla "consulta_cliente.html".

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> html = presupuestos.consulta_cliente()
        >>> print(html)
        "<!DOCTYPE html>..."
        """
        id_cliente = request.args.get("cliente") or session.get("cliente_id")
        session["cliente_id"] = id_cliente
        listar_clientes = ClienteModel.query.all()
        query = PresupuestoModel.query.filter_by(cliente_id=id_cliente).order_by(
            PresupuestoModel.id_presupuesto.desc()
        )
        cliente_seleccionado = ClienteModel.query.get(id_cliente)
        nombre_cliente = cliente_seleccionado.nombre if cliente_seleccionado else ""
        print(id_cliente)
        presupuestos, total_pages = self.query_paginado(query, per_page=25)
        presupuesto_ids = [p.id_presupuesto for p in presupuestos.items]
        presupuesto_contacto_dict = self.consulta_mensajes(presupuesto_ids)
        return render_template(
            "consulta_cliente.html",
            presupuestos=presupuestos,
            listar_clientes=listar_clientes,
            nombre_cliente=nombre_cliente,
            total_pages=total_pages,
            id_cliente=id_cliente,
            presupuesto_contacto=presupuesto_contacto_dict,
        )

    def obtener_clientes_y_contactos(self):
        """
        Obtiene una lista de todos los clientes y un contacto específico.

        Esta función realiza dos consultas a la base de datos. Primero, obtiene una lista de todos los clientes
        utilizando el modelo ClienteModel. Luego, obtiene un contacto específico utilizando el modelo ContactoModel.
        El ID del contacto se obtiene del formulario de solicitud.

        Returns:
            tuple: Una tupla que contiene dos elementos:
                - Una lista de todos los clientes. Cada cliente es una instancia de ClienteModel.
                - Un contacto específico. El contacto es una instancia de ContactoModel, o None si el ID del contacto
                  no se encuentra en la base de datos.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> clientes, contacto = presupuestos.obtener_clientes_y_contactos()
        >>> print(clientes)
        [<ClienteModel 1>, <ClienteModel 2>, <ClienteModel 3>]
        >>> print(contacto)
        <ContactoModel 1>
        """
        listar_clientes = ClienteModel.query.all()
        id_contacto = request.form.get("contacto")
        contacto = ContactoModel.query.get(id_contacto)
        return listar_clientes, contacto

    def cerrar(self):
        session.clear()
        self.contador_partidas = 1
        print("Cerraste el sistema")
        return redirect(url_for("index"))

    def borrar_partida(self, id_partida):
        """
        Borra una partida específica y actualiza el presupuesto correspondiente.

        Esta función toma un ID de partida, busca la partida en la base de datos y la borra. Luego, reordena las partidas
        restantes y recalcula los totales del presupuesto.

        Si la partida no se encuentra, la función redirige al usuario al índice.

        Después de borrar la partida, la función redirige al usuario al índice si se está creando un nuevo presupuesto,
        o de vuelta al presupuesto si se está consultando un presupuesto existente.

        Args:
            id_partida (int): El ID de la partida a borrar.

        Returns:
            Werkzeug Response: Una respuesta de redirección al índice o al presupuesto.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> respuesta = presupuestos.borrar_partida(1)
        >>> print(respuesta)
        <Response 302 FOUND>
        """
        partida = Presupuesto_Partida.query.get(id_partida)

        # Comprueba si la partida existe
        if partida is None:
            print("No se econtró la partida")
            return redirect(url_for("index"))
        presupuesto_id = partida.presupuesto_id
        db.session.delete(partida)
        db.session.commit()
        iva_porcentaje = session.get("iva_porcentaje", 0.08)
        self.reordenar_partidas(presupuesto_id)
        self.recalcular_totales(presupuesto_id, iva_porcentaje)

        nuevo_presupuesto = "id_presupuesto" in session
        if nuevo_presupuesto:
            return redirect(url_for("index"))
        else:
            return redirect(
                url_for("consultar_presupuesto", id_presupuesto=presupuesto_id)
            )

    def reordenar_partidas(self, presupuesto_id):
        """
        Reordena las partidas de un presupuesto específico.

        Esta función toma un ID de presupuesto, busca todas las partidas asociadas a ese presupuesto en la base de datos,
        y luego las reordena. El orden de las partidas se establece en función de su posición en la lista de partidas.

        Después de reordenar las partidas, la función guarda los cambios en la base de datos.

        Args:
            presupuesto_id (int): El ID del presupuesto cuyas partidas se van a reordenar.

        Ejemplo de uso:

        >>> presupuestos = Presupuestos()
        >>> presupuestos.reordenar_partidas(1)
        """
        partidas = Presupuesto_Partida.query.filter_by(
            presupuesto_id=presupuesto_id
        ).all()
        for i, partida in enumerate(partidas, start=1):
            partida.partida = i
        db.session.commit()

    # INICIO SEGMENTO DE CODIGO
    # EL SIGUIENTE CODIGO, ES PARA AGREGAR SIMBOLOS ESPECIALES A TRAVES DE TECLAS DE FUNCION
    # PERO SOLO FUNCIONA EN EL EQUIPO DONDE SE ESTA EJECUNTANDO EL PROGRAMA. NO FUNCIONA PARA LOS
    # USUARIOS QUE SE CONECTAN A TRAVES DE LA RED LOCAL
    # def on_f7():
    #     keyboard.write("°")
    #     return "Symbol added"

    # def on_f8():
    #     keyboard.write("#")
    #     return "Symbol added"

    # def on_f9():
    #     keyboard.write("Ø")
    #     return "Symbol added"

    # keyboard.add_hotkey("f7", on_f7)
    # keyboard.add_hotkey("f8", on_f8)
    # keyboard.add_hotkey("f9", on_f9)

    # FIN DEL SEGMENTO DE CODIGO

    # INICIO SEGMENTO DE CODIGO NUEVO, SUSITUYE AL ANTERIOR
    # EL SIGUIENTE CODIGO, ES PARA AGREGAR SIMBOLOS ESPECIALES A TRAVES DE UNA RUTA
    # LOS USUARIOS MIENTRAS ESTEN EN LA RED LOCAL YA PUEDEN AGREGAR SIMBOLOS ESPECIALES

    def add_symbol(self):
        symbol = request.form.get("symbol")
        if symbol == "f7":
            return "°"
        elif symbol == "f8":
            return "#"
        elif symbol == "f9":
            return "Ø"
        else:
            return "Invalid symbol"

    # FIN DEL SEGMENTO DE CODIGO NUEVO

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
            "/consulta_presupuesto_contacto",
            "consulta_presupuesto_contacto",
            self.consulta_presupuesto_contacto,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/borrar_partida/<int:id_partida>",
            "borrar_partida",
            self.borrar_partida,
            methods=["GET"],
        )

        self.app.add_url_rule(
            "/add_symbol", "add_symbol", self.add_symbol, methods=["POST"]
        )
