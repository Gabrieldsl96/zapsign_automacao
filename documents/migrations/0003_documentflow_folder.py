from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0002_remove_zapsigndocument_pdf_url_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="documentflow",
            name="folder",
            field=models.CharField(
                default="Geral", max_length=255, verbose_name="Pasta ZapSign"
            ),
        ),
    ]
