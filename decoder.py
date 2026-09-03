import json, os, sys
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

if getattr(sys, 'frozen', False):
    ROOT = os.path.dirname(sys.executable)
else:
    ROOT = os.path.dirname(os.path.abspath(__file__))

KEY_DIR = os.path.join(ROOT, "private_key")
META_DIR = os.path.join(ROOT, "private_key")

def load_private_key(key_name=None):
    """Loads the private key. If no name is provided, it looks for any available private key in KEY_DIR."""
    if not os.path.exists(KEY_DIR):
        raise Exception(f"Private key directory not found: {KEY_DIR}")

    # If a specific key name isn't passed, find the first available private key in the folder
    if not key_name:
        pem_files = [f for f in os.listdir(KEY_DIR) if f.endswith("_private.pem")]
        if not pem_files:
            raise Exception(f"No private keys found in {KEY_DIR}")
        key_name = pem_files[0].replace("_private.pem", "")

    private_key_path = os.path.join(KEY_DIR, f"{key_name}_private.pem")
    private_meta_path = os.path.join(KEY_DIR, f"{key_name}_private.meta")

    if not os.path.exists(private_key_path) or not os.path.exists(private_meta_path):
        raise Exception(f"Key files for '{key_name}' not found in {KEY_DIR}")

    with open(private_key_path, "rb") as f:
        key_data = f.read()

    with open(private_meta_path, "rb") as f:
        password = f.read()

    return serialization.load_pem_private_key(
        key_data,
        password=password
    )


def find_matching_aes_key(private_key, encrypted_keys):
    for rid, enc_key_hex in encrypted_keys.items():
        try:
            encrypted_key = bytes.fromhex(enc_key_hex)

            aes_key = private_key.decrypt(
                encrypted_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            print(f"Matched key entry: {rid}")
            return aes_key

        except Exception:
            continue

    raise Exception("No matching key found for this private key")


def decrypt_file(input_path, output_path=None, key_name=None):
    private_key = load_private_key(key_name)

    with open(input_path, "r") as f:
        package = json.load(f)
    
    filename = package["filename"]
    
    if output_path is None:
        output_path = os.path.join(ROOT, filename)

    # 1. Find correct AES key automatically
    aes_key = find_matching_aes_key(private_key, package["keys"])

    # 2. Decrypt data
    encrypted_data = bytes.fromhex(package["data"])
    cipher = Fernet(aes_key)

    try:
        decrypted = cipher.decrypt(encrypted_data)
    except Exception:
        raise Exception("Decryption failed (data may be corrupted or tampered)")
    
    with open(output_path, "wb") as f:
        f.write(decrypted)

    print(f"Decryption successful -> {output_path}")
