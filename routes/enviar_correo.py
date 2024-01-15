from flask import Blueprint, redirect, url_for
from models.presupuesto import Presupuesto as PresupuestoModel
from models.atencion import PresupuestoContacto
from models.cliente import Contacto as ContactoModel
# from routes.generar_pdf import Pdf
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

correo = Blueprint("correo", __name__)

email_server = os.getenv("EMAIL_SERVER")
email_server_port = os.getenv("EMAIL_SERVER_PORT")
email_user = os.getenv("EMAIL_USER")
email_pass = os.getenv("EMAIL_PASS")


class Correo:
    def __init__(self, app):
        self.app = app
        self.rutas()

    def crear_mensaje(self, destinatarios, asunto, cuerpo):
        """
        Esta función se encarga de crear un mensaje de correo electrónico.

        Parámetros:
        destinatarios (list): Una lista de direcciones de correo electrónico a las que se enviará el correo.
        asunto (str): El asunto del correo electrónico.
        cuerpo (str): El cuerpo del correo electrónico.

        Proceso:
        1. Crea una nueva instancia de la clase `MIMEMultipart`, que representa un correo electrónico.
        2. Establece el campo "From" del correo con un valor fijo "Correo de prueba".
        3. Establece el campo "To" del correo con las direcciones de correo electrónico de los destinatarios, separadas por comas.
        4. Establece el campo "Subject" del correo con el asunto proporcionado.
        5. Adjunta el cuerpo del correo al mensaje como texto plano.

        Retorna:
        El mensaje de correo electrónico creado.
        """
        mensaje = MIMEMultipart()
        mensaje["From"] = "Correo de prueba"
        mensaje["To"] = ", ".join(destinatarios)
        mensaje["Subject"] = asunto
        mensaje.attach(MIMEText(cuerpo, "plain"))
        return mensaje

    def adjuntar_archivo(self, mensaje, archivo_adjunto):
        """
        Esta función se encarga de adjuntar un archivo a un mensaje de correo electrónico.

        Parámetros:
        mensaje (EmailMessage): El mensaje de correo electrónico al que se adjuntará el archivo. Debe ser una instancia de la clase `EmailMessage`.
        archivo_adjunto (str): La ruta del archivo que se adjuntará al correo.

        Proceso:
        1. Abre el archivo en modo binario.
        2. Crea una nueva parte MIME de tipo "application/octet-stream".
        3. Establece el contenido de la parte con el contenido del archivo y lo codifica en base64.
        4. Añade una cabecera "Content-Disposition" a la parte para indicar que es un adjunto y para especificar su nombre de archivo.
        5. Adjunta la parte al mensaje.

        No retorna nada.
        """
        with open(archivo_adjunto, "rb") as adjunto:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(adjunto.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(archivo_adjunto)}",
            )
            mensaje.attach(part)

    def enviar_correo(self, mensaje, destinatarios):
        """
        Esta función se encarga de enviar un correo electrónico a una lista de destinatarios.

        Parámetros:
        mensaje (EmailMessage): El mensaje de correo electrónico que se enviará. Debe ser una instancia de la clase `EmailMessage`.
        destinatarios (list): Una lista de direcciones de correo electrónico a las que se enviará el correo.

        Proceso:
        1. Configura el servidor SMTP, el puerto, el usuario y la contraseña para el envío de correos.
        2. Intenta establecer una conexión con el servidor SMTP y enviar el correo.
        3. Si la conexión y el envío son exitosos, imprime un mensaje de éxito.
        4. Si ocurre un error durante la conexión o el envío, imprime un mensaje de error.

        No retorna nada.
        """
        smtp_server = email_server
        puerto = email_server_port
        usuario = email_user
        contrasena = email_pass
        try:
            with smtplib.SMTP(smtp_server, puerto) as servidor:
                servidor.starttls()
                servidor.login(usuario, contrasena)
                servidor.sendmail(usuario, destinatarios, mensaje.as_string())
                print("Correo enviado con exito.")
        except Exception as e:
            print("Error al enviar el correo: ", e)

    def obtener_contactos(self, presupuesto_id):
        """
        Esta función se encarga de obtener todos los contactos asociados con un presupuesto específico.

        Parámetros:
        presupuesto_id (int): El ID del presupuesto del cual se obtendrán los contactos.

        Proceso:
        1. Realiza una consulta en la tabla `PresupuestoContacto` para obtener todos los registros que tengan el `presupuesto_id` proporcionado.

        Retorna:
        Una lista de objetos `PresupuestoContacto` que representan los contactos asociados con el presupuesto. Si no hay contactos asociados con el presupuesto, retorna una lista vacía.
        """
        return PresupuestoContacto.query.filter_by(presupuesto_id=presupuesto_id).all()

    def obtener_correos_y_asuntos(self, presupuesto_contactos):
        """
        Esta función se encarga de obtener los correos electrónicos y los asuntos de los contactos asociados con un presupuesto.

        Parámetros:
        presupuesto_contactos (list): Una lista de objetos que representan los contactos asociados con un presupuesto.

        Proceso:
        1. Inicializa dos listas vacías, una para los correos electrónicos y otra para los asuntos.
        2. Itera sobre cada contacto en `presupuesto_contactos`.
        3. Obtiene el objeto `ContactoModel` correspondiente al contacto actual utilizando su `contacto_id`.
        4. Si el objeto `ContactoModel` existe, añade su correo electrónico y su mensaje a las listas correspondientes.

        Retorna:
        Un par de listas: la primera contiene los correos electrónicos de los contactos y la segunda contiene los asuntos de los correos.
        """
        correos_electronicos = []
        asuntos = []
        for pc in presupuesto_contactos:
            contacto = ContactoModel.query.get(pc.contacto_id)
            if contacto:
                correos_electronicos.append(contacto.correo)
                asuntos.append(pc.mensaje)
        return correos_electronicos, asuntos

    # def enviar_correos(self, destinatarios, asuntos, presupuesto_id):
    #     cuerpo = f"Buen dia, envio presupuesto {presupuesto_id}."
    #     archivo_adjunto = os.path.join(
    #         os.getcwd(), "presupuestos_pdf", f"P-{presupuesto_id}.pdf"
    #     )
    #     for destinatario, asunto in zip(destinatarios, asuntos):
    #         mensaje = self.crear_mensaje([destinatario], asunto, cuerpo)
    #         self.adjuntar_archivo(mensaje, archivo_adjunto)
    #         self.enviar_correo(mensaje, [destinatario])

    # def enviar_correos(self, destinatarios, asuntos, presupuesto_id):
    #     """
    #     Esta función se encarga de enviar correos electrónicos con el presupuesto más reciente adjunto a una lista de destinatarios.

    #     Parámetros:
    #     destinatarios (list): Una lista de direcciones de correo electrónico a las que se enviará el correo.
    #     asuntos (list): Una lista de asuntos para los correos. Se utilizará el primer asunto de la lista.
    #     presupuesto_id (int): El ID del presupuesto que se adjuntará al correo.

    #     Proceso:
    #     1. Crea el cuerpo del correo.
    #     2. Crea una instancia de la clase Pdf y obtiene el nombre y la ruta del archivo del presupuesto más reciente.
    #     3. Crea el mensaje de correo electrónico utilizando la función `crear_mensaje`.
    #     4. Adjunta el archivo del presupuesto más reciente al mensaje utilizando la función `adjuntar_archivo`.
    #     5. Envía el correo a los destinatarios utilizando la función `enviar_correo`.

    #     No retorna nada.
    #     """
    #     cuerpo = f"Buen dia, envio presupuesto {presupuesto_id}."

    #     generador_pdf = Pdf(self.app)
    #     nombre_archivo, ruta_pdf = generador_pdf.obtener_nombre_y_ruta_archivo(
    #         presupuesto_id
    #     )
    #     archivo_adjunto = ruta_pdf

    #     asunto = (
    #         asuntos[0] if asuntos else ""
    #     )  # Usar el primer asunto o una cadena vacía si no hay asuntos
    #     mensaje = self.crear_mensaje(destinatarios, asunto, cuerpo)
    #     self.adjuntar_archivo(mensaje, archivo_adjunto)
    #     self.enviar_correo(mensaje, destinatarios)



    def enviar_correos(self, destinatarios, asuntos, presupuesto_id): 
        cuerpo = f"Buen dia, envio presupuesto {presupuesto_id}." 
        archivo_adjunto = os.path.join( os.getcwd(), "presupuestos_pdf", f"P-{presupuesto_id}.pdf" ) 
        asunto = asuntos[0] if asuntos else '' 
        # Usar el primer asunto o una cadena vacía si no hay asuntos 
        mensaje = self.crear_mensaje(destinatarios, asunto, cuerpo) 
        self.adjuntar_archivo(mensaje, archivo_adjunto) 
        self.enviar_correo(mensaje, destinatarios)

    def enviar_correo_presupuesto(self, presupuesto_id):
        """
        Esta función se encarga de enviar correos electrónicos con el presupuesto adjunto a los contactos asociados con un presupuesto específico.

        Parámetros:
        presupuesto_id (int): El ID del presupuesto del cual se enviará el correo.

        Proceso:
        1. Obtiene los contactos asociados con el presupuesto utilizando la función `obtener_contactos`.
        2. Obtiene los correos electrónicos y asuntos de los contactos utilizando la función `obtener_correos_y_asuntos`.
        3. Envía los correos a los contactos con el presupuesto adjunto utilizando la función `enviar_correos`.
        4. Redirige al usuario a la página "cerrar" utilizando la función `redirect` de Flask.

        Retorna:
        Un objeto `Response` de Flask que redirige al usuario a la página "cerrar".
        """
        presupuesto_contactos = self.obtener_contactos(presupuesto_id)
        correos_electronicos, asuntos = self.obtener_correos_y_asuntos(
            presupuesto_contactos
        )
        self.enviar_correos(correos_electronicos, asuntos, presupuesto_id)
        return redirect(url_for("cerrar"))

    def rutas(self):
        self.app.add_url_rule(
            "/enviar_correo/<int:presupuesto_id>",
            "enviar_correo_presupuesto",
            self.enviar_correo_presupuesto,
        )
