from django.db import models
from django.utils import timezone

class TicketType(models.Model):
    """Types de billets disponibles (peut être géré en base pour plus de flexibilité)"""
    name = models.CharField(max_length=100, unique=True)
    price = models.PositiveIntegerField(help_text="Prix en Ariary (Ar)")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.price} Ar"

class Order(models.Model):
    """Commande / Paiement"""
    created_at = models.DateTimeField(default=timezone.now)
    paid = models.BooleanField(default=False)
    total_amount = models.PositiveIntegerField(default=0)
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=20, unique=True, blank=True)  # Code EAN13
    customer_email = models.EmailField(blank=True)
    customer_name = models.CharField(max_length=200, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, help_text="Numéro utilisé pour le SMS de confirmation")

    validated_at = models.DateTimeField(null=True, blank=True)
    validation_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Commande #{self.id} - {self.total_amount} Ar"

class OrderItem(models.Model):
    """Ligne de commande"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100)  # Nom du billet au moment de l'achat
    price = models.PositiveIntegerField()    # Prix unitaire au moment de l'achat
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.name}"
    
class ScanLog(models.Model):
    """Historique des scans de tickets (validations)"""
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='scan_logs')
    scanned_at = models.DateTimeField(auto_now_add=True)
    scan_location = models.CharField(max_length=100, blank=True, help_text="Lieu du scan (ex: Entrée principale)")
    success = models.BooleanField(default=True)
    message = models.CharField(max_length=200, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"{status} Scan {self.order.transaction_id} - {self.scanned_at.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = "Historique de scan"
        verbose_name_plural = "Historiques de scan"
        ordering = ['-scanned_at']


# ─────────────────────────────────────────────────────────────
#  NOUVEAUX MODÈLES  (ajoutés sans modifier le code principal)
# ─────────────────────────────────────────────────────────────

class Contact(models.Model):
    """Messages envoyés via le formulaire de contact"""
    SUBJECT_CHOICES = [
        ('info', 'Demande d\'information'),
        ('reservation', 'Réservation de groupe'),
        ('partenariat', 'Partenariat'),
        ('autre', 'Autre'),
    ]
    name = models.CharField(max_length=200, verbose_name="Nom complet")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES, default='info', verbose_name="Sujet")
    message = models.TextField(verbose_name="Message")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Date d'envoi")
    is_read = models.BooleanField(default=False, verbose_name="Lu")

    def __str__(self):
        return f"{self.name} – {self.get_subject_display()} ({self.created_at.strftime('%d/%m/%Y')})"

    class Meta:
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering = ['-created_at']


class StaffMember(models.Model):
    """Membres du personnel du musée"""
    ROLE_CHOICES = [
        ('directeur', 'Directeur / Directrice'),
        ('conservateur', 'Conservateur / Conservatrice'),
        ('guide', 'Guide touristique'),
        ('accueil', 'Agent d\'accueil'),
        ('securite', 'Agent de sécurité'),
        ('technique', 'Technicien'),
        ('administration', 'Administration'),
        ('autre', 'Autre'),
    ]
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='autre', verbose_name="Rôle")
    phone = models.CharField(max_length=20, verbose_name="Numéro de téléphone")
    email = models.EmailField(blank=True, verbose_name="Email professionnel")
    bio = models.TextField(blank=True, verbose_name="Biographie courte")
    photo = models.ImageField(upload_to='staff/', blank=True, null=True, verbose_name="Photo")
    is_active = models.BooleanField(default=True, verbose_name="En poste")
    joined_at = models.DateField(null=True, blank=True, verbose_name="Date d'arrivée")

    def __str__(self):
        return f"{self.first_name} {self.last_name} – {self.get_role_display()}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Membre du personnel"
        verbose_name_plural = "Membres du personnel"
        ordering = ['last_name', 'first_name']


class Event(models.Model):
    """Événements organisés au musée"""
    CATEGORY_CHOICES = [
        ('exposition', 'Exposition'),
        ('visite_guidee', 'Visite guidée'),
        ('conference', 'Conférence'),
        ('atelier', 'Atelier'),
        ('spectacle', 'Spectacle culturel'),
        ('autre', 'Autre'),
    ]
    title = models.CharField(max_length=200, verbose_name="Titre de l'événement")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='exposition', verbose_name="Catégorie")
    description = models.TextField(verbose_name="Description")
    image = models.ImageField(upload_to='events/', blank=True, null=True, verbose_name="Image de l'événement")
    start_date = models.DateTimeField(verbose_name="Date de début")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de fin")
    location = models.CharField(max_length=200, blank=True, default='Musée Rova d\'Antananarivo', verbose_name="Lieu")
    is_free = models.BooleanField(default=True, verbose_name="Entrée gratuite")
    max_participants = models.PositiveIntegerField(null=True, blank=True, verbose_name="Capacité maximale")
    is_published = models.BooleanField(default=True, verbose_name="Publié")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} – {self.start_date.strftime('%d/%m/%Y')}"

    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
        ordering = ['-start_date']