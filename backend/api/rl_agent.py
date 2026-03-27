"""
Reinforcement Learning Model (RLM) for Forex Signal Generation
Uses a Proximal Policy Optimization (PPO) style agent with a tabular
Q-learning fallback when Stable-Baselines3 is not available.
"""

import numpy as np
import pandas as pd
import os
import json
import joblib
from typing import Dict, Optional, Tuple
from datetime import datetime


# ─────────────────────────────────────────────
#  Optional: Stable-Baselines3 (SB3) / Gymnasium
# ─────────────────────────────────────────────
try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv
    import gymnasium as gym
    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False


# ─────────────────────────────────────────────
#  Gymnasium trading environment  (optional)
# ─────────────────────────────────────────────
if SB3_AVAILABLE:
    class ForexTradingEnv(gym.Env):
        """
        Simple Forex trading gym environment.
        Observation: last N OHLCV rows flattened + position.
        Action: 0=HOLD, 1=BUY, 2=SELL
        """

        metadata = {"render_modes": []}

        def __init__(self, df: pd.DataFrame, window: int = 20):
            super().__init__()
            self.df = df.reset_index(drop=True)
            self.window = window
            self.n_features = 5  # open, high, low, close, volume
            obs_size = window * self.n_features + 1  # +1 for current position

            self.observation_space = gym.spaces.Box(
                low=-np.inf, high=np.inf, shape=(obs_size,), dtype=np.float32
            )
            self.action_space = gym.spaces.Discrete(3)  # 0=HOLD,1=BUY,2=SELL
            self.reset()

        def _get_obs(self) -> np.ndarray:
            start = max(0, self.current_step - self.window)
            end = self.current_step
            rows = self.df.iloc[start:end]
            pad = self.window - len(rows)

            arr = rows[['open', 'high', 'low', 'close', 'volume']].values
            if pad > 0:
                arr = np.vstack([np.zeros((pad, 5)), arr])
            # Normalise by last close
            last_close = arr[-1, 3] if arr[-1, 3] != 0 else 1.0
            arr = arr / last_close
            return np.append(arr.flatten().astype(np.float32), float(self.position))

        def reset(self, *, seed=None, options=None):
            super().reset(seed=seed)
            self.current_step = self.window
            self.position = 0  # 0=flat, 1=long, -1=short
            self.entry_price = 0.0
            self.total_pnl = 0.0
            return self._get_obs(), {}

        def step(self, action: int):
            price = float(self.df.iloc[self.current_step]['close'])
            reward = 0.0

            if action == 1 and self.position <= 0:   # BUY
                self.entry_price = price
                self.position = 1
            elif action == 2 and self.position >= 0: # SELL
                self.entry_price = price
                self.position = -1
            elif action == 0:                        # HOLD
                if self.position == 1:
                    reward = (price - self.entry_price) / (self.entry_price or 1)
                elif self.position == -1:
                    reward = (self.entry_price - price) / (self.entry_price or 1)

            self.total_pnl += reward
            self.current_step += 1
            done = self.current_step >= len(self.df) - 1
            truncated = False
            return self._get_obs(), reward, done, truncated, {}


# ─────────────────────────────────────────────
#  Q-table fallback (no SB3 dependency)
# ─────────────────────────────────────────────
class QTableAgent:
    """
    Lightweight tabular Q-learning agent used when SB3 is unavailable.
    State is discretised from the last 5 closes trend + RSI bucket.
    """

    ACTIONS = {0: 'HOLD', 1: 'BUY', 2: 'SELL'}
    N_STATES = 27  # 3 trend buckets x 3 momentum x 3 rsi = 27

    def __init__(self, lr: float = 0.1, gamma: float = 0.95,
                 epsilon: float = 0.1):
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table = np.zeros((self.N_STATES, 3))

    def _state(self, df: pd.DataFrame) -> int:
        closes = df['close'].values[-10:] if len(df) >= 10 else df['close'].values
        if len(closes) < 2:
            return 0
        # Trend bucket: 0=down, 1=flat, 2=up
        ret = (closes[-1] - closes[0]) / (closes[0] or 1)
        trend = 0 if ret < -0.001 else (2 if ret > 0.001 else 1)

        # Momentum bucket
        short = closes[-1] - closes[-min(3, len(closes))]
        mom = 0 if short < 0 else (2 if short > 0 else 1)

        # RSI-like bucket
        diffs = np.diff(closes)
        gains = diffs[diffs > 0].sum()
        losses = -diffs[diffs < 0].sum()
        rs = gains / (losses + 1e-9)
        rsi = 100 - 100 / (1 + rs)
        rsi_b = 0 if rsi < 35 else (2 if rsi > 65 else 1)

        return int(trend * 9 + mom * 3 + rsi_b)

    def predict(self, df: pd.DataFrame) -> Tuple[int, float]:
        state = self._state(df)
        if np.random.rand() < self.epsilon:
            action = np.random.randint(3)
        else:
            action = int(np.argmax(self.q_table[state]))
        confidence = float(np.max(self.q_table[state]))
        # Map raw Q value to a confidence in [0.3, 0.95]
        confidence = min(0.95, max(0.3, 0.5 + confidence * 0.1))
        return action, confidence

    def update(self, state_df: pd.DataFrame, action: int,
               reward: float, next_df: pd.DataFrame):
        s = self._state(state_df)
        s_next = self._state(next_df)
        td_target = reward + self.gamma * np.max(self.q_table[s_next])
        self.q_table[s, action] += self.lr * (td_target - self.q_table[s, action])

    def save(self, path: str):
        np.save(path, self.q_table)

    def load(self, path: str):
        if os.path.exists(path):
            self.q_table = np.load(path)


