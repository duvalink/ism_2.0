from flask import Blueprint, redirect, url_for
from models.presupuesto import Presupuesto as PresupuestoModel
from models.atencion import PresupuestoContacto
from models.cliente import Contacto as ContactoModel
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

correo = Blueprint("correo", __name__)

email_user = os.getenv("EMAIL_USER")
email_pass = os.getenv("EMAIL_PASS")


class Correo:
    def __init__(self, app):
        self.app = app
        self.rutas()

    def crear_mensaje(self, destinatarios, asunto, cuerpo):
        mensaje = MIMEMultipart()
        mensaje["From"] = "Correo de prueba"
        mensaje["To"] = ", ".join(destinatarios)
        mensaje["Subject"] = asunto
        mensaje.attach(MIMEText(cuerpo, "plain"))
        return mensaje

    def adjuntar_archivo(self, mensaje, archivo_adjunto):
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
        smtp_server = "smtp.office365.com"
        puerto = 587
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
        return PresupuestoContacto.query.filter_by(presupuesto_id=presupuesto_id).all()

    def obtener_correos_y_asuntos(self, presupuesto_contactos):
        correos_electronicos = []
        asuntos = []
        for pc in presupuesto_contactos:
            contacto = ContactoModel.query.get(pc.contacto_id)
            if contacto:
                correos_electronicos.append(contacto.correo)
                asuntos.append(pc.mensaje)
        return correos_electronicos, asuntos

    def enviar_correos(self, destinatarios, asuntos, presupuesto_id):
        cuerpo = f"Buen dia, envio presupuesto {presupuesto_id}."
        archivo_adjunto = os.path.join(
            os.getcwd(), "presupuestos_pdf", f"P-{presupuesto_id}.pdf"
        )
        for destinatario, asunto in zip(destinatarios, asuntos):
            mensaje = self.crear_mensaje([destinatario], asunto, cuerpo)
            self.adjuntar_archivo(mensaje, archivo_adjunto)
            self.enviar_correo(mensaje, [destinatario])

    def enviar_correo_presupuesto(self, presupuesto_id):
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
