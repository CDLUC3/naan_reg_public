# Changelog for CDLUC3/naan_reg_public

Provides a summary of changes to code and overrides. 

Changes to NAAN or Shoulder records generated from the upstream source of truth (i.e. CDLUC3/naan_reg_priv) are not 
documented here.

## 2024-07-08:

Changes:

- Move shadow NAAN records from code generated to magic files in preparation for updating NAAN registry.
- Make a local copy of the EZID shoulder file to avoid occasional network access issues.
- Update README

Upcoming:

- Move script management to python poetry
- Migrate magic files to private NAAN repository record updates
- Remove need for EZID shoulder list through a combination of NAAN registry and EZID config =uration updates

