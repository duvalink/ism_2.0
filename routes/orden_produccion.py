from flask import Blueprint, redirect, url_for, request, send_file
from dotenv import load_dotenv
import os
import webbrowser
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Flowable,
    KeepTogether,
    PageBreak,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from models.cliente import Cliente as ClienteModel
from models.cliente import Contacto as ContactoModel
from models.presupuesto import Presupuesto as PresupuestoModel
from models.atencion import PresupuestoContacto
from utils.db import db
import locale

load_dotenv()

pdf = Blueprint("pdf", __name__)


class Pdf:
    def __init__(self, app):
        self.app = app
        self.rutas()

    def datos_tabla_presupuesto(self, presupuesto):
        id_presupuesto = presupuesto.id_presupuesto
        fecha = presupuesto.fecha.strftime("%d/%m/%Y")
        cliente = ClienteModel.query.get(presupuesto.cliente_id)
        materiales = presupuesto.materiales
        mano_obra = presupuesto.mano_obra
        subtotal = presupuesto.subtotal
        iva = presupuesto.iva
        total = presupuesto.total

        return {
            "id_presupuesto": id_presupuesto,
            "fecha": fecha,
            "cliente": cliente,
            "materiales": materiales,
            "mano_obra": mano_obra,
            "subtotal": subtotal,
            "iva": iva,
            "total": total,
        }

    def datos_tabla_cliente(self, presupuesto):
        cliente = ClienteModel.query.get(presupuesto.cliente_id)

        return {
            "cliente": {
                "nombre": cliente.nombre,
                "direccion": cliente.direccion,
                "cp": cliente.cp,
                "ciudad": cliente.ciudad,
                "telefono": cliente.telefono,
                "rfc": cliente.rfc,
            },
            "fecha": presupuesto.fecha.strftime("%d/%m/%Y"),
            "id_presupuesto": presupuesto.id_presupuesto,
        }

    def datos_tabla_contacto(self, presupuesto_id):
        contactos_presupuesto = (
            db.session.query(ContactoModel)
            .join(
                PresupuestoContacto,
                PresupuestoContacto.contacto_id == ContactoModel.id_contacto,
            )
            .filter(PresupuestoContacto.presupuesto_id == presupuesto_id)
            .all()
        )

        nombres_contactos = ", ".join(
            [contacto.contacto for contacto in contactos_presupuesto]
        )

        return nombres_contactos

    def datos_tabla_pres_part(self, presupuesto):
        presupuesto_partida = presupuesto.presupuesto_partida

        partidas = []

        for partida in presupuesto_partida:
            partidas.append(
                {
                    "partida": partida.partida,
                    "descripcion": partida.descripcion,
                    "cantidad": partida.cantidad,
                    "precio": partida.precio,
                    "importe": partida.importe,
                    "material": partida.material,
                }
            )

        return partidas

    def procesar_partidas(self, partidas, styles):
        data = []
        for partida in partidas:
            numero_partida = partida["partida"]
            descripcion_material = (
                partida["descripcion"] + ", MATERIAL " + partida["material"]
            )

            # Verificar la longitud de descripcion_material
            if len(descripcion_material) > 120 and len(descripcion_material) < 200:
                estilo_descripcion = styles["DescripcionStyleSmall"]
            else:
                estilo_descripcion = styles["DescripcionStyle"]

            descripcion = Paragraph(descripcion_material, style=estilo_descripcion)
            cantidad = partida["cantidad"]

            data.append(
                [
                    numero_partida,
                    descripcion,
                    (cantidad),
                ]
            )
        return data

    def datos_ism(self):
        # Datos de la empresa
        ism_nombre = os.getenv("ISM_NOMBRE")
        ism_rfc = os.getenv("ISM_RFC")
        ism_direccion = os.getenv("ISM_DIRECCION")
        ism_telefono = os.getenv("ISM_TELEFONO")
        documento_tipo = os.getenv("DOCUMENTO_TIPO_OP")

        return {
            "ism_nombre": ism_nombre,
            "ism_rfc": ism_rfc,
            "ism_direccion": ism_direccion,
            "ism_telefono": ism_telefono,
            "documento_tipo": documento_tipo,
        }

    def crear_datos_empresa(
        self,
        logo,
        datos_ism,
        minimal_leading_style,
        doc_type_style,
        empresa_nombre_estilo,
    ):
        nombre_empresa = Paragraph(datos_ism["ism_nombre"], style=empresa_nombre_estilo)
        rfc_empresa = Paragraph(datos_ism["ism_rfc"], style=minimal_leading_style)
        direccion_empresa = Paragraph(
            datos_ism["ism_direccion"], style=minimal_leading_style
        )
        telefono_empresa = Paragraph(
            datos_ism["ism_telefono"], style=minimal_leading_style
        )
        documento_tipo = Paragraph(datos_ism["documento_tipo"], style=doc_type_style) if datos_ism.get("documento_tipo") else ""

        # Tabla de datos de la empresa
        datos_empresa = Table(
            [
                [
                    logo,
                    "",
                    [
                        [nombre_empresa],
                        [rfc_empresa],
                        [direccion_empresa],
                        [telefono_empresa],
                        [documento_tipo],
                    ],
                    "",
                    logo,
                ]
            ],
            colWidths=[100, 5, 310, 5, 100],  # Ajuste de anchos de columnas
        )

        # Estilo de la tabla de encabezado
        datos_empresa.setStyle(
            TableStyle(
                [
                    # Alineación vertical en la parte superior
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    # Alineación vertical en la parte superior de la tabla anidada
                    ("VALIGN", (1, 0), (1, 0), "TOP"),
                ]
            )
        )

        return datos_empresa

    def crear_datos_cliente(self, datos_presupuesto, contactos_presupuesto, styleN):
        # contactos_presupuest0_paragraph = Paragraph(contactos_presupuesto, styleN)
        datos_cliente = [
            [
                "Cliente:",
                datos_presupuesto["cliente"].nombre,
                "",
                "",
                "",
                "Presupuesto: ",
            ],
            [
                "Fecha Inicio:",
                "",
                "",
                "",
                "",
                datos_presupuesto["id_presupuesto"],
            ],
            [
                "Fecha Fin:",
                "",
                "",
                "",
            ],
        ]

        return datos_cliente
    
    def crear_datos_orden_proceso(self, styleN):
        datos_orden_proceso=[
            [
                "Horas",
                "Esclavo",
                "Actividades",
            ],
            [],
            [],
            [],
            [],
            [],
        ]
        return datos_orden_proceso

    def obtener_nombre_archivo_unico(self, presupuesto_id):
        # Nombre base del archivo
        nombre_archivo = f"REMISION-{presupuesto_id}.pdf"

        # Ruta del archivo
        dir_path = os.path.dirname(os.path.realpath(__file__))
        dir_pdf = os.path.join(dir_path, "../remisiones")

        # Verificar si el directorio existe, si no, crearlo
        if not os.path.exists(dir_pdf):
            os.makedirs(dir_pdf)

        ruta_pdf = os.path.join(dir_pdf, nombre_archivo)

        # Verificar si el archivo original ya existe
        if not os.path.exists(ruta_pdf):
            # Crear el archivo
            with open(ruta_pdf, "w") as fp:
                pass

        # Si el archivo ya existe
        else:
            # Contador para identificar a los archivos que se generen cuando ya exista un archivo con el mismo nombre
            contador = 1

            # Adjuntar el consecutivo al nombre base, en caso de que ya exista el archivo pdf
            nuevo_nombre_archivo = f"REMISION-{presupuesto_id}_({contador}).pdf"
            nueva_ruta_pdf = os.path.join(dir_pdf, nuevo_nombre_archivo)

            # Incrementar el contador hasta que se encuentre un nombre de archivo que no exista en el directorio
            while os.path.exists(nueva_ruta_pdf):
                contador += 1
                nuevo_nombre_archivo = f"REMISION-{presupuesto_id}_({contador}).pdf"
                nueva_ruta_pdf = os.path.join(dir_pdf, nuevo_nombre_archivo)

            # Asignar el nuevo nombre al archivo
            nombre_archivo = nuevo_nombre_archivo
            ruta_pdf = nueva_ruta_pdf

        return nombre_archivo, ruta_pdf

    def orden_produccion(self, presupuesto_id):
        # Establecer el locale para los formatos de moneda
        locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")

        # Obtener el presupuesto
        presupuesto = PresupuestoModel.query.get(presupuesto_id)
        # Accede a los datos de la tabla presupuesto
        datos_presupuesto = self.datos_tabla_presupuesto(presupuesto)

        # Obtener los contactos del presupuesto
        contactos_presupuesto = self.datos_tabla_contacto(presupuesto_id)

        # Acceder a los datos de la tabla presupuesto_partida a traves de la relacion con presupuesto

        # Datos de la empresa
        datos_ism = self.datos_ism()

        # Nombre base del archivo
        nombre_archivo, ruta_pdf = self.obtener_nombre_archivo_unico(presupuesto_id)

        doc = SimpleDocTemplate(
            nombre_archivo,
            pagesize=letter,
            leftMargin=10 * mm,  # Margen izquierdo de 20 mm
            rightMargin=10 * mm,  # Margen derecho de 20 mm
            topMargin=5 * mm,  # Margen superior de 20 mm
            bottomMargin=8 * mm,  # Margen inferior de 20 mm
        )

        # Logo de la empresa
        # logo_path = "./static/img/logoEmpresa.png"
        dir_path = os.path.dirname(os.path.realpath(__file__))
        logo_path = os.path.join(dir_path, "../static/img/logoEmpresa.png")
        # Ajustar width y height segun dimensiones deseadas
        logo = Image(logo_path, width=100, height=92)

        # Estilos
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="DescripcionStyle", fontSize=10, leading=11))
        styles.add(ParagraphStyle(name="DescripcionStyleSmall", fontSize=8, leading=9))
        styleN = styles["Normal"]

        # Estilo de encabezado
        header_style = styles["Heading1"]
        header_style.alignment = 1  # Centrado

        # Estilo personalizado para el parrafo con un espacio entre lineas minimo
        minimal_leading_style = ParagraphStyle(
            name="MinimalLeading",
            fontSize=10,
            leading=11,  # Valor que define el espacio entre lineas, ajustar segun necesidad
            alignment=1,  # Alineacion vertical
        )

        # Estilos personalizados para el nombre de ISM
        empresa_nombre_estilo = ParagraphStyle(
            name="MinimalLeading",
            fontSize=16,  # Tamaño de la fuente
            # negritas
            fontName="Helvetica-Bold",
            leading=15,  # Valor que define el espacio entre lineas, ajustar segun necesidad
            alignment=1,  # Alineacion vertical
        )
        # Estilo personalizado para el tipo de documento (Orden de Produccion)
        doc_type_style = ParagraphStyle(
            name="DocTypeStyle",
            fontSize=23,
            fontName="Helvetica-Bold",
            leading=20,  # Valor que define el espacio entre lineas, ajustar segun necesidad
            alignment=1,  # Alineacion vertical
        )

        datos_empresa = self.crear_datos_empresa(
            logo,
            datos_ism,
            minimal_leading_style,
            doc_type_style,
            empresa_nombre_estilo,
        )

        datos_cliente = self.crear_datos_cliente(
            datos_presupuesto, contactos_presupuesto, styleN
        )
        
        # MEDIDAS DE ESPACIO EN LOS DATOS DEL CLIENTE Y FECHA
        datos_cliente = Table(datos_cliente, colWidths=[70, "*", 20, 40, 70])
        

        # Estilo de la tabla de encabezado
        datos_cliente.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),  # Alineación a la izquierda
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),  # Fuente negrita
                    ("FONTSIZE", (0, 0), (-1, -1), 10),  # Tamaño de fuente
                    (
                        "FONTSIZE",
                        (5, 1),
                        (5, 1),
                        15,
                    ),  # Tamaño de fuente del id_prespuesto
                    (
                        "FONTNAME",
                        (5, 1),
                        (5, 1),
                        "Helvetica-Bold",
                    ),  # Fuente negrita del id_presupuesto
                    (
                        "ALIGN",
                        (5, 1),
                        (5, 1),
                        "CENTER",
                    ),  # Alineación centrada del id_presupuesto
                    (
                        "SPAN",
                        (1, 3),
                        (4, 3),
                    ),  # Combinar celdas de la fila de atencion")
                    # alignacion vertical centrada de la celda "Atencion"
                    ("VALIGN", (0, 3), (0, 3), "TOP"),
                ]
            )
        )
        
        
        datos_orden_proceso=self.crear_datos_orden_proceso(styleN)

        datos_orden_proceso=Table(datos_orden_proceso, colWidths=[40,"*",350,10])

        datos_orden_proceso.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),  # Alineación a la izquierda
                    ("FONTSIZE", (0, 0), (-1, -1), 12),  # Tamaño de fuente
                    ("FONTNAME",(0, 0), (-1, -1),"Helvetica-Bold",),  # Fuente negrita del id_presupuesto
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),  # Alineación a la izquierda
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        data = [
            [
                "Part",
                "Descripcion",
                "Cant",
                # "Precio",
                # "Importe",
            ]
        ]

        partidas = self.datos_tabla_pres_part(presupuesto)

        data += self.procesar_partidas(partidas, styles)

        table = Table(data, colWidths=[30, 500, 30])

        # Estilo de la tabla de cotizaciones
        table.setStyle(
            TableStyle(
                [
                    # ("BACKGROUND", (0, 0), (-1, 0), colors.gray),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("ALIGN", (0, 1), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    # NEGRITA
                    ("FONTNAME", (4, 1), (4, -1), "Helvetica-Bold"),
                ]
            )
        )

        # Tabla de totales
        datos_totales = [
            [
                "",
                "",
                "",
                "",
                "",
                "",
            ],
            [
                "",
                "",
                "",
                "DIBUJO O ANEXAR HOJA DE DIBUJO",
            ],
        ]

        # Ajustar el tamaño de las columnas de espacio si es necesario
        # cols_datos_totales = Table(datos_totales, colWidths=[100, 30, 100, 50, 100])

        tabla_totales = Table(
            datos_totales, colWidths=[100,50, 100]
        )

        tabla_totales.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (3, 0), (3, 1), "Helvetica-Bold"),
                ]
            )
        )

        spacer = Spacer(0, 5)

        # Agregar la tabla de información de la empresa
        flowables = [datos_empresa, spacer]
        flowables.append(datos_cliente)  # Agregar la tabla de encabezado
        flowables.append(datos_orden_proceso)  # Agregar la tabla de encabezado
        flowables.append(spacer)  # Agregar un espacio
        flowables.append(KeepTogether(table))  # Agregar la tabla de cotizaciones

        # # Calcular la altura de las tablas
        header_table_width, header_table_height = datos_cliente.wrap(
            doc.width, doc.height
        )
        
        table_width, table_height = table.wrap(doc.width, doc.height)
        tabla_totales_width, tabla_totales_height = tabla_totales.wrap(doc.width, doc.height)

        # Calcular espacio disponible en la página actual
        remaining_space = (
            doc.height - (header_table_height + spacer.height + table_height) - 180
        )
        spacer_height = remaining_space - tabla_totales_height - 60
        totals_spacer = Spacer(-1, spacer_height)

        flowables.append(totals_spacer)

        # Agregar un salto de página a los flowables
        flowables.append(tabla_totales)
        doc.build(flowables)

        return send_file(nombre_archivo, mimetype="application/pdf")

    def rutas(self):
        self.app.add_url_rule(
            "/orden_produccion/<int:presupuesto_id>",
            "orden_produccion",
            self.orden_produccion,
            methods=["GET", "POST"],
        )
