"""
Django management command to start WebSocket service
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import asyncio
import threading
import time

from data_layer.websocket_manager import websocket_manager
from data_layer.real_time_data_store import real_time_data_store


class Command(BaseCommand):
    help = 'Start the WebSocket service for real-time FX data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            nargs='+',
            default=['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'],
            help='Currency pairs to stream'
        )
        parser.add_argument(
            '--providers',
            type=str,
            default='forexcom',
            help='Data providers (forexcom, oanda)'
        )
        parser.add_argument(
            '--oanda-api-key',
            type=str,
            help='OANDA API key (required for oanda provider)'
        )
        parser.add_argument(
            '--oanda-account-id',
            type=str,
            help='OANDA account ID (required for oanda provider)'
        )
    
    def handle(self, *args, **options):
        symbols = options['symbols']
        providers_config = {}
        
        # Configure providers
        if 'oanda' in options['providers']:
            if not options['oanda_api_key'] or not options['oanda_account_id']:
                self.stdout.write(
                    self.style.ERROR('OANDA API key and account ID are required for OANDA provider')
                )
                return
            
            providers_config['oanda'] = {
                'api_key': options['oanda_api_key'],
                'account_id': options['oanda_account_id']
            }
        
        if 'forexcom' in options['providers']:
            providers_config['forexcom'] = {}
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting WebSocket service for symbols: {symbols}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Providers: {list(providers_config.keys())}')
        )
        
        try:
            # Start real-time data store
            real_time_data_store.start()
            self.stdout.write(
                self.style.SUCCESS('Real-time data store started')
            )
            
            # Start WebSocket manager
            websocket_manager.start(symbols, providers_config)
            self.stdout.write(
                self.style.SUCCESS('WebSocket manager started')
            )
            
            # Keep the service running
            self.stdout.write(
                self.style.SUCCESS('WebSocket service is running... Press Ctrl+C to stop')
            )
            
            # Print status updates every 30 seconds
            while True:
                time.sleep(30)
                stats = real_time_data_store.get_statistics()
                connections = real_time_data_store.get_connection_status()
                
                self.stdout.write(
                    f"[{timezone.now().strftime('%H:%M:%S')}] "
                    f"Ticks: {stats.get('total_ticks', 0)}, "
                    f"Candles: {stats.get('total_candles', 0)}, "
                    f"Active symbols: {stats.get('active_symbols', 0)}, "
                    f"Connections: {len(connections)}"
                )
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('Stopping WebSocket service...')
            )
            
            # Stop services
            websocket_manager.stop()
            real_time_data_store.stop()
            
            self.stdout.write(
                self.style.SUCCESS('WebSocket service stopped')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running WebSocket service: {e}')
            )
