import os, secrets, sys
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


if getattr(sys, 'frozen', False):
    ROOT = os.path.dirname(sys.executable)
else:
    ROOT = os.path.dirname(os.path.abspath(__file__))

KEY_DIR=os.path.join(ROOT,"private_key")
PUBLIC_DIR=os.path.join(ROOT,"public_keys")

def generate_keys(name):
    if not name or not name.strip():
        raise ValueError("Invalid key name")

    name=name.strip()

    os.makedirs(KEY_DIR,exist_ok=True)
    os.makedirs(PUBLIC_DIR,exist_ok=True)

    private_key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    public_key=private_key.public_key()
    password=secrets.token_bytes(32)

    private_path=os.path.join(KEY_DIR,f"{name}_private.pem")
    meta_path=os.path.join(KEY_DIR,f"{name}_private.meta")
    public_path=os.path.join(PUBLIC_DIR,f"{name}_public.pem")

    with open(private_path,"wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(password)
        ))

    with open(public_path,"wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    with open(meta_path,"wb") as f:
        f.write(password)

    print(f"Generated keys for '{name}'")
    print(f"Private : {private_path}")
    print(f"Public  : {public_path}")

    return private_path,public_path,meta_path

if __name__=="__main__":
    generate_keys("bravo")