"""
Django management command for MCP Agent Collecteur
Usage:
    python manage.py mcp_collecteur start
    python manage.py mcp_collecteur stop
    python manage.py mcp_collecteur status
    python manage.py mcp_collecteur context
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import json


class Command(BaseCommand):
    help = 'MCP Agent Collecteur - Modern data collection with Model Context Protocol'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['start', 'stop', 'status', 'context', 'tools'],
            help='Action to perform: start, stop, status, context, tools'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'start':
            self.start_mcp_agent()
        elif action == 'stop':
            self.stop_mcp_agent()
        elif action == 'status':
            self.show_status()
        elif action == 'context':
            self.show_context()
        elif action == 'tools':
            self.show_tools()
    
    def start_mcp_agent(self):
        """Start MCP Agent Collecteur"""
        try:
            from mcp_agent_collecteur import get_mcp_agent_collecteur
            
            self.stdout.write(self.style.SUCCESS('🚀 Starting MCP Agent Collecteur...'))
            
            # Get and start the agent
            agent = get_mcp_agent_collecteur()
            agent.start_collection()
            
            self.stdout.write(self.style.SUCCESS('✅ MCP Agent Collecteur Started!'))
            self.stdout.write('🤖 Agent Features:')
            self.stdout.write('   • Model Context Protocol (MCP) integration')
            self.stdout.write('   • Real-time MT5 price data collection')
            self.stdout.write('   • RSS news feed collection')
            self.stdout.write('   • FRED economic indicators')
            self.stdout.write('   • Intelligent data quality analysis')
            self.stdout.write('   • Automatic optimization')
            self.stdout.write('')
            self.stdout.write('📊 Collection Intervals:')
            self.stdout.write('   • MT5 Price Data: Every 60 seconds')
            self.stdout.write('   • RSS News: Every 5 minutes')
            self.stdout.write('   • FRED Indicators: Every 1 hour')
            self.stdout.write('')
            self.stdout.write('💡 Commands:')
            self.stdout.write('   python manage.py mcp_collecteur status')
            self.stdout.write('   python manage.py mcp_collecteur context')
            self.stdout.write('   python manage.py mcp_collecteur tools')
            
        except Exception as e:
            raise CommandError(f'Failed to start MCP Agent: {e}')
    
    def stop_mcp_agent(self):
        """Stop MCP Agent Collecteur"""
        try:
            from mcp_agent_collecteur import get_mcp_agent_collecteur
            
            self.stdout.write(self.style.WARNING('🛑 Stopping MCP Agent Collecteur...'))
            
            agent = get_mcp_agent_collecteur()
            agent.stop_collection()
            
            self.stdout.write(self.style.SUCCESS('✅ MCP Agent Collecteur Stopped'))
            
        except Exception as e:
            raise CommandError(f'Failed to stop MCP Agent: {e}')
    
    def show_status(self):
        """Show MCP Agent status"""
        try:
            from mcp_agent_collecteur import get_mcp_agent_collecteur
            
            agent = get_mcp_agent_collecteur()
            stats = agent.get_statistics()
            
            self.stdout.write(self.style.SUCCESS('📊 MCP Agent Collecteur Status'))
            self.stdout.write('=' * 50)
            
            # Basic status
            status = "🟢 Running" if agent.is_running else "🔴 Stopped"
            self.stdout.write(f'🔄 Status: {status}')
            self.stdout.write(f'🆔 Session: {agent.session_id}')
            self.stdout.write(f'⏱️  Uptime: {stats["uptime_seconds"]:.0f} seconds')
            
            # Collection statistics
            self.stdout.write('')
            self.stdout.write('📈 Collection Statistics:')
            self.stdout.write(f'   • Total Collections: {stats["total_collections"]}')
            self.stdout.write(f'   • Successful: {stats["successful_collections"]}')
            self.stdout.write(f'   • Failed: {stats["failed_collections"]}')
            self.stdout.write(f'   • Success Rate: {stats["success_rate"]:.1%}')
            self.stdout.write(f'   • Data Points: {stats["data_points_collected"]}')
            self.stdout.write(f'   • Points/Hour: {stats["data_points_per_hour"]:.1f}')
            
            # Data sources status
            self.stdout.write('')
            self.stdout.write('🗄️  Data Sources Status:')
            for source, config in agent.data_sources.items():
                status_icon = "🟢" if config['status'] == 'active' else "🔴" if config['status'] == 'inactive' else "🟡"
                self.stdout.write(f'   {status_icon} {source}: {config["status"]}')
                if config.get('last_update'):
                    self.stdout.write(f'      Last Update: {config["last_update"]}')
                if config.get('total_updates', 0) > 0:
                    self.stdout.write(f'      Total Updates: {config["total_updates"]}')
            
            # Last activity
            if stats.get('last_activity'):
                self.stdout.write('')
                self.stdout.write(f'🕐 Last Activity: {stats["last_activity"]}')
            
        except Exception as e:
            raise CommandError(f'Failed to get status: {e}')
    
    def show_context(self):
        """Show MCP context"""
        try:
            from mcp_agent_collecteur import get_mcp_agent_collecteur
            
            agent = get_mcp_agent_collecteur()
            context = agent.get_mcp_context()
            
            self.stdout.write(self.style.SUCCESS('🤖 MCP Agent Collecteur Context'))
            self.stdout.write('=' * 50)
            
            self.stdout.write(f'🆔 Session ID: {context["session_id"]}')
            self.stdout.write(f'🤖 Agent Name: {context["agent_name"]}')
            self.stdout.write(f'⏰ Timestamp: {context["timestamp"]}')
            
            self.stdout.write('')
            self.stdout.write('🛠️  Available Tools:')
            for i, tool in enumerate(context["tools_available"], 1):
                self.stdout.write(f'   {i}. {tool}')
            
            self.stdout.write('')
            self.stdout.write('📊 Data Sources:')
            for source, status in context["collection_status"].items():
                status_icon = "🟢" if status == 'active' else "🔴" if status == 'inactive' else "🟡"
                self.stdout.write(f'   {status_icon} {source}: {status}')
            
        except Exception as e:
            raise CommandError(f'Failed to get context: {e}')
    
    def show_tools(self):
        """Show MCP tools details"""
        try:
            from mcp_agent_collecteur import get_mcp_agent_collecteur
            
            agent = get_mcp_agent_collecteur()
            
            self.stdout.write(self.style.SUCCESS('🛠️  MCP Agent Collecteur Tools'))
            self.stdout.write('=' * 50)
            
            for i, tool in enumerate(agent.tools, 1):
                self.stdout.write(f'{i}. 📦 {tool.name.upper()}')
                self.stdout.write(f'   📝 Description: {tool.description}')
                self.stdout.write(f'   ⚙️  Parameters: {list(tool.parameters.keys())}')
                self.stdout.write('')
            
            self.stdout.write('🔧 Tool Capabilities:')
            self.stdout.write('   • collect_mt5_data: Real-time price collection from MetaTrader5')
            self.stdout.write('   • collect_rss_news: News articles from multiple RSS feeds')
            self.stdout.write('   • collect_fred_data: Economic indicators from FRED API')
            self.stdout.write('   • store_influxdb: Time-series data storage')
            self.stdout.write('   • store_postgresql: Relational data storage')
            self.stdout.write('   • analyze_data_quality: Data quality assessment')
            self.stdout.write('   • optimize_collection: Performance optimization')
            
        except Exception as e:
            raise CommandError(f'Failed to show tools: {e}')
