from package import ChainLink2
import time
import argparse
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="eth_utils")


chain = ChainLink2('polygon', 'uni3')

# TOKENS = {
#     "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
#     "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
#     "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
#     "FRAX": "0x45c32fA6DF82ead1e2EF74d17b76547EDdFaFF89",
#     "MAI": "0xa3Fa99A148fA48D14Ed51d610c367C61876997F1",
#     "CRV": "0x172370d5Cd63279eFa6d502DAB29171933a610AF",
#     "PAXG": "0x553d3D295e0f695B9228246232eDF400ed3560B5",
#     "GMT": "0x714DB550b574b3E927af3D93E26127D15721D4C2",
#     "UNI": "0xb33EaAd8d922B1083446DC23f610c2567fB5180f",    
# }



# build_pool_index()

# chain.get_current_tick(fee=500)
# print()
# print(chain.get_swap_ammount_quoter(1, 0, 'I', fee=500))
# print(chain.get_swap_ammount_quoter(1, 1, 'I', fee=500))
# print(chain.get_swap_ammount_quoter(0.5, 0, 'Q', fee=500))
# print(chain.get_swap_ammount_quoter(0.5, 1, 'Q', fee=500))