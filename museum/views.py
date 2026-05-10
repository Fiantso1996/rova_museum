import json
import time
import re
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib import messages
from .models import TicketType, Order, OrderItem

# Configuration du logger pour les SMS simulés
logger = logging.getLogger(__name__)

# Types de billets prédéfinis (peuvent aussi être gérés via l'admin)
TICKET_TYPES = [
    {'name': 'Étranger', 'price': 40000},
    {'name': 'Adulte Résident', 'price': 5000},
    {'name': 'Enfant Résident', 'price': 2000},
]

# --- Fonction utilitaire d'envoi de SMS (simulation) ---
def send_sms_confirmation(phone_number, order):
    """
    Simule l'envoi d'un SMS de confirmation.
    En production, remplacez par un appel à une API SMS (ex: Twilio, Africa's Talking).
    """
    message = (
        f"Musee Rova: Paiement confirme! Commande #{order.id}. "
        f"Total: {order.total_amount} Ar. Code EAN13: {order.transaction_id}. "
        f"Presentez ce code a l'entree. Merci!"
    )
    # Écriture dans les logs (simulation)
    logger.info(f"[SMS SENT] To: {phone_number} | Message: {message}")
    return True


# --- Gestion du panier en session ---
def get_cart(request):
    return request.session.get('cart', [])

def save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


# --- Vues principales ---
def home(request):
    """Page d'accueil avec la billetterie"""
    # Créer automatiquement les types de billets en base s'ils n'existent pas
    for ticket in TICKET_TYPES:
        TicketType.objects.get_or_create(
            name=ticket['name'],
            defaults={'price': ticket['price']}
        )
    return render(request, 'museum/index.html')


@require_POST
def add_to_cart(request):
    """Ajoute un article au panier (AJAX)"""
    try:
        data = json.loads(request.body)
        name = data.get('name')
        price = int(data.get('price'))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Données invalides'}, status=400)

    if not TicketType.objects.filter(name=name, price=price).exists():
        return JsonResponse({'success': False, 'error': 'Type de billet non valide'}, status=400)

    cart = get_cart(request)
    found = False
    for item in cart:
        if item['name'] == name:
            item['quantity'] += 1
            found = True
            break
    if not found:
        cart.append({'name': name, 'price': price, 'quantity': 1})

    save_cart(request, cart)
    return JsonResponse({'success': True, 'cart': cart})


@require_POST
def remove_from_cart(request):
    """Supprime un article du panier (AJAX)"""
    try:
        data = json.loads(request.body)
        index = int(data.get('index'))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Index invalide'}, status=400)

    cart = get_cart(request)
    if 0 <= index < len(cart):
        if cart[index]['quantity'] > 1:
            cart[index]['quantity'] -= 1
        else:
            cart.pop(index)
        save_cart(request, cart)
        return JsonResponse({'success': True, 'cart': cart})
    else:
        return JsonResponse({'success': False, 'error': 'Index hors limite'}, status=400)


def cart_data(request):
    """Retourne le contenu actuel du panier (AJAX)"""
    cart = get_cart(request)
    total = sum(item['price'] * item['quantity'] for item in cart)
    count = sum(item['quantity'] for item in cart)
    return JsonResponse({
        'cart': cart,
        'total': total,
        'count': count
    })


def checkout(request):
    """Page de paiement avec récapitulatif du panier"""
    cart = get_cart(request)
    if not cart:
        messages.warning(request, "Votre panier est vide.")
        return redirect('home')
    total = sum(item['price'] * item['quantity'] for item in cart)
    return render(request, 'museum/checkout.html', {
        'cart': cart,
        'total': total,
    })


# --- Génération du code EAN-13 ---
def calculate_ean13_checksum(code):
    """Calcule la clé de contrôle d'un code EAN-13"""
    sum_ = 0
    for i, digit in enumerate(code[:12]):
        d = int(digit)
        if i % 2 == 0:
            sum_ += d
        else:
            sum_ += d * 3
    return (10 - (sum_ % 10)) % 10

def generate_ean13():
    """Génère un code EAN13 unique basé sur le timestamp et le préfixe Madagascar (261)"""
    prefix = "261"
    timestamp_part = str(int(time.time() * 1000))[-9:]  # 9 derniers chiffres du timestamp ms
    base = prefix + timestamp_part
    checksum = calculate_ean13_checksum(base)
    return base + str(checksum)


