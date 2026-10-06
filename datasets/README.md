# Datasets

This folder holds the **scripts and documentation** for each dataset. The data files themselves live in OneDrive,
not in git:

`~/Library/CloudStorage/OneDrive-Personal/Projects/The 4th Sheet/Data/<Domain>/`

| Domain | Data folder | Scripts here |
| --- | --- | --- |
| Health | `Data/Health/` | none (documentation in `Health/data/README.md`) |
| Legal | `Data/Legal/` | `Legal/scripts/` (build, import to PostgreSQL, reporting models) |
| Purchasing | `Data/Purchasing/` | `Purchasing/Scripts/` (generate, create schema, load to Azure SQL) |
| Retail | `Data/Retail/` | none yet |

Scripts read and write the OneDrive folder automatically, on the Mac or a Windows PC. Set `FOURTH_SHEET_DATA` to point at a different `Data` folder.
