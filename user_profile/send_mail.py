import smtplib
from email.mime.text import MIMEText
from django.conf import settings 
from celery import shared_task 
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator 
from django.utils.encoding import force_bytes

url = "http://localhost:2000/"

@shared_task(bind=True,max_retries=20)
def send_register_mail(self,user,key):
    body = """<p>
    Hello from ecommerce!<br><br>
    Confirmation Mail: %s
    You can see more details in this link:%saccount-confirm-email%s<br><br>
    Thank you from ecommerce!<br><br>
    </p>
    """%(user.username,url,key,)
    subject = "Registration Mail"
    recipients = [user.email]
    try:
        send_email(body,subject,recipients,"html")
        return "Email Is Sent"
    except Exception as e:
        print("Email not sent",e)
        raise self.retry(exc=e,countdown=25200)

@shared_task(bind=True,max_retries=20)
def send_reset_password_email(self,user):
    body = """
    hello %s,
    reset url:%sretrypassword/%s/%s
    """%(user.username,
    url,
    urlsafe_base64_encode(force_bytes(user.pk)).decode(),
    default_token_generator.make_token(user),
    )
    subject = "Reset password Mail"
    reciptients = [user.email]
    try:
        send_email(body,subject,reciptients,"html")
        return "Email Is Sent"
    except Exception as e:
        print("Email not sent",e)
        raise self.retry(exc=e,countdown=25200)

def send_email(body,subject,reciptients,body_type="plain"):
    session = smtplib.SMTP("smtp.gmail.com",getattr(settings,"EMAIL_PORT",None))
    session.starttls()
    session.login(
        getattr(settings,"EMAIL_HOST_USER",None),
        getattr(settings,"EMAIL_HOST_PASSWORD",None),
    )
    sender = "sardor5676626@gmail.com"
    msg = MIMEText(body,body_type)
    msg["subject"]=subject 
    msg["From"]=sender 
    msg["To"]=", ".join(reciptients)
    session.sendmail(sender,reciptients,msg.as_string())
