import core.uniswap_fn as uni
from dotenv import load_dotenv
import os




load_dotenv("private/secrets.env")
main_address = os.getenv("MAIN_ADR")
print(main_address)


print(uni.test)