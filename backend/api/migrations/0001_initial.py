from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='SignalLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('symbol', models.CharField(max_length=20)),
                ('direction', models.CharField(choices=[('BUY', 'Buy'), ('SELL', 'Sell'), ('HOLD', 'Hold')], max_length=4)),
                ('confidence', models.FloatField()),
                ('agent_name', models.CharField(max_length=50)),
                ('reasoning', models.TextField(blank=True)),
                ('rl_action', models.CharField(blank=True, max_length=10, null=True)),
                ('rl_reward', models.FloatField(blank=True, null=True)),
            ],
            options={'ordering': ['-timestamp']},
        ),
        migrations.CreateModel(
            name='LangChainSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(max_length=100, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('symbol', models.CharField(blank=True, max_length=20)),
                ('messages', models.JSONField(default=list)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='signallog',
            index=models.Index(fields=['symbol', 'timestamp'], name='api_signall_symbol_timestamp_idx'),
        ),
    ]
