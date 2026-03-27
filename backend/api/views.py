"""
Django REST Framework Views for Forex Alpha API
Endpoints:
  GET  /api/symbols/              – list available symbols
  GET  /api/forex-data/           – OHLCV data from InfluxDB
  GET  /api/economic-indicators/  – from PostgreSQL
  POST /api/signals/              – generate multi-agent + RLM signals
  POST /api/signals/train-rl/     – trigger Q-table training
  GET  /api/signals/history/      – stored signal logs
  POST /api/chat/                 – LangChain AI chat
  POST /api/chat/explain/         – explain a specific signal
"""

import sys
import os

# Make the workspace root importable (agents/, ml_models.py, etc.)
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import uuid
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

# Local
from .models import SignalLog, LangChainSession
from .serializers import (
    SignalLogSerializer, ForexDataRequestSerializer,
    SignalRequestSerializer, ChatRequestSerializer, TrainRLRequestSerializer,
)
from .rl_agent import RLMSignalAgent
from .langchain_service import get_langchain_service

# Agents (from workspace root)
try:
    from agents.ensemble_agent import EnsembleAgent
    from agents.technical_agent import TechnicalAgent
    from agents.fundamental_agent import FundamentalAgent
    from agents.sentiment_agent import SentimentAgent
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False

# InfluxDB
try:
    from influxdb_client import InfluxDBClient
    INFLUX_AVAILABLE = True
except ImportError:
    INFLUX_AVAILABLE = False

# PostgreSQL
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

# ── Singletons ──────────────────────────────────────────────
_rl_agent = RLMSignalAgent(
    model_dir=os.path.join(WORKSPACE_ROOT, 'models_rl')
)


def _get_influx_client():
    if not INFLUX_AVAILABLE:
        return None
    return InfluxDBClient(
        url=settings.INFLUXDB_URL,
        token=settings.INFLUXDB_TOKEN,
        org=settings.INFLUXDB_ORG,
    )


def _get_pg_conn():
    """
    Direct psycopg2 connection to the forex_metadata PostgreSQL database.
    Uses the same Windows cp1252 encoding workaround as the original app.py:
    temporarily strip LANG/LC_ env vars so libpq doesn't pick up a Latin-1
    locale, and force PGCLIENTENCODING=UTF8.
    Django's own ORM uses SQLite (see settings.py), so this path is only taken
    for reading pre-existing forex_metadata data (economic indicators etc.).
    """
    if not PSYCOPG2_AVAILABLE:
        return None
    import os as _os
    old_env = _os.environ.copy()
    try:
        for k in [k for k in list(_os.environ) if k.startswith(('LANG', 'LC_'))]:
            del _os.environ[k]
        _os.environ['PGCLIENTENCODING'] = 'UTF8'
        _os.environ['PGPASSFILE'] = 'NUL'
        conn = psycopg2.connect(
            host=_os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(_os.getenv('POSTGRES_PORT', '5432')),
            database=_os.getenv('POSTGRES_DB', 'forex_metadata'),
            user=_os.getenv('POSTGRES_USER', 'forex_user'),
            password=_os.getenv('POSTGRES_PASSWORD', 'forex_pass_2026'),
        )
        conn.set_client_encoding('UTF8')
        return conn
    except Exception:
        return None
    finally:
        _os.environ.clear()
        _os.environ.update(old_env)


