from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('museum', '0005_alter_scanlog_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nom complet')),
                ('email', models.EmailField(verbose_name='Email')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Téléphone')),
                ('subject', models.CharField(
                    choices=[
                        ('info', "Demande d'information"),
                        ('reservation', 'Réservation de groupe'),
                        ('partenariat', 'Partenariat'),
                        ('autre', 'Autre'),
                    ],
                    default='info',
                    max_length=50,
                    verbose_name='Sujet',
                )),
                ('message', models.TextField(verbose_name='Message')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date d'envoi")),
                ('is_read', models.BooleanField(default=False, verbose_name='Lu')),
            ],
            options={
                'verbose_name': 'Message de contact',
                'verbose_name_plural': 'Messages de contact',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='StaffMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100, verbose_name='Prénom')),
                ('last_name', models.CharField(max_length=100, verbose_name='Nom')),
                ('role', models.CharField(
                    choices=[
                        ('directeur', 'Directeur / Directrice'),
                        ('conservateur', 'Conservateur / Conservatrice'),
                        ('guide', 'Guide touristique'),
                        ('accueil', "Agent d'accueil"),
                        ('securite', 'Agent de sécurité'),
                        ('technique', 'Technicien'),
                        ('administration', 'Administration'),
                        ('autre', 'Autre'),
                    ],
                    default='autre',
                    max_length=50,
                    verbose_name='Rôle',
                )),
                ('phone', models.CharField(max_length=20, verbose_name='Numéro de téléphone')),
                ('email', models.EmailField(blank=True, verbose_name='Email professionnel')),
                ('bio', models.TextField(blank=True, verbose_name='Biographie courte')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='staff/', verbose_name='Photo')),
                ('is_active', models.BooleanField(default=True, verbose_name='En poste')),
                ('joined_at', models.DateField(blank=True, null=True, verbose_name="Date d'arrivée")),
            ],
            options={
                'verbose_name': 'Membre du personnel',
                'verbose_name_plural': 'Membres du personnel',
                'ordering': ['last_name', 'first_name'],
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name="Titre de l'événement")),
                ('category', models.CharField(
                    choices=[
                        ('exposition', 'Exposition'),
                        ('visite_guidee', 'Visite guidée'),
                        ('conference', 'Conférence'),
                        ('atelier', 'Atelier'),
                        ('spectacle', 'Spectacle culturel'),
                        ('autre', 'Autre'),
                    ],
                    default='exposition',
                    max_length=50,
                    verbose_name='Catégorie',
                )),
                ('description', models.TextField(verbose_name='Description')),
                ('image', models.ImageField(blank=True, null=True, upload_to='events/', verbose_name="Image de l'événement")),
                ('start_date', models.DateTimeField(verbose_name='Date de début')),
                ('end_date', models.DateTimeField(blank=True, null=True, verbose_name='Date de fin')),
                ('location', models.CharField(
                    blank=True,
                    default="Musée Rova d'Antananarivo",
                    max_length=200,
                    verbose_name='Lieu',
                )),
                ('is_free', models.BooleanField(default=True, verbose_name='Entrée gratuite')),
                ('max_participants', models.PositiveIntegerField(blank=True, null=True, verbose_name='Capacité maximale')),
                ('is_published', models.BooleanField(default=True, verbose_name='Publié')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'Événement',
                'verbose_name_plural': 'Événements',
                'ordering': ['-start_date'],
            },
        ),
    ]