# ─────────────────────────────────────────────
#  High-level RLM Service
# ─────────────────────────────────────────────
class RLMSignalAgent:
    """
    Unified RL signal agent.
    • Uses PPO (SB3) if available and a pretrained model exists.
    • Falls back to Q-table otherwise.
    Exposes a single `generate_signal(symbol, df)` method that returns
    the same dict format as the ensemble agents.
    """

    ACTION_MAP = {0: 'HOLD', 1: 'BUY', 2: 'SELL'}

    def __init__(self, model_dir: str = 'models_rl'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self._agents: Dict[str, object] = {}

    def _load_or_create(self, symbol: str):
        if symbol in self._agents:
            return self._agents[symbol]

        if SB3_AVAILABLE:
            model_path = os.path.join(self.model_dir, f'{symbol}_ppo.zip')
            if os.path.exists(model_path):
                agent = PPO.load(model_path)
                self._agents[symbol] = ('ppo', agent)
                return self._agents[symbol]

        # Fallback Q-table
        qt_path = os.path.join(self.model_dir, f'{symbol}_qtable.npy')
        agent = QTableAgent()
        agent.load(qt_path)
        self._agents[symbol] = ('qtable', agent)
        return self._agents[symbol]

    # ----------------------------------------------------------
    def generate_signal(self, symbol: str, df: pd.DataFrame) -> Dict:
        """
        Generate a trading signal from the RL model.

        Parameters
        ----------
        symbol : str
            Currency pair, e.g. 'EURUSD'
        df : pd.DataFrame
            OHLCV dataframe with columns: open, high, low, close, volume

        Returns
        -------
        dict  with keys: direction, confidence, agent_name, reasoning,
              rl_action_idx, timestamp
        """
        if df is None or df.empty:
            return self._hold_signal(symbol, "No data available")

        kind, agent = self._load_or_create(symbol)

        if kind == 'ppo':
            # Build a dummy env observation
            env = ForexTradingEnv(df.tail(100))
            obs, _ = env.reset()
            action, _ = agent.predict(obs, deterministic=True)
            action = int(action)
            confidence = 0.72  # PPO doesn't expose simple confidence
        else:
            action, confidence = agent.predict(df)

        direction = self.ACTION_MAP.get(action, 'HOLD')

        # Build human-readable reasoning
        recent = df.tail(5)
        close_change = (
            (recent['close'].iloc[-1] - recent['close'].iloc[0]) /
            (recent['close'].iloc[0] + 1e-9) * 100
        )
        reasoning = (
            f"RL ({kind.upper()}) action={direction} | "
            f"5-bar return={close_change:+.3f}% | "
            f"confidence={confidence:.2f}"
        )

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': symbol,
            'direction': direction,
            'confidence': confidence,
            'agent_name': f'RLM-{kind.upper()}',
            'reasoning': reasoning,
            'rl_action_idx': action,
        }

    def train_qtable(self, symbol: str, df: pd.DataFrame,
                     episodes: int = 50) -> Dict:
        """Quick online Q-table training on historical data."""
        qt_path = os.path.join(self.model_dir, f'{symbol}_qtable.npy')
        agent = QTableAgent(epsilon=0.3)
        agent.load(qt_path)

        for _ in range(episodes):
            for i in range(10, len(df) - 1):
                state_df = df.iloc[:i]
                next_df = df.iloc[:i + 1]
                action, _ = agent.predict(state_df)
                current_price = df.iloc[i]['close']
                next_price = df.iloc[i + 1]['close']
                reward = (next_price - current_price) / (current_price + 1e-9)
                if action == 2:  # SELL
                    reward = -reward
                elif action == 0:
                    reward = 0.0
                agent.update(state_df, action, reward, next_df)

        agent.save(qt_path)
        # Invalidate cache
        self._agents.pop(symbol, None)
        return {'status': 'trained', 'symbol': symbol, 'episodes': episodes}

    # ----------------------------------------------------------
    @staticmethod
    def _hold_signal(symbol: str, reason: str) -> Dict:
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': symbol,
            'direction': 'HOLD',
            'confidence': 0.0,
            'agent_name': 'RLM',
            'reasoning': reason,
            'rl_action_idx': 0,
        }
