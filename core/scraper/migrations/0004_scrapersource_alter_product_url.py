# Generated manually for scraper source URLs and TextField-only model text.

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scraper", "0003_favorite"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="url",
            field=models.TextField(verbose_name="URL"),
        ),
        migrations.CreateModel(
            name="ScraperSource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.TextField(db_index=True, unique=True, verbose_name="Nombre")),
                (
                    "url",
                    models.TextField(
                        db_index=True,
                        unique=True,
                        validators=[django.core.validators.URLValidator()],
                        verbose_name="URL",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creacion")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Fecha de actualizacion")),
            ],
            options={
                "verbose_name": "Fuente de scraper",
                "verbose_name_plural": "Fuentes de scraper",
                "ordering": ["name"],
            },
        ),
    ]
