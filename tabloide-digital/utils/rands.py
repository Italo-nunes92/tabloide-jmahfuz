import string
from random import SystemRandom
from django.utils.text import slugify
import secrets

def random_letters(k):
    return ''.join(SystemRandom().choices(
        string.ascii_lowercase + string.digits, k=k
    ))

def slygify_new(text, k=5):
    return slugify(text) + '-' + random_letters(k)



def generate_secret_key(length=50):
    return secrets.token_urlsafe(length)