# ── Helpers ─────────────────────────────────────────────────
def _fetch_ohlcv(symbol: str, timeframe: str, days_back: int) -> pd.DataFrame:
    """Fetch OHLCV from InfluxDB; fall back to demo data."""
    client = _get_influx_client()
    if client:
        try:
            query_api = client.query_api()
            query = f'''
            from(bucket: "{settings.INFLUXDB_BUCKET}")
                |> range(start: -{days_back}d)
                |> filter(fn: (r) => r["_measurement"] == "forex_prices")
                |> filter(fn: (r) => r["symbol"] == "{symbol}")
                |> filter(fn: (r) => r["timeframe"] == "{timeframe}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            df = query_api.query_data_frame(query)
            if not df.empty:
                df['_time'] = pd.to_datetime(df['_time'])
                df = df.sort_values('_time').rename(columns={'_time': 'time'})
                return df
        except Exception:
            pass
    # Demo fallback
    return _generate_demo_ohlcv(symbol, days_back)


def _generate_demo_ohlcv(symbol: str, days_back: int = 30) -> pd.DataFrame:
    """Generate realistic-looking demo OHLCV data."""
    np.random.seed(hash(symbol) % (2 ** 31))
    base = {'EURUSD': 1.08, 'GBPUSD': 1.27, 'USDJPY': 149.5,
            'USDCHF': 0.90, 'AUDUSD': 0.65}.get(symbol, 1.0)
    n = days_back * 24  # hourly bars
    times = pd.date_range(end=datetime.utcnow(), periods=n, freq='h')
    returns = np.random.normal(0, 0.0005, n)
    closes = base * np.cumprod(1 + returns)
    highs = closes * (1 + np.abs(np.random.normal(0, 0.001, n)))
    lows = closes * (1 - np.abs(np.random.normal(0, 0.001, n)))
    opens = closes * (1 + np.random.normal(0, 0.0003, n))
    volumes = np.random.randint(500, 5000, n).astype(float)
    return pd.DataFrame({
        'time': times, 'open': opens, 'high': highs,
        'low': lows, 'close': closes, 'volume': volumes,
    })


def _build_ensemble_signal(symbol: str, df: pd.DataFrame) -> dict:
    """Run the multi-agent ensemble if available."""
    if not AGENTS_AVAILABLE or df.empty:
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': symbol,
            'direction': 'HOLD',
            'confidence': 0.5,
            'agent_name': 'Ensemble',
            'reasoning': 'Agents not available or no data.',
            'individual_signals': [],
        }
    try:
        ensemble = EnsembleAgent()
        result = ensemble.analyze(symbol=symbol, forex_data=df)
        return result
    except Exception as e:
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': symbol,
            'direction': 'HOLD',
            'confidence': 0.0,
            'agent_name': 'Ensemble',
            'reasoning': f'Ensemble error: {e}',
            'individual_signals': [],
        }


# ════════════════════════════════════════════════════════════
#  Views
# ════════════════════════════════════════════════════════════

class SymbolsView(APIView):
    """GET /api/symbols/ — list available currency pairs"""

    def get(self, request):
        symbols = [
            {'symbol': 'EURUSD', 'description': 'Euro / US Dollar', 'category': 'Major'},
            {'symbol': 'GBPUSD', 'description': 'British Pound / US Dollar', 'category': 'Major'},
            {'symbol': 'USDJPY', 'description': 'US Dollar / Japanese Yen', 'category': 'Major'},
            {'symbol': 'USDCHF', 'description': 'US Dollar / Swiss Franc', 'category': 'Major'},
            {'symbol': 'AUDUSD', 'description': 'Australian Dollar / US Dollar', 'category': 'Major'},
            {'symbol': 'USDCAD', 'description': 'US Dollar / Canadian Dollar', 'category': 'Major'},
            {'symbol': 'NZDUSD', 'description': 'New Zealand Dollar / US Dollar', 'category': 'Major'},
            {'symbol': 'EURGBP', 'description': 'Euro / British Pound', 'category': 'Cross'},
            {'symbol': 'EURJPY', 'description': 'Euro / Japanese Yen', 'category': 'Cross'},
            {'symbol': 'GBPJPY', 'description': 'British Pound / Japanese Yen', 'category': 'Cross'},
        ]
        return Response(symbols)


class TimeframesView(APIView):
    """GET /api/timeframes/ — list available timeframes"""

    def get(self, request):
        timeframes = [
            {'value': 'M1',  'label': '1 Minute'},
            {'value': 'M5',  'label': '5 Minutes'},
            {'value': 'M15', 'label': '15 Minutes'},
            {'value': 'M30', 'label': '30 Minutes'},
            {'value': 'H1',  'label': '1 Hour'},
            {'value': 'H4',  'label': '4 Hours'},
            {'value': 'D1',  'label': '1 Day'},
            {'value': 'W1',  'label': '1 Week'},
        ]
        return Response(timeframes)


class ForexDataView(APIView):
    """GET /api/forex-data/?symbol=EURUSD&timeframe=H1&days_back=30"""

    def get(self, request):
        serializer = ForexDataRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        symbol = serializer.validated_data['symbol']
        timeframe = serializer.validated_data['timeframe']
        days_back = serializer.validated_data['days_back']

        df = _fetch_ohlcv(symbol, timeframe, days_back)

        if df.empty:
            return Response({'error': 'No data found'}, status=status.HTTP_404_NOT_FOUND)

        # Convert to records – stringify timestamps
        df['time'] = df['time'].astype(str)
        records = df[['time', 'open', 'high', 'low', 'close', 'volume']].to_dict('records')

        return Response({
            'symbol': symbol,
            'timeframe': timeframe,
            'days_back': days_back,
            'count': len(records),
            'data': records,
        })


class EconomicIndicatorsView(APIView):
    """GET /api/economic-indicators/"""

    def get(self, request):
        conn = _get_pg_conn()
        if conn is None:
            return Response({'error': 'PostgreSQL not available',
                             'data': []}, status=status.HTTP_200_OK)
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT series_id, series_name, value, date, units, frequency
                    FROM economic_indicators
                    ORDER BY date DESC
                    LIMIT 200
                ''')
                cols = [d[0] for d in cur.description]
                rows = [dict(zip(cols, row)) for row in cur.fetchall()]
            return Response({'count': len(rows), 'data': rows})
        except Exception as e:
            return Response({'error': str(e), 'data': []})
        finally:
            conn.close()


