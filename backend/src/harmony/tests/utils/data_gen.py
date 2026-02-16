import uuid
import random
import string
from faker import Faker

fake = Faker()

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def generate_user_data():
    uid = str(uuid.uuid4())[:8]
    return {
        "username": f"user_{uid}",
        "email": f"user_{uid}@{random_string(6)}.com",
        "password": random_string(12),
    }

def generate_chat_message(min_words=3, max_words=15):
    """Generates a random sentence or short paragraph."""
    return fake.sentence(nb_words=random.randint(min_words, max_words))