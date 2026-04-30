from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0004_alter_documentflow_folder_default"),
    ]

    operations = [
        migrations.AddField(
            model_name="zapsigndocument",
            name="signed_file_url",
            field=models.URLField(
                blank=True, verbose_name="Link do Documento Assinado"
            ),
        ),
    ]
