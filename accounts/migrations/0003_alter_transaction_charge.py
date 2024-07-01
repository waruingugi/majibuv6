# Generated by Django 5.0.6 on 2024-06-22 17:56

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_rename_mpesapayments_mpesapayment_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="charge",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.0"),
                help_text="Total amount after deducting fees and tax.",
                max_digits=10,
            ),
        ),
    ]
