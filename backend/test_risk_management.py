#!/usr/bin/env python
"""
Test script for risk management functionality
"""
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from risk_management.position_sizer import create_position_sizer, PositionSizingMethod

def test_risk_management():
    """Test the risk management system"""
    print("🛡️ Testing Risk Management System")
    print("=" * 50)
    
    # Create position sizer
    sizer = create_position_sizer(
        max_portfolio_risk=0.02,
        max_position_risk=0.01,
        account_balance=100000.0
    )
    
    print(f"💰 Account Balance: ${sizer.account_balance:,.2f}")
    print(f"📊 Risk Parameters:")
    print(f"   Max Portfolio Risk: {sizer.risk_params.max_portfolio_risk * 100:.1f}%")
    print(f"   Max Position Risk: {sizer.risk_params.max_position_risk * 100:.1f}%")
    print(f"   Max Positions: {sizer.risk_params.max_positions}")
    
    # Test position sizing with different methods
    test_cases = [
        {
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'entry_price': 1.0850,
            'stop_loss': 1.0750,
            'method': 'percentage',
            'confidence': 0.7,
            'volatility': 0.01
        },
        {
            'symbol': 'GBPUSD',
            'direction': 'SELL',
            'entry_price': 1.2650,
            'stop_loss': 1.2750,
            'method': 'fixed',
            'confidence': 0.8,
            'volatility': 0.012
        },
        {
            'symbol': 'USDJPY',
            'direction': 'BUY',
            'entry_price': 149.50,
            'stop_loss': 148.50,
            'method': 'volatility',
            'confidence': 0.6,
            'volatility': 0.015
        }
    ]
    
    print(f"\n📏 Testing Position Sizing Methods:")
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🎯 Test Case {i}: {case['symbol']} {case['direction']}")
        print(f"   Entry: {case['entry_price']}, Stop Loss: {case['stop_loss']}")
        
        try:
            method_enum = PositionSizingMethod(case['method'])
            position_size, details = sizer.calculate_position_size(
                symbol=case['symbol'],
                direction=case['direction'],
                entry_price=case['entry_price'],
                stop_loss=case['stop_loss'],
                method=method_enum,
                confidence=case['confidence'],
                volatility=case['volatility']
            )
            
            print(f"   ✅ Position Size: {position_size:,.2f}")
            print(f"   💸 Risk Amount: ${details['risk_amount']:,.2f}")
            print(f"   🎯 Take Profit: {details['take_profit']:.5f}")
            print(f"   📈 Risk/Reward: {details['risk_reward_ratio']:.2f}")
            print(f"   📊 Portfolio Risk: {details['portfolio_risk'] * 100:.2f}%")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test portfolio summary
    print(f"\n📊 Portfolio Summary:")
    summary = sizer.get_portfolio_summary()
    print(f"   Account Balance: ${summary['account_balance']:,.2f}")
    print(f"   Open Positions: {summary['open_positions']}")
    print(f"   Total Risk: ${summary['total_risk']:,.2f}")
    print(f"   Risk Utilization: {summary['risk_utilization'] * 100:.2f}%")
    
    # Test risk validation
    print(f"\n🔍 Risk Validation:")
    validation = sizer.validate_risk_limits()
    print(f"   Compliant: {'✅' if validation['is_compliant'] else '❌'}")
    print(f"   Portfolio Risk: {validation['portfolio_risk_pct']:.2f}%")
    print(f"   Position Count: {validation['position_count']}")
    
    if validation['violations']:
        print(f"   Violations:")
        for violation in validation['violations']:
            print(f"     ❌ {violation}")
    else:
        print(f"   ✅ No violations detected")
    
    print(f"\n✅ Risk Management Test Completed!")

if __name__ == "__main__":
    test_risk_management()
