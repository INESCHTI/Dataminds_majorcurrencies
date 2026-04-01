"""
Django management command for MCP Agent Feeder
Usage:
    python manage.py mcp_feeder start
    python manage.py mcp_feeder stop
    python manage.py mcp_feeder status
    python manage.py mcp_feeder feeds
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = 'MCP Agent Feeder - Specialized data distribution to agents'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['start', 'stop', 'status', 'feeds', 'agents'],
            help='Action to perform: start, stop, status, feeds, agents'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'start':
            self.start_feeder()
        elif action == 'stop':
            self.stop_feeder()
        elif action == 'status':
            self.show_status()
        elif action == 'feeds':
            self.show_feeds()
        elif action == 'agents':
            self.show_agents()
    
    def start_feeder(self):
        """Start MCP Agent Feeder"""
        try:
            from mcp_agent_feeder import get_mcp_agent_feeder
            
            self.stdout.write(self.style.SUCCESS('🚀 Starting MCP Agent Feeder...'))
            
            # Get and start the feeder
            feeder = get_mcp_agent_feeder()
            feeder.start_feeding()
            
            self.stdout.write(self.style.SUCCESS('✅ MCP Agent Feeder Started!'))
            self.stdout.write('🤖 Agent Data Feeding System:')
            self.stdout.write('   • Technical Agent: Real-time price data + indicators')
            self.stdout.write('   • Macro Agent: Economic indicators + calendar data')
            self.stdout.write('   • Sentiment Agent: News sentiment + social data')
            self.stdout.write('   • Geopolitical Agent: Political events + risk analysis')
            self.stdout.write('   • Coordinator Agent: All agent signals + overview')
            self.stdout.write('')
            self.stdout.write('📊 Feeding Frequencies:')
            self.stdout.write('   • Technical Agent: Every 60 seconds')
            self.stdout.write('   • Macro Agent: Every 5 minutes')
            self.stdout.write('   • Sentiment Agent: Every 3 minutes')
            self.stdout.write('   • Geopolitical Agent: Every 4 minutes')
            self.stdout.write('   • Coordinator Agent: Every 2 minutes')
            self.stdout.write('')
            self.stdout.write('💡 Commands:')
            self.stdout.write('   python manage.py mcp_feeder status')
            self.stdout.write('   python manage.py mcp_feeder feeds')
            self.stdout.write('   python manage.py mcp_feeder agents')
            
        except Exception as e:
            raise CommandError(f'Failed to start MCP Feeder: {e}')
    
    def stop_feeder(self):
        """Stop MCP Agent Feeder"""
        try:
            from mcp_agent_feeder import get_mcp_agent_feeder
            
            self.stdout.write(self.style.WARNING('🛑 Stopping MCP Agent Feeder...'))
            
            feeder = get_mcp_agent_feeder()
            feeder.stop_feeding()
            
            self.stdout.write(self.style.SUCCESS('✅ MCP Agent Feeder Stopped'))
            
        except Exception as e:
            raise CommandError(f'Failed to stop MCP Feeder: {e}')
    
    def show_status(self):
        """Show MCP Feeder status"""
        try:
            from mcp_agent_feeder import get_mcp_agent_feeder
            
            feeder = get_mcp_agent_feeder()
            stats = feeder.get_feeding_statistics()
            
            self.stdout.write(self.style.SUCCESS('📊 MCP Agent Feeder Status'))
            self.stdout.write('=' * 50)
            
            # Basic status
            status = "🟢 Running" if feeder.is_running else "🔴 Stopped"
            self.stdout.write(f'🔄 Status: {status}')
            self.stdout.write(f'⏱️  Uptime: {stats["uptime_seconds"]:.0f} seconds')
            
            # Feeding statistics
            self.stdout.write('')
            self.stdout.write('📈 Feeding Statistics:')
            self.stdout.write(f'   • Total Feeds: {stats["total_feeds"]}')
            self.stdout.write(f'   • Successful: {stats["successful_feeds"]}')
            self.stdout.write(f'   • Failed: {stats["failed_feeds"]}')
            self.stdout.write(f'   • Success Rate: {stats["success_rate"]:.1%}')
            self.stdout.write(f'   • Data Points: {stats["data_points_processed"]}')
            self.stdout.write(f'   • Points/Hour: {stats["data_points_per_hour"]:.1f}')
            
            # Agent-specific stats
            self.stdout.write('')
            self.stdout.write('🤖 Agent Feed Status:')
            for agent_name, agent_stats in stats["agent_feeds"].items():
                status_icon = "🟢" if agent_stats["is_active"] else "🔴"
                self.stdout.write(f'   {status_icon} {agent_name.title()} Agent:')
                self.stdout.write(f'      Updates: {stats["agent_updates"][agent_name]}')
                self.stdout.write(f'      Frequency: {agent_stats["update_frequency"]}s')
                self.stdout.write(f'      Data Types: {len(agent_stats["data_types"])}')
                if agent_stats["last_update"]:
                    self.stdout.write(f'      Last Update: {agent_stats["last_update"]}')
            
        except Exception as e:
            raise CommandError(f'Failed to get status: {e}')
    
    def show_feeds(self):
        """Show detailed feed configurations"""
        try:
            from mcp_agent_feeder import get_mcp_agent_feeder
            
            feeder = get_mcp_agent_feeder()
            
            self.stdout.write(self.style.SUCCESS('📡 MCP Agent Feeds Configuration'))
            self.stdout.write('=' * 50)
            
            for agent_name, feed in feeder.agent_feeds.items():
                self.stdout.write(f'🤖 {agent_name.title()} Agent Feed:')
                self.stdout.write(f'   📊 Data Types: {", ".join(feed.data_types)}')
                self.stdout.write(f'   ⏰ Update Frequency: {feed.update_frequency} seconds')
                self.stdout.write(f'   🎯 Active: {"Yes" if feed.is_active else "No"}')
                
                self.stdout.write('   🔍 Filters:')
                for filter_key, filter_value in feed.filters.items():
                    if isinstance(filter_value, list):
                        self.stdout.write(f'      • {filter_key}: {", ".join(filter_value[:3])}{"..." if len(filter_value) > 3 else ""}')
                    else:
                        self.stdout.write(f'      • {filter_key}: {filter_value}')
                
                self.stdout.write('')
            
        except Exception as e:
            raise CommandError(f'Failed to show feeds: {e}')
    
    def show_agents(self):
        """Show agent connections and capabilities"""
        try:
            from mcp_agent_feeder import get_mcp_agent_feeder
            
            feeder = get_mcp_agent_feeder()
            
            self.stdout.write(self.style.SUCCESS('🤖 Connected Agents'))
            self.stdout.write('=' * 50)
            
            for agent_name, agent in feeder.agents.items():
                self.stdout.write(f'🤖 {agent_name.title()} Agent:')
                self.stdout.write(f'   📦 Class: {agent.__class__.__name__}')
                
                # Show agent-specific capabilities
                if agent_name == 'technical':
                    self.stdout.write('   🎯 Specialization: Multi-timeframe technical analysis')
                    self.stdout.write('   📊 Data Focus: OHLCV, indicators, patterns')
                elif agent_name == 'macro':
                    self.stdout.write('   🎯 Specialization: Economic analysis')
                    self.stdout.write('   📊 Data Focus: GDP, CPI, interest rates, employment')
                elif agent_name == 'sentiment':
                    self.stdout.write('   🎯 Specialization: Market sentiment analysis')
                    self.stdout.write('   📊 Data Focus: News sentiment, social media, market mood')
                elif agent_name == 'geopolitical':
                    self.stdout.write('   🎯 Specialization: Political/event analysis')
                    self.stdout.write('   📊 Data Focus: Elections, conflicts, sanctions, risk events')
                elif agent_name == 'coordinator':
                    self.stdout.write('   🎯 Specialization: Multi-agent coordination')
                    self.stdout.write('   📊 Data Focus: All agent signals, weight optimization')
                
                self.stdout.write('')
            
        except Exception as e:
            raise CommandError(f'Failed to show agents: {e}')
