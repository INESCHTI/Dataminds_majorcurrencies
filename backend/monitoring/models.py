"""
Monitoring models for performance tracking and safety
"""
from django.db import models


class AgentPerformanceLog(models.Model):
    """Log of agent performance for tracking"""
    agent_name = models.CharField(max_length=50, db_index=True)
    symbol = models.CharField(max_length=20, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Performance metrics
    pnl = models.FloatField(default=0.0)
    confidence = models.FloatField(default=0.0)
    was_correct = models.BooleanField(default=False)
    
    # Additional metadata
    signal = models.CharField(max_length=10)
    reasoning = models.TextField(blank=True)
    
    class Meta:
        db_table = "agent_performance_log"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['agent_name', '-timestamp']),
            models.Index(fields=['symbol', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.agent_name} - {self.symbol} - {self.pnl:.2f}"


class SystemHealth(models.Model):
    """System health monitoring"""
    timestamp = models.DateTimeField(auto_now_add=True)
    component = models.CharField(max_length=50)
    status = models.CharField(max_length=20)  # HEALTHY, DEGRADED, ERROR
    message = models.TextField(blank=True)
    metrics = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['component', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.component} - {self.status}"
