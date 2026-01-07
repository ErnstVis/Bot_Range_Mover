import subprocess
import json

ADDRESS = "0x63e207c8adbd8c33fd74bade16184f93cadebdb875646bddd2f482bcd72e188f"

proc = subprocess.run(
    ["node", "sui-js/index.js", ADDRESS],
    capture_output=True,
    text=True,
    check=True,
)

data = json.loads(proc.stdout)

print("SUI raw:", data["sui"]["total"])
for token in data["tokens"]:
    if "IKA" in token["coinType"]:
        print("IKA raw:", token["totalBalance"])
