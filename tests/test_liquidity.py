import io
import pytest
from unittest.mock import MagicMock, patch
from package.core_layer_chain import ChainLink
import os
import json


@pytest.fixture
def mock_chain_link():
    with patch("package.core_layer_chain.Web3") as MockWeb3, \
         patch("os.getenv") as mock_getenv, \
         patch("builtins.open", new=mock_open_files) as mock_open_builtins:

        mock_getenv.side_effect = lambda x: {
            "RPC_ARBITRUM": "http://mock-rpc-arbitrum",
            "MAIN_ADR": "0xmain",
            "WORK_ADR": "0xwork",
            "WORK_KEY": "0xkey",
        }.get(x, "")
        
        # Mock contract calls and their return values
        mock_contract_token0 = MagicMock()
        mock_contract_token0.functions.decimals.return_value.call.return_value = 18
        mock_contract_token0.functions.name.return_value.call.return_value = "MockToken0"
        mock_contract_token0.functions.symbol.return_value.call.return_value = "MT0"

        mock_contract_token1 = MagicMock()
        mock_contract_token1.functions.decimals.return_value.call.return_value = 6
        mock_contract_token1.functions.name.return_value.call.return_value = "MockToken1"
        mock_contract_token1.functions.symbol.return_value.call.return_value = "MT1"

        mock_contract_factory = MagicMock()
        mock_contract_factory.functions.getPool.return_value.call.return_value = "0xmockpooladdress"

        mock_contract_pool = MagicMock()
        mock_contract_pool.functions.tickSpacing.return_value.call.return_value = 60
        mock_contract_pool.functions.token0.return_value.call.return_value = "0xmocktoken1address"
        mock_contract_pool.functions.token1.return_value.call.return_value = "0xmocktoken0address"
        mock_contract_pool.functions.slot0.return_value.call.return_value = (1000, 500)  # sqrtPriceX96, tick
        mock_contract_pool.functions.liquidity.return_value.call.return_value = 1234567890123456789
        mock_contract_pool.functions.feeGrowthGlobal0X128.return_value.call.return_value = 987654321098765432109876543210987654321
        mock_contract_pool.functions.feeGrowthGlobal1X128.return_value.call.return_value = 123456789012345678901234567890123456789

        mock_contract_manager = MagicMock()
        mock_contract_router = MagicMock()
        mock_contract_quoter = MagicMock()
        
        mock_connection = MagicMock()
        mock_connection.is_connected.return_value = True
        mock_connection.eth.chain_id = 42

        def contract_factory(*args, **kwargs):
            address = kwargs.get("address") if "address" in kwargs else (args[0] if args else None)
            if address == "0xmocktoken0address":
                return mock_contract_token0
            if address == "0xmocktoken1address":
                return mock_contract_token1
            if address == "0xmockfactoryaddress":
                return mock_contract_factory
            if address == "0xmockrouteraddress":
                return mock_contract_router
            if address == "0xmockquoteraddress":
                return mock_contract_quoter
            if address == "0xmockmanageraddress":
                return mock_contract_manager
            if address == "0xmockpooladdress":
                return mock_contract_pool
            return MagicMock()

        mock_connection.eth.contract.side_effect = contract_factory
        MockWeb3.return_value = mock_connection

        yield ChainLink("arbitrum", "weth", "usdc", "uniswap", "test")

def mock_open_files(filename, mode="r", **kwargs):
    if filename == "config/addresses/arbitrum.json":
        return io.StringIO(json.dumps({
            "weth": "0xmocktoken0address",
            "usdc": "0xmocktoken1address",
            "uniswap_factory": "0xmockfactoryaddress",
            "uniswap_router": "0xmockrouteraddress",
            "uniswap_quoter": "0xmockquoteraddress",
            "uniswap_manager": "0xmockmanageraddress",
        }))
    elif filename == "config/abi/token.json":
        return io.StringIO(json.dumps([]))
    elif filename == "config/abi/uniswap_factory.json":
        return io.StringIO(json.dumps([]))
    elif filename == "config/abi/uniswap_router.json":
        return io.StringIO(json.dumps([]))
    elif filename == "config/abi/uniswap_quoter.json":
        return io.StringIO(json.dumps([]))
    elif filename == "config/abi/uniswap_manager.json":
        return io.StringIO(json.dumps([]))
    elif filename == "config/abi/uniswap_pool.json":
        return io.StringIO(json.dumps([]))
    elif filename == "private/secrets.env":
        return io.StringIO("")
    raise FileNotFoundError(filename)


def test_get_liquidity_no_scanner(mock_chain_link):
    chain_link = mock_chain_link
    l_row, fee0, fee1 = chain_link.get_liquidity()

    assert l_row == 1234567890123456789
    assert fee0 == 123456789012345678901234567890123456789 / 2**128 / (10**6)  # feeGrowthGlobal1X128 / 10**decimals1 (reversed)
    assert fee1 == 987654321098765432109876543210987654321 / 2**128 / (10**18) # feeGrowthGlobal0X128 / 10**decimals0 (reversed)

    chain_link.pools[chain_link.L_fee]["reversed"] = False
    l_row, fee0, fee1 = chain_link.get_liquidity()
    assert fee0 == 987654321098765432109876543210987654321 / 2**128 / (10**18) # feeGrowthGlobal0X128 / 10**decimals0
    assert fee1 == 123456789012345678901234567890123456789 / 2**128 / (10**6)  # feeGrowthGlobal1X128 / 10**decimals1

def test_get_liquidity_with_scanner(mock_chain_link):
    chain_link = mock_chain_link
    
    # Mock the ticks function for the scanner
    def mock_ticks_call(tick):
        if tick == 540 + 60 or tick == 540 - 60: # up_direction and down_direction after alignment
            return (1000,)
        return (0,)

    def ticks_fn(tick):
        m = MagicMock()
        m.call.return_value = mock_ticks_call(tick)
        return m

    chain_link.pools[chain_link.L_fee]["contract"].functions.ticks.side_effect = ticks_fn

    # Mock current tick for the scanner to work
    chain_link.current_tick = 540
    chain_link.pools[chain_link.L_fee]["spacing"] = 60

    liq_up_10, liq_up_30, liq_down_10, liq_down_30 = chain_link.get_liquidity(scaner=True)

    # Assuming the mock_ticks_call returns 1000 for relevant ticks
    assert liq_up_10 == 1000  # Only one tick will return 1000 for 10 cycles
    assert liq_up_30 == 1000  # Only one tick will return 1000 for 30 cycles
    assert liq_down_10 == 1000 # Only one tick will return 1000 for 10 cycles
    assert liq_down_30 == 1000 # Only one tick will return 1000 for 30 cycles

    # Test reversed pool
    chain_link.pools[chain_link.L_fee]["reversed"] = True
    liq_up_10, liq_up_30, liq_down_10, liq_down_30 = chain_link.get_liquidity(scaner=True)

    assert liq_up_10 == 1000  # up_direction becomes -spacing, so 500 - 60 = 440 (which is mocked to return 1000)
    assert liq_up_30 == 1000
    assert liq_down_10 == 1000 # down_direction becomes spacing, so 500 + 60 = 560 (which is mocked to return 1000)
    assert liq_down_30 == 1000
