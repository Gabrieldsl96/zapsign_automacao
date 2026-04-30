from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0003_documentflow_folder"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documentflow",
            name="folder",
            field=models.CharField(
                default="Sistema_RN", max_length=255, verbose_name="Pasta ZapSign"
            ),
        ),
    ]
