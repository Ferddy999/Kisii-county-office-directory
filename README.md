# Kisii County Office Directory

A web system that lists the departments, directorates, offices, services and staff of the County Government of Kisii, so that county staff can find the right office or officer quickly.

Built with Django 5.2 and PostgreSQL. Pages use plain HTML, one stylesheet and a small JavaScript file.

## What it does

- Role-based access: **Administrators** add, edit and delete records and read the audit log. **Ordinary users** can only search and view.
- Sign-in with a password and a 6-digit one-time code sent by email or SMS, with a lockout after repeated wrong passwords.
- Directory search with filters (department, office, building, service) and Staff and Offices tabs, on desktop and on phones.
- Validation and duplicate prevention (unique emails, phone numbers, extensions, office names).
- Audit trail of every create, update and delete.
- Terms and Conditions, Privacy and Cookie Policy, and a cookie consent banner.
- Settings page for contact details and password, and a handover cleanup for removing test data.

## Folder guide

| Folder | Purpose |
| --- | --- |
| `config/` | Project settings and top-level URLs |
| `core/` | Sign-in, one-time codes, settings, legal pages, dashboard, directory search |
| `departments/` | Departments and directorates |
| `offices/` | Offices and services |
| `staff/` | Staff records |
| `audit/` | Audit log |
| `templates/` | HTML templates |
| `static/` | Stylesheet, JavaScript and images |

## Set up on your own computer

You need Python 3.12 or newer, PostgreSQL 16 or newer and Git. The commands below are for Windows PowerShell.

**1. Get the code**

```powershell
git clone https://github.com/Ferddy999/Kisii-county-office-directory.git
cd Kisii-county-office-directory
```

**2. Create a virtual environment and install the packages**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks the activation script, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` first.

**3. Create the database**

In pgAdmin (Query Tool on the `postgres` database), run these one at a time:

```sql
CREATE USER directory_app WITH PASSWORD 'choose-your-own-password' CREATEDB;
```

```sql
CREATE DATABASE kisii_directory OWNER directory_app;
```

`CREATEDB` lets the test suite create its temporary database.

**4. Configure the environment**

```powershell
Copy-Item .env.example .env
```

Open `.env` and set:

- `SECRET_KEY` to any long random string
- `DEBUG=True` for development
- `ALLOWED_HOSTS=localhost,127.0.0.1`
- `DB_PASSWORD` to the password you chose above
- leave `EMAIL_BACKEND` as the console backend for development

Never commit `.env`. It is ignored by Git.

**5. Prepare the database and starter data**

```powershell
python manage.py migrate
python manage.py createcachetable
python manage.py setup_roles
python manage.py seed_directory
python manage.py createsuperuser
```

`seed_directory` loads the county's departments and a small amount of sample data. Give your superuser an email address, because sign-in codes are sent to it.

**6. Run it**

```powershell
python manage.py runserver
```

Open http://127.0.0.1:8000/. In development, sign-in codes and reset emails are printed in the terminal where `runserver` is running.

To create more users, open http://127.0.0.1:8000/admin/ and add them. Give each an email address and put them in the **Administrator** or **Ordinary user** group.

## Run the tests

```powershell
python manage.py test
```

All tests must pass before you open a pull request.

## Team workflow

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: one branch per task, a pull request for every change, and a teammate reviews before it is merged into `main`.

## Team

| Name | GitHub | Responsibility |
| --- | --- | --- |
| | | |

## Copyright

(c) 2026 County Government of Kisii. All rights reserved. The county name and seal are used with the permission of the county ICT office.
