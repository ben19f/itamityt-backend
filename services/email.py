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

    async def send_email_change_verification(
        self,
        to_email: str,
        token: str,
    ) -> None:
        verification_url = (
            f"{settings.public_api_url.rstrip('/')}"
            f"/verify-email.php?token={token}"
        )

        body = f"""Здравствуйте!

Чтобы изменить адрес e-mail в профиле itamityt.ru, перейдите по ссылке:

{verification_url}

Ссылка действительна в течение 24 часов. Текущий адрес останется без изменений,
если вы не подтвердите новый.

Если вы не запрашивали изменение адреса, просто проигнорируйте это письмо.
"""

        await run_in_threadpool(
            self._send,
            to_email,
            "Подтверждение нового e-mail — itamityt.ru",
            body,
        )

    async def send_password_reset_email(
        self,
        to_email: str,
        token: str,
    ) -> None:
        reset_url = (
            f"{settings.public_api_url.rstrip('/')}"
            f"/reset-password.php?token={token}"
        )

        body = f"""Здравствуйте!

Для сброса пароля на itamityt.ru перейдите по ссылке:

{reset_url}

Ссылка действительна в течение 1 часа и может быть использована только один раз.
Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.
"""

        await run_in_threadpool(
            self._send,
            to_email,
            "Сброс пароля — itamityt.ru",
            body,
        )


email_service = EmailService()
