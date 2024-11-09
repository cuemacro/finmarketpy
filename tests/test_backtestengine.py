import pytest
import pandas as pd
import numpy as np
from finmarketpy.backtest.backtestengine import Backtest
from finmarketpy.backtest.backtestengine import BacktestRequest

@pytest.fixture
def sample_data():
    dates = pd.date_range(start='2020-01-01', periods=5, freq='D')
    asset_a_df = pd.DataFrame(data=np.random.randn(5, 1), index=dates, columns=['Asset'])
    signal_df = pd.DataFrame(data=np.random.choice([1, -1, 0], size=(5, 1)), index=dates, columns=['Signal'])
    further_df = [pd.DataFrame(data=np.random.randn(5, 1), index=dates, columns=['Further'])]
    further_df_labels = ['Label']
    return asset_a_df, signal_df, further_df, further_df_labels

def test_calculate_diagnostic_trading_PnL(sample_data):
    asset_a_df, signal_df, further_df, further_df_labels = sample_data
    backtest = Backtest()
    result = backtest.calculate_diagnostic_trading_PnL(asset_a_df, signal_df, further_df, further_df_labels)
    
    assert isinstance(result, pd.DataFrame)
    assert 'Asset' in result.columns
    assert 'Asset_entry' in result.columns
    assert 'Asset_asset_rets' in result.columns
    assert 'Asset_strat_rets' in result.columns
    assert 'Signal_final_signal' in result.columns
    assert 'Further_Label' in result.columns
    assert len(result) == 5
    

def test_calculate_trading_PnL(sample_data):
    asset_a_df, signal_df, further_df, further_df_labels = sample_data
    contract_value_df = pd.DataFrame(data=np.random.randn(5, 1), index=asset_a_df.index, columns=['ContractValue'])
    br = BacktestRequest()
    br.signal_delay = 1
    br.spot_tc_bp = 0.1
    br.spot_rc_bp = 0.1
    br.portfolio_vol_adjust = False
    br.signal_vol_adjust = False
    br.portfolio_combination = "mean"
    br.portfolio_combination_weights = None
    br.portfolio_vol_target = 0.1
    br.portfolio_vol_max_leverage = 2
    br.portfolio_vol_periods = 60
    br.portfolio_vol_obs_in_year = 252
    br.portfolio_vol_rebalance_freq = "BM"
    br.portfolio_vol_resample_freq = None
    br.portfolio_vol_resample_type = "mean"
    br.portfolio_vol_period_shift = 0
    br.max_net_exposure = None
    br.max_abs_exposure = None
    br.position_clip_period_shift = 0
    br.position_clip_rebalance_freq = None
    br.position_clip_resample_type = None
    br.cum_index = 'mult'
    br.ann_factor = 252
    br.resample_ann_factor = 252
    br.plot_start = None
    br.plot_finish = None
    br.start_date = asset_a_df.index[0]
    br.finish_date = asset_a_df.index[-1]
    br.write_csv = False
    br.calc_stats = False

    backtest = Backtest()
    backtest.calculate_trading_PnL(br, asset_a_df, signal_df, contract_value_df)

    assert isinstance(backtest.portfolio_pnl(), pd.DataFrame)
    assert 'Port' in backtest.portfolio_pnl().columns
    assert len(backtest.portfolio_pnl()) == 5
    
    
def test_filter_by_plot_start_finish_date(sample_data):
    asset_a_df, _, _, _ = sample_data
    br = BacktestRequest()
    br.start_date = asset_a_df.index[0]
    br.finish_date = asset_a_df.index[-1]
    
    backtest = Backtest()
    
    # Test case 1: No plot_start and plot_finish
    br.plot_start = None
    br.plot_finish = None
    filtered_df = backtest._filter_by_plot_start_finish_date(asset_a_df, br)
    assert filtered_df.equals(asset_a_df)
    
    # Test case 2: plot_start and plot_finish within the range
    br.plot_start = asset_a_df.index[1]
    br.plot_finish = asset_a_df.index[3]
    filtered_df = backtest._filter_by_plot_start_finish_date(asset_a_df, br)
    expected_df = asset_a_df.loc[br.plot_start:br.plot_finish]
    assert filtered_df.equals(expected_df)
    
    # Test case 3: plot_start before the range
    br.plot_start = asset_a_df.index[0] - pd.Timedelta(days=1)
    br.plot_finish = asset_a_df.index[3]
    filtered_df = backtest._filter_by_plot_start_finish_date(asset_a_df, br)
    expected_df = asset_a_df.loc[:br.plot_finish]
    assert filtered_df.equals(expected_df)
    
    # Test case 4: plot_finish after the range
    br.plot_start = asset_a_df.index[1]
    br.plot_finish = asset_a_df.index[-1] + pd.Timedelta(days=1)
    filtered_df = backtest._filter_by_plot_start_finish_date(asset_a_df, br)
    expected_df = asset_a_df.loc[br.plot_start:]
    assert filtered_df.equals(expected_df)
    
    # Test case 5: plot_start and plot_finish outside the range
    br.plot_start = asset_a_df.index[0] - pd.Timedelta(days=1)
    br.plot_finish = asset_a_df.index[-1] + pd.Timedelta(days=1)
    filtered_df = backtest._filter_by_plot_start_finish_date(asset_a_df, br)
    assert filtered_df.equals(asset_a_df)
def test_trade_no(sample_data):
    asset_a_df, signal_df, further_df, further_df_labels = sample_data
    backtest = Backtest()
    br = BacktestRequest()
    br.signal_delay = 1
    br.spot_tc_bp = 0.1
    br.spot_rc_bp = 0.1
    br.portfolio_vol_adjust = False
    br.signal_vol_adjust = False
    br.portfolio_combination = "mean"
    br.portfolio_combination_weights = None
    br.portfolio_vol_target = 0.1
    br.portfolio_vol_max_leverage = 2
    br.portfolio_vol_periods = 60
    br.portfolio_vol_obs_in_year = 252
    br.portfolio_vol_rebalance_freq = "BM"
    br.portfolio_vol_resample_freq = None
    br.portfolio_vol_resample_type = "mean"
    br.portfolio_vol_period_shift = 0
    br.max_net_exposure = None
    br.max_abs_exposure = None
    br.position_clip_period_shift = 0
    br.position_clip_rebalance_freq = None
    br.position_clip_resample_type = None
    br.cum_index = 'mult'
    br.ann_factor = 252
    br.resample_ann_factor = 252
    br.plot_start = None
    br.plot_finish = None
    br.start_date = asset_a_df.index[0]
    br.finish_date = asset_a_df.index[-1]
    br.write_csv = False
    br.calc_stats = False

    contract_value_df = pd.DataFrame(data=np.random.randn(5, 1), index=asset_a_df.index, columns=['ContractValue'])
    backtest.calculate_trading_PnL(br, asset_a_df, signal_df, contract_value_df)

    trade_no_df = backtest.trade_no()
    
    assert isinstance(trade_no_df, pd.DataFrame)
    assert 'Signal_final_signal' in trade_no_df.columns
    assert len(trade_no_df) == 1
    
    
    