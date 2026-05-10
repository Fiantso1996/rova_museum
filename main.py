import qrcode

# 1. Données que tu souhaites encoder (Lien URL ou texte)
data = "https://rova-museum.onrender.com"

# 2. Configuration du QR Code
qr = qrcode.QRCode(
    version=1,  # Taille du QR Code (1 à 40)
    error_correction=qrcode.constants.ERROR_CORRECT_L, # Tolérance aux erreurs
    box_size=10, # Taille de chaque carré du QR
    border=4,    # Épaisseur de la bordure
)

# Ajouter les données
qr.add_data(data)
qr.make(fit=True)

# 3. Création de l'image (couleurs personnalisables)
img = qr.make_image(fill_color="black", back_color="white")

# 4. Sauvegarder le fichier
img.save("mon_qrcode.png")

print("Le QR Code a été généré avec succès sous le nom 'mon_qrcode.png' !")