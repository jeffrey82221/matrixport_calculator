import numpy as np


class BTCU:
    """BTCU 雙幣投資"""

    def __init__(self, duration, current_price, hook_price, buy_price, anual_earning_rate):
        """
        Args:
            - duration: 天數
            - current_price: 當天BTC價錢
            - hook_price: 掛鉤價
            - buy_price: 失敗時的 BTC買入價
            - earning_rate: 成功的年化報酬
        """
        self._current_price = float(current_price)
        self._duration = float(duration)
        self._hook_price = float(hook_price)
        self._buy_price = float(buy_price)
        assert self._buy_price < self._hook_price
        self._earning_rate = float(anual_earning_rate) / 360. * self._duration

    @property
    def get_max_annual_earning_rate(self):
        return self._earning_rate / self._duration * 360.

    def end_earning_rate(self, end_price):
        init_usd_amount = 1.
        if end_price <= self._hook_price:
            btc_amount = init_usd_amount / self._buy_price
            end_usd_amount = btc_amount * end_price
        else:
            end_usd_amount = init_usd_amount * (1. + self._earning_rate)

        return end_usd_amount - init_usd_amount


class BTCDown:
    """BTC智盈看跌"""

    def __init__(self, duration, current_price,
                 start_increase_price, end_increase_price,
                 low_anual_earning_rate, high_anual_earning_rate):
        self._duration = float(duration)
        self._current_price = float(current_price)
        self._start_increase_price = float(start_increase_price)
        self._end_increase_price = float(end_increase_price)
        self._low_earning_rate = float(low_anual_earning_rate) / 360. * self._duration
        self._high_earning_rate = float(high_anual_earning_rate) / 360. * self._duration

    def end_earning_rate(self, end_price):
        if end_price >= self._start_increase_price:
            return self._low_earning_rate
        elif end_price <= self._end_increase_price:
            return self._high_earning_rate
        else:
            lower_price_diff = end_price - self._end_increase_price
            higher_price_diff = self._start_increase_price - end_price
            total_price_diff = self._start_increase_price - self._end_increase_price
            l_w = lower_price_diff / total_price_diff
            h_w = higher_price_diff / total_price_diff
            earning_rate = self._high_earning_rate * h_w + self._low_earning_rate * l_w
            return earning_rate


class BTCUp:
    """BTC智盈看跌"""

    def __init__(self, duration, current_price,
                 start_increase_price, end_increase_price,
                 low_anual_earning_rate, high_anual_earning_rate):
        self._duration = float(duration)
        self._current_price = float(current_price)
        self._start_increase_price = float(start_increase_price)
        self._end_increase_price = float(end_increase_price)
        self._low_earning_rate = float(low_anual_earning_rate) / 360. * self._duration
        self._high_earning_rate = float(high_anual_earning_rate) / 360. * self._duration

    def end_earning_rate(self, end_price):
        if end_price <= self._start_increase_price:
            return self._low_earning_rate
        elif end_price >= self._end_increase_price:
            return self._high_earning_rate
        else:
            lower_price_diff = self._end_increase_price - end_price
            higher_price_diff = end_price - self._start_increase_price
            total_price_diff = self._end_increase_price - self._start_increase_price
            l_w = lower_price_diff / total_price_diff
            h_w = higher_price_diff / total_price_diff
            earning_rate = self._high_earning_rate * h_w + self._low_earning_rate * l_w
            return earning_rate


class BTCwithStop:
    """買入BTC"""

    def __init__(self, current_price, stop_price):
        self._initial_price = float(current_price)
        self._stop_price = float(stop_price)

    def end_earning_rate(self, end_price):
        if end_price > self._stop_price:
            return (end_price - self._initial_price) / self._initial_price
        elif end_price <= self._stop_price:
            return (self._stop_price - self._initial_price) / self._initial_price


class BTCGrid:
    """
    買入BTC網格

    假設一半的利潤來自網格交易
    一半的利潤來自BTC漲落

    並且在low_price會做停損

    NOTE: 若停損時間太快，網格利潤能持續獲得的時間就會減少
    : holding_ratio 用來代表持有的時間長短
    """

    def __init__(self, current_price, low_price, high_price, grid_anual_earning_rate, duration):
        self._initial_price = float(current_price)
        self._low_price = float(low_price)
        self._high_price = float(high_price)
        self._duration = float(duration)
        self._grid_earning_rate = float(grid_anual_earning_rate) / 360. * self._duration

    def end_earning_rate(self, end_price, non_stop=True, hold_rate=1.0, stop_mode='low'):
        if non_stop:
            grid_earning = self.end_grid_earning_rate(1.0)
            btc_earning = self.end_btc_earning_rate(end_price)
            return grid_earning + (btc_earning * 0.5)
        else:
            assert stop_mode == 'high' or stop_mode == 'low'
            assert hold_rate < 1.0
            grid_earning = self.end_grid_earning_rate(hold_rate)
            if stop_mode == 'high':
                btc_earning = self.end_btc_earning_rate(self._high_price)
            elif stop_mode == 'low':
                btc_earning = self.end_btc_earning_rate(self._low_price)
            return grid_earning + (btc_earning * 0.5)

    def end_grid_earning_rate(self, hold_rate):
        return self._grid_earning_rate * hold_rate

    def end_btc_earning_rate(self, end_price):
        if end_price > self._high_price:
            return (self._high_price - self._initial_price) / self._initial_price
        elif end_price < self._low_price:
            return (self._low_price - self._initial_price) / self._initial_price
        else:
            return (end_price - self._initial_price) / self._initial_price


if __name__ == '__main__':
    # BTCU 12 days + BTCDOWN 15 days
    # Tunable Parameters:
    # 1. invest rate of BTCU vs BTCDOWN:
    # 2. hook price & earning_rate list of BTCU
    # Scan over prices (0., 1000, 2000, ... 300000)
    current_price = 21433.64
    days = 15
    btc_down = BTCDown(days, current_price, 20000, 15000, 0.03, 0.164)
    btc_up = BTCUp(days, current_price, 22000, 32000, 0.03, 0.311)
    # btc_with_stop = BTCwithStop(current_price, 15000)
    btc_grid = BTCGrid(current_price, 20000, 22000, 1.1102, days)
    down_rate = 0.5
    up_rate = 1 - down_rate

    bot_rate = 0.03
    mode = 'normal'  # or bad
    zoom_in = True
    if zoom_in:
        price_range = np.arange(btc_grid._low_price, btc_grid._high_price, 100.)
    else:
        price_range = np.arange(15000., 30000., 500.)
    for price in price_range:
        btc_up_earning = btc_up.end_earning_rate(price)
        btc_down_earning = btc_down.end_earning_rate(price)
        if mode == 'normal':
            bot_earning = btc_grid.end_earning_rate(price, non_stop=True)
        elif mode == 'bad':
            bot_earning = btc_grid.end_earning_rate(price, non_stop=False, hold_rate=0.0, stop_mode='low')
        usd_earning = btc_up_earning * up_rate + btc_down_earning * down_rate
        total_earning = bot_earning * bot_rate + usd_earning * (1. - bot_rate)
        annual_earning = total_earning / days * 360.
        print(f'price: {price}, yer: {round(annual_earning*100,2)}%')