# --- Traitement du paiement ---
@require_POST
def process_payment(request):
    """Traite le paiement, valide les données, crée la commande et envoie un SMS si mobile."""
    cart = get_cart(request)
    if not cart:
        messages.error(request, "Votre panier est vide.")
        return redirect('home')

    payment_method = request.POST.get('payment_method')
    if payment_method not in ['visa', 'mobile']:
        messages.error(request, "Méthode de paiement invalide.")
        return redirect('checkout')

    card_number = request.POST.get('card_number', '').strip()
    mobile_number = request.POST.get('mobile_number', '').strip()

    errors = []
    if payment_method == 'visa':
        card_clean = re.sub(r'\s+', '', card_number)
        if not card_clean:
            errors.append("Veuillez saisir un numéro de carte bancaire.")
        elif not re.match(r'^4\d{12}(\d{3})?$', card_clean):
            errors.append("Numéro de carte Visa invalide. Il doit commencer par 4 et comporter 13 ou 16 chiffres.")
    else:  # mobile
        mobile_clean = re.sub(r'[\s\+]', '', mobile_number)
        if not mobile_clean:
            errors.append("Veuillez saisir un numéro de téléphone mobile.")
        elif not re.match(r'^(261)?(32|33|34|38)\d{7}$', mobile_clean):
            errors.append("Numéro de téléphone mobile invalide. Format attendu : 034 XX XXX XX ou +261 34 XX XXX XX.")

    if errors:
        for error in errors:
            messages.error(request, error)
        return redirect('checkout')

    total = sum(item['price'] * item['quantity'] for item in cart)

    with transaction.atomic():
        order = Order.objects.create(
            paid=True,
            total_amount=total,
            payment_method=payment_method,
            transaction_id=generate_ean13(),
            phone_number=mobile_number if payment_method == 'mobile' else '',
        )
        for item in cart:
            ticket_type = TicketType.objects.filter(name=item['name']).first()
            OrderItem.objects.create(
                order=order,
                ticket_type=ticket_type,
                name=item['name'],
                price=item['price'],
                quantity=item['quantity']
            )

    # Envoi du SMS de confirmation pour les paiements mobile
    if payment_method == 'mobile' and mobile_number:
        send_sms_confirmation(mobile_number, order)

    # Vider le panier
    request.session['cart'] = []
    request.session.modified = True

    return render(request, 'museum/payment_success.html', {
        'order': order,
        'total': total,
    })

import io
import barcode
from barcode.writer import ImageWriter
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404

def download_barcode(request, order_id):
    """
    Génère et renvoie l'image PNG du code-barres EAN-13 associé à une commande.
    """
    order = get_object_or_404(Order, id=order_id, paid=True)
    if not order.transaction_id:
        raise Http404("Aucun code-barres associé à cette commande.")

    # Créer l'objet code-barres EAN13
    ean = barcode.get('ean13', order.transaction_id, writer=ImageWriter())

    # Écrire l'image dans un buffer mémoire
    buffer = io.BytesIO()
    ean.write(buffer)

    # Retourner l'image en réponse HTTP
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="billet_{order.transaction_id}.png"'

    return response

# museum/api_views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Order

@csrf_exempt
@require_POST
def validate_ticket(request):
    """
    Endpoint API pour valider un ticket par code-barres EAN13.
    Attend un JSON avec la clé "barcode".
    Retourne le statut du ticket et les détails de la commande.
    """
    try:
        data = json.loads(request.body)
        barcode = data.get('barcode', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)

    if not barcode:
        return JsonResponse({'success': False, 'error': 'Code-barres manquant'}, status=400)

    try:
        order = Order.objects.get(transaction_id=barcode, paid=True)
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ticket invalide ou non payé'}, status=404)

    if order.validated_at is not None:
        return JsonResponse({
            'success': False,
            'error': 'Ticket déjà utilisé',
            'validated_at': order.validated_at.isoformat(),
            'validation_count': order.validation_count
        }, status=409)

    # Première validation : enregistrer
    order.validated_at = timezone.now()
    order.validation_count = 1
    order.save()

    # Construire la réponse avec détails
    items = [{'name': item.name, 'quantity': item.quantity} for item in order.items.all()]
    return JsonResponse({
        'success': True,
        'message': 'Ticket valide - accès autorisé',
        'order_id': order.id,
        'total_amount': order.total_amount,
        'items': items,
        'validated_at': order.validated_at.isoformat()
    })

def scan_page(request):
    """Page de scan pour le personnel (protégée éventuellement)"""
    return render(request, 'museum/scan_ticket.html')

# ─────────────────────────────────────────────────────────────
#  NOUVELLES VUES : Contact, Staff, Événements
# ─────────────────────────────────────────────────────────────
from .models import Contact, StaffMember, Event

def contact(request):
    """Page de contact avec formulaire"""
    success = False
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', 'info')
        message_text = request.POST.get('message', '').strip()

        if name and email and message_text:
            Contact.objects.create(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message_text,
            )
            success = True
        else:
            messages.error(request, 'Veuillez remplir tous les champs obligatoires.')

    return render(request, 'museum/contact.html', {'success': success})


def staff(request):
    """Page de présentation du personnel"""
    members = StaffMember.objects.filter(is_active=True)
    return render(request, 'museum/staff.html', {'members': members})


def events(request):
    """Page des événements"""
    from django.utils import timezone
    upcoming = Event.objects.filter(is_published=True, start_date__gte=timezone.now()).order_by('start_date')
    past = Event.objects.filter(is_published=True, start_date__lt=timezone.now()).order_by('-start_date')[:6]
    return render(request, 'museum/events.html', {'upcoming': upcoming, 'past': past})


def event_detail(request, event_id):
    """Détail d'un événement"""
    from django.shortcuts import get_object_or_404
    event = get_object_or_404(Event, id=event_id, is_published=True)
    return render(request, 'museum/event_detail.html', {'event': event})
