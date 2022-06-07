# Generated by Django 4.0.4 on 2022-06-05 06:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cards', '0001_initial'),
        ('decks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cardset',
            name='set_format',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sets', to='decks.format', verbose_name='Format'),
        ),
        migrations.AddField(
            model_name='card',
            name='card_class',
            field=models.ManyToManyField(to='cards.cardclass', verbose_name='Class'),
        ),
        migrations.AddField(
            model_name='card',
            name='card_set',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cardsets', to='cards.cardset', verbose_name='Set'),
        ),
        migrations.AddField(
            model_name='card',
            name='mechanic',
            field=models.ManyToManyField(blank=True, help_text='Card mechanics', to='cards.mechanic', verbose_name='Mechanics'),
        ),
        migrations.AddField(
            model_name='card',
            name='tribe',
            field=models.ManyToManyField(blank=True, help_text='For creatures only.', to='cards.tribe', verbose_name='Tribe'),
        ),
    ]
