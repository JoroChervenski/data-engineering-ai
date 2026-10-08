# Standard snapshot

A pinned copy of `standard.json` and the two note templates from the Project Standard in the vault's
`Knowledge/` folder, so the tests run where no vault is mounted. It is a test double, not the standard.

`tests/test_vault_sync.py` compares it with the real standard when `KNOWLEDGE_DIR` points at the
vault's Knowledge folder, and fails if they differ. Refresh it by copying the three files over.
