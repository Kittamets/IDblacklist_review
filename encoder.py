import json, os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

PUBLIC_KEY_DIR = "public_keys"

def load_public_keys():
    recipients = {}

    for filename in os.listdir(PUBLIC_KEY_DIR):
        if filename.endswith(".pem"):
            rid = os.path.splitext(filename)[0]
            path = os.path.join(PUBLIC_KEY_DIR, filename)

            with open(path, "rb") as f:
                recipients[rid] = serialization.load_pem_public_key(f.read())
    
    print("Recipients loaded:", list(recipients.keys()))

    return recipients


def encrypt_file(input_path, output_path):
    recipients = load_public_keys()

    if not recipients:
        raise Exception("No public keys found")

    with open(input_path, "rb") as f:
        data = f.read()

    # 1. Generate AES key (Fernet uses AES internally)
    aes_key = Fernet.generate_key()
    cipher = Fernet(aes_key)

    # 2. Encrypt data
    encrypted_data = cipher.encrypt(data)

    encrypted_keys = {}

    # 3. Encrypt AES key for each recipient
    for rid, public_key in recipients.items():
        enc_key = public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        encrypted_keys[rid] = enc_key.hex()

    # 4. Package everything
    package = {
        "filename": os.path.basename(input_path),
        "keys": encrypted_keys,
        "data": encrypted_data.hex()
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(package, f)

    print(f"Encrypted for {len(encrypted_keys)} recipients -> {output_path}")
    
    return output_path
