import logging
import smtplib
from email.message import EmailMessage
from html import escape

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_user_created_email(full_name: str, email: str, dni: str) -> None:
    settings = get_settings()
    if not settings.mail_username or not settings.mail_password:
        logger.warning("SMTP no configurado. Usuario creado para %s con DNI temporal.", email)
        return

    login_url = f"{settings.frontend_url.rstrip('/')}/login"
    _send_email(
        to_email=email,
        subject="Acceso a DocSuite",
        text=_build_text_email(full_name, email, dni, login_url),
        html=_build_html_email(full_name, email, dni, login_url),
    )


def send_password_reset_email(full_name: str, email: str, reset_url: str) -> None:
    settings = get_settings()
    if not settings.mail_username or not settings.mail_password:
        logger.warning("SMTP no configurado. Restablecimiento solicitado para %s.", email)
        return

    _send_email(
        to_email=email,
        subject="Restablece tu contrasena de DocSuite",
        text=_build_reset_text_email(full_name, reset_url),
        html=_build_reset_html_email(full_name, reset_url),
    )


def _send_email(to_email: str, subject: str, text: str, html: str) -> None:
    settings = get_settings()
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.mail_from or settings.mail_username
    message["To"] = to_email
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(settings.mail_host, settings.mail_port, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(settings.mail_username, settings.mail_password)
            smtp.send_message(message)
    except Exception as exc:
        logger.warning("No se pudo enviar correo a %s: %s", to_email, exc)


def _build_text_email(full_name: str, email: str, dni: str, login_url: str) -> str:
    return "\n".join(
        [
            f"Hola, {full_name}",
            "",
            "Bienvenido a DocSuite.",
            "El administrador creo tu cuenta para acceder a la plataforma.",
            f"Usuario: {email}",
            f"Contrasena temporal: {dni}",
            f"Ingresar: {login_url}",
            "",
            "Al iniciar sesion se te pedira cambiar esta contrasena.",
        ]
    )


def _build_html_email(full_name: str, email: str, dni: str, login_url: str) -> str:
    safe_full_name = escape(full_name)
    safe_email = escape(email)
    safe_dni = escape(dni)
    safe_login_url = escape(login_url, quote=True)
    return f"""
    <!doctype html>
    <html lang="es">
      <body style="margin:0;padding:0;background:#f1f5f9;font-family:Inter,Arial,sans-serif;color:#0f172a;">
        <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
          <tr>
            <td align="center" style="padding:32px 16px;">
              <table width="560" cellpadding="0" cellspacing="0" role="presentation" style="max-width:560px;width:100%;background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
                <tr>
                  <td style="background:#2563eb;padding:24px 28px;color:#ffffff;">
                    <p style="margin:0;font-size:18px;font-weight:700;">DocSuite</p>
                    <p style="margin:6px 0 0;font-size:13px;color:#dbeafe;">Productividad academica para documentos y actas</p>
                  </td>
                </tr>
                <tr>
                  <td style="padding:28px;">
                    <h1 style="margin:0 0 12px;font-size:22px;line-height:1.3;color:#0f172a;">Bienvenido a DocSuite</h1>
                    <p style="margin:0 0 18px;font-size:14px;line-height:1.7;color:#475569;">
                      Hola, <strong>{safe_full_name}</strong>. El administrador creo tu cuenta para acceder a la plataforma.
                    </p>
                    <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="margin:0 0 22px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;">
                      <tr>
                        <td style="padding:16px 18px;">
                          <p style="margin:0 0 8px;font-size:13px;color:#475569;">Usuario</p>
                          <p style="margin:0 0 14px;font-size:15px;font-weight:700;color:#0f172a;">{safe_email}</p>
                          <p style="margin:0 0 8px;font-size:13px;color:#475569;">Contrasena temporal</p>
                          <p style="margin:0;font-size:18px;font-weight:700;letter-spacing:1px;color:#0f172a;">{safe_dni}</p>
                        </td>
                      </tr>
                    </table>
                    <table cellpadding="0" cellspacing="0" role="presentation">
                      <tr>
                        <td style="background:#2563eb;border-radius:8px;">
                          <a href="{safe_login_url}" style="display:inline-block;padding:13px 22px;color:#ffffff;text-decoration:none;font-size:14px;font-weight:700;">
                            Ingresar a DocSuite
                          </a>
                        </td>
                      </tr>
                    </table>
                    <p style="margin:20px 0 0;font-size:12px;line-height:1.6;color:#64748b;">
                      Al iniciar sesion se te pedira cambiar esta contrasena por una personal.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """


def _build_reset_text_email(full_name: str, reset_url: str) -> str:
    return "\n".join(
        [
            f"Hola, {full_name}",
            "",
            "Recibimos una solicitud para restablecer tu contrasena de DocSuite.",
            f"Restablecer contrasena: {reset_url}",
            "",
            "Este enlace vence pronto. Si no solicitaste este cambio, ignora este correo.",
        ]
    )


def _build_reset_html_email(full_name: str, reset_url: str) -> str:
    safe_full_name = escape(full_name)
    safe_reset_url = escape(reset_url, quote=True)
    return f"""
    <!doctype html>
    <html lang="es">
      <body style="margin:0;padding:0;background:#f1f5f9;font-family:Inter,Arial,sans-serif;color:#0f172a;">
        <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
          <tr>
            <td align="center" style="padding:32px 16px;">
              <table width="560" cellpadding="0" cellspacing="0" role="presentation" style="max-width:560px;width:100%;background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
                <tr>
                  <td style="background:#0f172a;padding:24px 28px;color:#ffffff;">
                    <p style="margin:0;font-size:18px;font-weight:700;">DocSuite</p>
                    <p style="margin:6px 0 0;font-size:13px;color:#cbd5e1;">Restablecimiento seguro de acceso</p>
                  </td>
                </tr>
                <tr>
                  <td style="padding:28px;">
                    <h1 style="margin:0 0 12px;font-size:22px;line-height:1.3;color:#0f172a;">Restablece tu contrasena</h1>
                    <p style="margin:0 0 18px;font-size:14px;line-height:1.7;color:#475569;">
                      Hola, <strong>{safe_full_name}</strong>. Usa el siguiente boton para crear una nueva contrasena de acceso.
                    </p>
                    <table cellpadding="0" cellspacing="0" role="presentation" style="margin:0 0 22px;">
                      <tr>
                        <td style="background:#2563eb;border-radius:8px;">
                          <a href="{safe_reset_url}" style="display:inline-block;padding:13px 22px;color:#ffffff;text-decoration:none;font-size:14px;font-weight:700;">
                            Restablecer contrasena
                          </a>
                        </td>
                      </tr>
                    </table>
                    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px;">
                      <p style="margin:0;font-size:12px;line-height:1.7;color:#64748b;">
                        El enlace vence pronto y solo puede usarse una vez. Si no solicitaste este cambio, puedes ignorar este mensaje.
                      </p>
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """
