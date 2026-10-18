[README.md](https://github.com/user-attachments/files/33634730/README.md)
# Hospital Management System database

`schema.sql` is the canonical fresh-install schema for MySQL 8+. It creates the 13 target application tables and does not drop existing objects. Do not run it against the current database; the migration has already been applied.

## Migration record

- Source database: `hospital_management` (MySQL 8.0.46).
- Backup made before migration: `backend/backups/hospital_management_pre_fastapi_20261011_142104.sql`.
- Staging migration: `python migrate.py stage`.
- The stage runner checks the six singular legacy copies are empty, checks there are no unexpired old sessions, copies compatible data, hashes legacy passwords, and validates counts and relationships. It leaves the original tables in place.
- After reviewing the stage report, the owner approved cleanup. Promotion was run with `python promote_migration.py --confirm-drop-legacy`.
- Promotion verified exactly the 13 canonical tables remain.

## Data mapping

IDs were preserved for all populated records. Account names are retained in `users.display_name`; linked doctor and patient names are split into profile names. Department locations are appended to descriptions, medicine descriptions are retained, old appointment date/time values are combined, and operation notes are retained as report summaries. The four patient-to-doctor assignments are retained in `patients.primary_doctor_id`. Legacy fields with no source remain nullable or defaulted (for example blood group, emergency contacts, doctor degree/experience, manufacturer/category, and report files). The seven medicines have descriptions; the old schema had no manufacturer or category column. The singular duplicate tables and the old session table were empty of live records; all five old sessions had expired and were not carried forward.

## Fresh install

Create an empty database and run:

```powershell
mysql -u <db-user> -p hospital_management < backend/sql/schema.sql
```

Set `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `FRONTEND_ORIGINS`, and `COOKIE_SECURE` in `backend/.env`. Keep this file and backups private. `COOKIE_SECURE=true` is required behind HTTPS in production; local HTTP development defaults to false.

## Backup and rollback

The original backup contains the pre-migration tables and must be treated as sensitive because the old database stored password values without a recognized password-hash format. It is excluded from Git. Uploaded documents live under `backend/storage/` by default and need their own file-system backup alongside MySQL backups.

For a pre-promotion rollback, the old source tables were untouched; remove only the `stage_*` tables after verifying they contain no records you need. For rollback after promotion, first take a fresh backup of the current database, stop the API, then restore the verified original dump into `hospital_management`:

```powershell
mysqldump -u <db-user> -p --single-transaction hospital_management > backend/backups/hospital_management_before_restore.sql
mysql -u <db-user> -p hospital_management < backend/backups/hospital_management_pre_fastapi_20261011_142104.sql
```

The restore replaces tables named in that dump and loses any data written since migration. Review the current backup and restore output before restarting the application.
