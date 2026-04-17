import re


def is_valid_email(email):
    """Validate email format."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None


def is_valid_ip(ip):
    """Validate IPv4 address."""
    pattern = r"^(?:\d{1,3}\.){3}\d{1,3}$"
    if not re.match(pattern, ip):
        return False
    parts = ip.split(".")
    return all(0 <= int(part) <= 255 for part in parts)


def validate_line(line):
    """
    Validate structure:
    email;passwordEmail;ipAddress;port;login;password;recoveryEmail
    """
    errors = []
    parts = line.strip().split(";")

    if len(parts) != 7:
        errors.append(f"❌ Nombre de colonnes invalide (trouvé {len(parts)} au lieu de 7)")
        return errors

    email, password_email, ip, port, login, password, recovery_email = parts

    # Validate emails
    if not is_valid_email(email):
        errors.append("❌ Format email principal invalide")

    if not is_valid_email(recovery_email):
        errors.append("❌ Format email recovery invalide")

    # Validate IP
    if not is_valid_ip(ip):
        errors.append("❌ Adresse IP invalide")

    # Validate Port
    if not port.isdigit() or not (1 <= int(port) <= 65535):
        errors.append("❌ Port invalide (doit être entre 1 et 65535)")

    return errors




def validate_file(file_path):
    invalid_lines = []
    total_lines = 0
    valid_count = 0

    print("🔎 Vérification du fichier en cours...\n")

    with open(file_path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):

            # Ignore header automatiquement
            if line_number == 1:
                print("ℹ️ Header détecté et ignoré.\n")
                continue

            if not line.strip():
                continue

            total_lines += 1
            errors = validate_line(line)

            if errors:
                invalid_lines.append((line_number, line.strip(), errors))
            else:
                valid_count += 1

    # ====== RESULTATS ======
    print("=" * 60)

    if not invalid_lines:
        print("✅ Tous les enregistrements sont valides.")
    else:
        print("❌ Des lignes invalides ont été détectées :\n")

        for line_number, content, errors in invalid_lines:
            print(f"📌 Ligne {line_number}:")
            print(f"   ➜ {content}")
            for error in errors:
                print(f"   {error}")
            print("-" * 60)

    print("\n📊 Résumé :")
    print(f"   📄 Total lignes vérifiées : {total_lines}")
    print(f"   ✅ Lignes valides : {valid_count}")
    print(f"   ❌ Lignes invalides : {len(invalid_lines)}")
    print("=" * 60)


if __name__ == "__main__":
    file_path = "input.txt"  
    validate_file(file_path)



