import json
from .config import ScreenerConfig
from .providers import NullProvider
from .screener import WalletScreener


def main() -> None:
    provider = NullProvider()
    screener = WalletScreener(provider, ScreenerConfig())
    addresses = provider.discover_wallets()
    results = screener.screen_many(addresses)
    print(json.dumps([screener.to_dict(r) for r in results], indent=2))


if __name__ == "__main__":
    main()
