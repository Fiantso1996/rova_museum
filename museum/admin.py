from django.contrib import admin
from django.utils.html import format_html
from .models import TicketType, Order, OrderItem, ScanLog, Contact, StaffMember, Event


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('name', 'price', 'quantity')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class ScanLogInline(admin.TabularInline):
    model = ScanLog
    extra = 0
    readonly_fields = ('scanned_at', 'scan_location', 'success', 'message', 'ip_address')
    can_delete = False
    ordering = ['-scanned_at']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created_at',
        'paid',
        'total_amount_display',
        'payment_method',
        'transaction_id_short',
        'validation_status',
        'scan_count',
    )
    list_filter = ('paid', 'payment_method', 'created_at', 'validated_at')
    search_fields = ('transaction_id', 'customer_name', 'customer_email', 'phone_number')
    readonly_fields = (
        'created_at',
        'total_amount',
        'transaction_id',
        'payment_method',
        'validated_at',
        'validation_count',
    )
    fieldsets = (
        ('Informations de paiement', {
            'fields': (
                'paid',
                'payment_method',
                'transaction_id',
                'total_amount',
                'created_at',
            )
        }),
        ('Informations client', {
            'fields': (
                'customer_name',
                'customer_email',
                'phone_number',
            )
        }),
        ('Validation du ticket', {
            'fields': (
                'validated_at',
                'validation_count',
            )
        }),
    )
    inlines = [OrderItemInline, ScanLogInline]
    date_hierarchy = 'created_at'
    actions = ['mark_as_paid']

    def total_amount_display(self, obj):
        return f"{obj.total_amount:,} Ar".replace(',', ' ')
    total_amount_display.short_description = "Montant total"
    total_amount_display.admin_order_field = 'total_amount'

    def transaction_id_short(self, obj):
        return obj.transaction_id or "-"
    transaction_id_short.short_description = "Code EAN13"

    def validation_status(self, obj):
        if obj.validated_at:
            return format_html('<span style="color: green;">✓ Validé le {}</span>', obj.validated_at.strftime('%d/%m/%Y %H:%M'))
        return format_html('<span style="color: orange;">⏳ Non validé</span>')
    validation_status.short_description = "Statut validation"

    def scan_count(self, obj):
        count = obj.scan_logs.count()
        if count > 0:
            return format_html('<a href="?q={}">{}</a>', obj.transaction_id, count)
        return "0"
    scan_count.short_description = "Nb scans"

    @admin.action(description="Marquer comme payé")
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(paid=True)
        self.message_user(request, f"{updated} commande(s) marquée(s) comme payée(s).")


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_display', 'is_active', 'description_preview')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    fields = ('name', 'price', 'description', 'is_active')

    def price_display(self, obj):
        return f"{obj.price:,} Ar".replace(',', ' ')
    price_display.short_description = "Prix"
    price_display.admin_order_field = 'price'

    def description_preview(self, obj):
        if obj.description:
            return obj.description[:50] + ('...' if len(obj.description) > 50 else '')
        return "-"
    description_preview.short_description = "Description"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_link', 'name', 'price_display', 'quantity')
    list_filter = ('order__paid', 'name')
    search_fields = ('order__id', 'name')
    readonly_fields = ('order', 'ticket_type', 'name', 'price', 'quantity')

    def has_add_permission(self, request):
        return False

    def price_display(self, obj):
        return f"{obj.price:,} Ar".replace(',', ' ')
    price_display.short_description = "Prix unitaire"

    def order_link(self, obj):
        url = f"/admin/museum/order/{obj.order.id}/change/"
        return format_html('<a href="{}">Commande #{}</a>', url, obj.order.id)
    order_link.short_description = "Commande"
    order_link.admin_order_field = 'order__id'


@admin.register(ScanLog)
class ScanLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order_link',
        'scanned_at',
        'scan_location',
        'success_icon',
        'message',
        'ip_address',
    )
    list_filter = ('success', 'scan_location', 'scanned_at')
    search_fields = ('order__transaction_id', 'message', 'ip_address')
    readonly_fields = ('order', 'scanned_at', 'scan_location', 'success', 'message', 'ip_address')
    date_hierarchy = 'scanned_at'

    def has_add_permission(self, request):
        return False

    def order_link(self, obj):
        url = f"/admin/museum/order/{obj.order.id}/change/"
        return format_html('<a href="{}">Commande #{}</a>', url, obj.order.id)
    order_link.short_description = "Commande"
    order_link.admin_order_field = 'order__id'

    def success_icon(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✅ Succès</span>')
        return format_html('<span style="color: red;">❌ Échec</span>')
    success_icon.short_description = "Résultat"

# ─────────────────────────────────────────────────────────────
#  ADMIN : NOUVEAUX MODÈLES
# ─────────────────────────────────────────────────────────────

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'subject_display', 'created_at', 'is_read', 'is_read_icon')
    list_filter = ('subject', 'is_read', 'created_at')
    search_fields = ('name', 'email', 'phone', 'message')
    readonly_fields = ('created_at',)
    list_editable = ('is_read',)
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Expéditeur', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Message', {
            'fields': ('subject', 'message', 'created_at', 'is_read')
        }),
    )

    def subject_display(self, obj):
        return obj.get_subject_display()
    subject_display.short_description = 'Sujet'

    def is_read_icon(self, obj):
        if obj.is_read:
            return format_html('<span style="color:green;">✅ Lu</span>')
        return format_html('<span style="color:orange;">📩 Non lu</span>')
    is_read_icon.short_description = 'Statut'

    actions = ['mark_as_read', 'mark_as_unread']

    @admin.action(description='Marquer comme lu')
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} message(s) marqué(s) comme lu(s).')

    @admin.action(description='Marquer comme non lu')
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} message(s) marqué(s) comme non lu(s).')


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'role_display', 'phone', 'email', 'is_active', 'photo_preview')
    list_filter = ('role', 'is_active')
    search_fields = ('first_name', 'last_name', 'phone', 'email')
    list_editable = ('is_active',)
    fieldsets = (
        ('Identité', {
            'fields': ('first_name', 'last_name', 'photo', 'bio')
        }),
        ('Poste', {
            'fields': ('role', 'is_active', 'joined_at')
        }),
        ('Coordonnées', {
            'fields': ('phone', 'email')
        }),
    )

    def role_display(self, obj):
        return obj.get_role_display()
    role_display.short_description = 'Rôle'

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="height:40px;width:40px;object-fit:cover;border-radius:50%;">', obj.photo.url)
        return '–'
    photo_preview.short_description = 'Photo'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category_display', 'start_date', 'end_date', 'location', 'is_free', 'is_published', 'image_preview')
    list_filter = ('category', 'is_free', 'is_published', 'start_date')
    search_fields = ('title', 'description', 'location')
    list_editable = ('is_published',)
    date_hierarchy = 'start_date'
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'category', 'description', 'image')
        }),
        ('Dates & Lieu', {
            'fields': ('start_date', 'end_date', 'location')
        }),
        ('Détails', {
            'fields': ('is_free', 'max_participants', 'is_published')
        }),
    )

    def category_display(self, obj):
        return obj.get_category_display()
    category_display.short_description = 'Catégorie'

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;width:70px;object-fit:cover;border-radius:4px;">', obj.image.url)
        return '–'
    image_preview.short_description = 'Aperçu'
