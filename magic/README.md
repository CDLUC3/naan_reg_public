# NAAN Registry magic configurations

This folder contains individual NAAN and shoulder records in JSON that patch the 
official NAAN registry and shoulder records to provide a final source of truth
that aligns with how legacy-n2t handles resolution for a few edge cases.

In some cases, naan_reg_priv/main_naans should be updated to reflect these 
overrides, but not always. Hence, the folder name.

These records are upserted to the registry after loading the other sources.

## Naming Convention

Files are named as follows, but the name is consistent for convenience only. The content of the file 
determines the effect.

```
PREFIX + ["_" + SHOULDER] + ".json"
```

