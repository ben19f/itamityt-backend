import smtplib
from email.message import EmailMessage

from starlette.concurrency import run_in_threadpool

from core.config import settings


class EmailService:

    def _send(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> None:
        message = EmailMessage()

        message["From"] = settings.smtp_from
        message["To"] = to_email
        message["Subject"] = subject

        message.set_content(body)

        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=20,
        ) as smtp:
            smtp.login(
                settings.smtp_username,
                settings.smtp_password,
            )

            smtp.send_message(message)

    async def send_verification_email(
        self,
        to_email: str,
        token: str,
    ) -> None:
        verification_url = (
            f"{settings.public_api_url.rstrip('/')}"
            f"/verify-email.php?token={token}"
        )

        body = f"""Здравствуйте!

Вы зарегистрировались на itamityt.ru.

Для подтверждения e-mail перейдите по ссылке:

{verification_url}

Ссылка действительна в течение 24 часов.

Если вы не регистрировались на itamityt.ru, просто проигнорируйте это письмо.
"""

        await run_in_threadpool(
            self._send,
            to_email,
            "Подтверждение e-mail — itamityt.ru",
            body,
        )


email_service = EmailService()