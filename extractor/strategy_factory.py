from typing import List
from strategy.base_strategy import BaseStrategy
from strategy.strategy_shippingline.strategy_anl import ANLStrategy
from strategy.strategy_shippingline.strategy_bal import BALStrategy
from strategy.strategy_shippingline.strategy_cosco import COSCOStrategy
from strategy.strategy_shippingline.strategy_evergreen import EvergreenStrategy
from strategy.strategy_shippingline.strategy_hamburg_sud import HamburgSudStrategy
from strategy.strategy_shippingline.strategy_hapag_lloyd import HapagLloydStrategy
from strategy.strategy_shippingline.strategy_hmm import HMMStrategy
from strategy.strategy_shippingline.strategy_maersk import MAERSKStrategy
from strategy.strategy_shippingline.strategy_msc import MSCStrategy
from strategy.strategy_shippingline.strategy_nautical import NauticalStrategy
from strategy.strategy_shippingline.strategy_one import ONEStrategy
from strategy.strategy_shippingline.strategy_oocl import OOCLStrategy
from strategy.strategy_shippingline.strategy_pil import PILStrategy
from strategy.strategy_shippingline.strategy_quay import QUAYStrategy
from strategy.strategy_shippingline.strategy_swire import SWIREStrategy
from strategy.strategy_shippingline.strategy_ts_lines import TSLINEStrategy
from strategy.strategy_shippingline.strategy_yangming import YANGMINGStrategy
from strategy.strategy_shippingline.strategy_zim import ZIMStrategy
from strategy.strategy_generic import GenericStrategy

class StrategyFactory:
    _registry: List[BaseStrategy] = [
        ANLStrategy(),
        BALStrategy(),
        COSCOStrategy(),
        EvergreenStrategy(),
        HamburgSudStrategy(),
        HapagLloydStrategy(),
        HMMStrategy(),
        ONEStrategy(),
        OOCLStrategy(),
        MAERSKStrategy(),
        MSCStrategy(),
        NauticalStrategy(),
        PILStrategy(),
        QUAYStrategy(),
        SWIREStrategy(),
        TSLINEStrategy(),
        YANGMINGStrategy(),
        ZIMStrategy(),
    ]
    _fallback = GenericStrategy()

    @classmethod
    def match_first(cls, text: str) -> BaseStrategy:
        t = (text or "").upper()
        for strat in cls._registry:
            try:
                if strat.match(t):
                    return strat
            except Exception:
                continue
        return cls._fallback


def get_matching_strategy(text: str) -> BaseStrategy:
    return StrategyFactory.match_first(text)
