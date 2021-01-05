from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

def send_mail_with_token(to_email, link):
    subject = 'Decide - Correo para autenticación'
    from_email = 'Decide <do_not_reply@decide.org>'

    cont = {
        'link': link
    }

    msg_plain = get_template('authentication/email/email.txt').render(cont)
    msg_html = get_template('authentication/email/email.html').render(cont)

    msg = EmailMultiAlternatives(subject, msg_plain, from_email, [to_email])
    msg.attach_alternative(msg_html, "text/html")
    msg.send(fail_silently=False)