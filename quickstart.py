"""
Quick Start Script for Forex Alpha Prediction Platform
Demonstrates full pipeline from data to predictions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("🚀 FOREX ALPHA PREDICTION PLATFORM - QUICK START")
print("=" * 80)
print()

# Step 1: Check dependencies
print("Step 1: Checking dependencies...")
try:
    import streamlit
    import plotly
    import sklearn
    import xgboost
    import lightgbm
    print("✅ All core dependencies installed")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Please run: pip install -r requirements.txt")
    exit(1)

# Step 2: Generate sample data (for demonstration)
print("\nStep 2: Generating sample market data...")
dates = pd.date_range(start='2024-01-01', end='2026-02-23', freq='1H')
sample_data = pd.DataFrame({
    'open': np.random.randn(len(dates)).cumsum() + 1.1000,
    'high': np.random.randn(len(dates)).cumsum() + 1.1020,
    'low': np.random.randn(len(dates)).cumsum() + 1.0980,
    'close': np.random.randn(len(dates)).cumsum() + 1.1000,
    'volume': np.random.randint(1000, 10000, len(dates))
}, index=dates)
print(f"✅ Generated {len(sample_data):,} data points")

# Step 3: Feature engineering
print("\nStep 3: Creating features...")
try:
    from feature_engineering import FeatureEngineer
    
    fe = FeatureEngineer()
    features_df = fe.create_all_features(sample_data)
    print(f"✅ Created {len(fe.feature_names)} features")
except Exception as e:
    print(f"❌ Feature engineering failed: {e}")
    exit(1)

# Step 4: Train ML models
print("\nStep 4: Training ML models...")
try:
    from modeling_pipeline import ForexModelingPipeline
    
    pipeline = ForexModelingPipeline(symbol='EURUSD', horizon=5)
    prepared_data = pipeline.prepare_data(sample_data)
    print(f"✅ Data prepared: {len(prepared_data)} samples")
    
    print("\n   Training ensemble models (this may take a minute)...")
    training_summary = pipeline.train_models(train_size=0.7, val_size=0.15)
    
    print("\n   Training Results:")
    print(f"   - Train samples: {training_summary['train_size']}")
    print(f"   - Val samples: {training_summary['val_size']}")
    print(f"   - Test samples: {training_summary['test_size']}")
    print(f"   - Features: {training_summary['n_features']}")
    print(f"   - Test Accuracy: {training_summary['test_metrics']['accuracy']:.4f}")
    print(f"   - Test F1: {training_summary['test_metrics']['f1']:.4f}")
    
    print("\n✅ Models trained successfully")
except Exception as e:
    print(f"❌ Model training failed: {e}")
    exit(1)

# Step 5: Make predictions
print("\nStep 5: Making predictions...")
try:
    # Get latest data for prediction
    latest_data = sample_data.tail(200)
    prediction = pipeline.predict(latest_data)
    
    print(f"\n   📊 PREDICTION RESULTS:")
    print(f"   - Signal: {prediction['direction']}")
    print(f"   - Confidence: {prediction['confidence']:.2%}")
    print(f"   - ML Prediction: {prediction['ml_prediction']}")
    print(f"   - Agent Signal: {prediction['agent_signal']}")
    print(f"   - Timestamp: {prediction['timestamp']}")
    
    print("\n✅ Prediction generated successfully")
except Exception as e:
    print(f"❌ Prediction failed: {e}")
    exit(1)

# Step 6: Evaluate performance
print("\nStep 6: Evaluating model performance...")
try:
    from evaluation import ModelEvaluator
    
    evaluator = ModelEvaluator(initial_capital=10000.0)
    
    # Generate sample predictions for backtesting
    n_samples = 100
    predictions_df = pd.DataFrame({
        'direction': np.random.choice(['BUY', 'SELL', 'HOLD'], n_samples),
        'confidence': np.random.uniform(0.5, 0.95, n_samples)
    })
    prices = pd.Series(np.random.randn(n_samples).cumsum() + 1.1000)
    
    backtest_results = evaluator.backtest_strategy(
        predictions_df,
        prices,
        min_confidence=0.5
    )
    
    print(f"\n   💰 BACKTEST RESULTS:")
    print(f"   - Total Return: {backtest_results['total_return']*100:.2f}%")
    print(f"   - Final Capital: ${backtest_results['final_capital']:,.2f}")
    print(f"   - Number of Trades: {backtest_results['num_trades']}")
    print(f"   - Win Rate: {backtest_results['win_rate']*100:.2f}%")
    print(f"   - Sharpe Ratio: {backtest_results['sharpe_ratio']:.2f}")
    print(f"   - Max Drawdown: {backtest_results['max_drawdown']*100:.2f}%")
    
    print("\n✅ Evaluation complete")
except Exception as e:
    print(f"⚠️ Evaluation skipped: {e}")

# Step 7: Save models
print("\nStep 7: Saving trained models...")
try:
    import os
    os.makedirs('models_demo', exist_ok=True)
    pipeline.save_pipeline('models_demo/EURUSD')
    print("✅ Models saved to 'models_demo/EURUSD'")
except Exception as e:
    print(f"⚠️ Model saving skipped: {e}")

# Step 8: Launch dashboard
print("\n" + "=" * 80)
print("🎉 QUICK START COMPLETE!")
print("=" * 80)
print()
print("Next Steps:")
print()
print("1. 📊 Launch the deployment dashboard:")
print("   streamlit run deployment_app.py")
print()
print("2. 📈 View data explorer:")
print("   streamlit run app.py")
print()
print("3. 🧪 Run agent tests:")
print("   python test_agents.py")
print()
print("4. 📚 Read complete documentation:")
print("   TDSP_COMPLETE_DOCUMENTATION.md")
print()
print("5. 🔄 Acquire real data:")
print("   python acquire_mt5_data.py")
print("   python acquire_fred_data.py")
print("   python acquire_news_data.py")
print()
print("=" * 80)
print()

# Ask if user wants to launch dashboard
try:
    response = input("Launch deployment dashboard now? (y/n): ")
    if response.lower() == 'y':
        print("\nLaunching dashboard...")
        import subprocess
        import sys
        
        # Launch Streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "deployment_app.py"])
except KeyboardInterrupt:
    print("\n\nGoodbye! 👋")
except Exception as e:
    print(f"\nNote: {e}")
    print("\nYou can manually launch the dashboard with:")
    print("streamlit run deployment_app.py")