class SignalsView(APIView):
    """POST /api/signals/ — generate multi-agent + RLM signals"""

    def post(self, request):
        serializer = SignalRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        symbol = serializer.validated_data['symbol']
        timeframe = serializer.validated_data['timeframe']
        days_back = serializer.validated_data['days_back']
        include_rl = serializer.validated_data['include_rl']
        include_langchain = serializer.validated_data['include_langchain']
        session_id = serializer.validated_data.get('session_id', 'default')

        df = _fetch_ohlcv(symbol, timeframe, days_back)

        # 1. Ensemble signal
        ensemble_signal = _build_ensemble_signal(symbol, df)

        # 2. RLM signal
        rl_signal = None
        if include_rl:
            rl_signal = _rl_agent.generate_signal(symbol, df)

        # 3. Final combined signal
        signals_list = [ensemble_signal]
        if rl_signal:
            signals_list.append(rl_signal)

        # Merge: average confidence, majority direction
        directions = [s['direction'] for s in signals_list]
        from collections import Counter
        final_direction = Counter(directions).most_common(1)[0][0]
        final_confidence = float(np.mean([s['confidence'] for s in signals_list]))

        combined = {
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': symbol,
            'direction': final_direction,
            'confidence': round(final_confidence, 4),
            'ensemble_signal': ensemble_signal,
            'rl_signal': rl_signal,
        }

        # 4. LangChain explanation
        if include_langchain:
            lc = get_langchain_service()
            market_ctx = {
                'symbol': symbol,
                'current_price': float(df['close'].iloc[-1]) if not df.empty else None,
                'price_change_1d': (
                    float((df['close'].iloc[-1] - df['close'].iloc[-24]) /
                          df['close'].iloc[-24] * 100)
                    if len(df) > 24 else None
                ),
            }
            combined['ai_explanation'] = lc.explain_signal(
                session_id, combined, market_ctx
            )

        # 5. Persist to DB
        try:
            SignalLog.objects.create(
                symbol=symbol,
                direction=final_direction,
                confidence=final_confidence,
                agent_name='Ensemble+RLM',
                reasoning=ensemble_signal.get('reasoning', ''),
                rl_action=rl_signal.get('direction') if rl_signal else None,
            )
        except Exception:
            pass  # DB might not be migrated yet

        return Response(combined)


class SignalHistoryView(APIView):
    """GET /api/signals/history/?symbol=EURUSD&limit=50"""

    def get(self, request):
        symbol = request.query_params.get('symbol', '')
        limit = int(request.query_params.get('limit', 50))
        qs = SignalLog.objects.all()
        if symbol:
            qs = qs.filter(symbol=symbol)
        qs = qs[:limit]
        data = SignalLogSerializer(qs, many=True).data
        return Response({'count': len(data), 'signals': data})


class TrainRLView(APIView):
    """POST /api/signals/train-rl/ — trigger Q-table training"""

    def post(self, request):
        serializer = TrainRLRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        symbol = serializer.validated_data['symbol']
        timeframe = serializer.validated_data['timeframe']
        days_back = serializer.validated_data['days_back']
        episodes = serializer.validated_data['episodes']

        df = _fetch_ohlcv(symbol, timeframe, days_back)
        if df.empty:
            return Response({'error': 'No training data found'}, status=400)

        result = _rl_agent.train_qtable(symbol, df, episodes=episodes)
        return Response(result)


class ChatView(APIView):
    """POST /api/chat/ — free-form LangChain conversation"""

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        session_id = serializer.validated_data['session_id']
        message = serializer.validated_data['message']

        lc = get_langchain_service()
        reply = lc.chat(session_id, message)

        # Persist session
        try:
            session, _ = LangChainSession.objects.get_or_create(
                session_id=session_id,
                defaults={'symbol': serializer.validated_data.get('symbol', '')}
            )
            msgs = session.messages or []
            msgs.append({'role': 'user', 'content': message, 'ts': datetime.utcnow().isoformat()})
            msgs.append({'role': 'assistant', 'content': reply, 'ts': datetime.utcnow().isoformat()})
            session.messages = msgs[-100:]  # keep last 100 messages
            session.save()
        except Exception:
            pass

        return Response({'session_id': session_id, 'reply': reply})


class ChatExplainView(APIView):
    """POST /api/chat/explain/ — explain a signal dict with LangChain"""

    def post(self, request):
        signal = request.data.get('signal')
        if not signal:
            return Response({'error': 'signal is required'}, status=400)
        session_id = request.data.get('session_id', str(uuid.uuid4()))
        market_context = request.data.get('market_context', {})

        lc = get_langchain_service()
        explanation = lc.explain_signal(session_id, signal, market_context)
        return Response({'session_id': session_id, 'explanation': explanation})


class HealthView(APIView):
    """GET /api/health/"""

    def get(self, request):
        return Response({
            'status': 'ok',
            'timestamp': datetime.utcnow().isoformat(),
            'agents_available': AGENTS_AVAILABLE,
            'influx_available': INFLUX_AVAILABLE,
            'psycopg2_available': PSYCOPG2_AVAILABLE,
        })
