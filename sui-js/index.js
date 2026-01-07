import { SuiClient, getFullnodeUrl } from '@mysten/sui/client';

async function main() {
  const address = process.argv[2];
  if (!address) {
    console.error("Usage: node index.js <SUI_ADDRESS>");
    process.exit(1);
  }

  const client = new SuiClient({
    url: getFullnodeUrl('mainnet'),
  });

  // --- Native SUI ---
  const suiBalance = await client.getBalance({
    owner: address,
  });

  // --- All token balances ---
  const allBalances = await client.getAllBalances({
    owner: address,
  });

  const result = {
    address,
    sui: {
      total: suiBalance.totalBalance,
      decimals: 9,
    },
    tokens: allBalances,
  };

  console.log(JSON.stringify(result, null, 2));
}

main().catch(err => {
  console.error("Error:", err);
  process.exit(1);
});
