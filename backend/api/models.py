"""
Django models for Forex Alpha API
"""

from django.db import models


class SignalLog(models.Model):
    """Logs every generated trading signal for auditing and history"""

    DIRECTION_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
        ('HOLD', 'Hold'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True)
    symbol = models.CharField(max_length=20)
    direction = models.CharField(max_length=4, choices=DIRECTION_CHOICES)
    confidence = models.FloatField()
    agent_name = models.CharField(max_length=50)
    reasoning = models.TextField(blank=True)
    rl_action = models.CharField(max_length=10, blank=True, null=True)
    rl_reward = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.symbol} | {self.direction} | {self.confidence:.2f} @ {self.timestamp}"


class LangChainSession(models.Model):
    """Stores LangChain conversation sessions for AI assistant"""

    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    symbol = models.CharField(max_length=20, blank=True)
    messages = models.JSONField(default=list)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Session {self.session_id} ({self.symbol})"
