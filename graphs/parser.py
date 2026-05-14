import pandas as pd
import json

df = pd.read_excel("stations.xlsx")

def extract_power(about):
    try:
        data = json.loads(about)
        charges = data.get("Charges", [])
        if charges:
            # Take the max power across all connectors
            return max(c.get("power", 0) for c in charges)
    except:
        pass
    return 10  # or a default like 7.2

df["power_kw"] = df["about"].apply(extract_power)

print(df[["name", "power_kw"]].head(20))
df.to_excel("stations_enriched.xlsx", index=False)