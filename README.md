# Confessio
A search engine for confession hours by scraping parish websites.

This is the codebase of the [confessio.fr](https://confessio.fr) project,
and its [API](https://confessio.fr/api/docs).

Please open an issue if you find a bug, or if you have any question or suggestion.
You can also reach us through the [contact form](https://confessio.fr/contact).
Also, you might want to check our [status page](https://status.confessio.fr/).

---
## 📄 Licenses

- The **source code** is released under the **GNU GPL v3 License** ([see LICENSE](./LICENSE)).  
  → This is a strong copyleft license that allows reuse and modification, but requires that any derivative work also be released under the GPL and remain open-source.

- The **data provided through the API** is released under the **ODbL v1.0 license** ([see LICENSE_ODBL](./LICENSE_ODBL)).  
  → This license allows free use, sharing, and adaptation of the database, provided you attribute the source and share any improvements under the same terms.

Please make sure to **credit the source** when using the data, and if possible, add a “Report an error” link near each displayed piece of data, including Confessio brand name and its logo. We encourage you to **get in touch with the maintainer** to ensure proper usage and collaboration.

---
## 🧡 Sponsors
We'd like to thank our sponsor [Hozana](https://hozana.org/) for their support.

![Hozana](static/assets/img/logo/hozana-logo-small.png)

---

# Dev environment

### Environment variables
Copy the `.env.sample` file to `.env` and fill in the values.

### Python virtualenv with pyenv
We recommend using pyenv to manage python versions. Install it following the instructions 
[here](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation).
```shell
pyenv virtualenv 3.12.4 confessio
pyenv activate confessio
pip install -r requirements.txt
```

### Install GIS dependencies
For MacOS, follow instructions [here](https://mits003.github.io/studio_null/2021/07/install-gdal-on-macos/).

Also, you can configure GDAL_LIBRARY_PATH and GEOS_LIBRARY_PATH env var in .env.

## Postgresql database
Works currently on postgresql 15.4, and requires postgis and pgvector extensions.

### Create the database
```shell
psql postgres
CREATE DATABASE confessio;
```
Create user and grant privileges:
```shell
CREATE USER confessio
GRANT ALL PRIVILEGES ON DATABASE confessio TO confessio;
```

### Init database from scratch
```shell
CREATE EXTENSION postgis;
CREATE EXTENSION vector;
```

The migrations can not be applied from the beginning because it crashes at some point.
If you'd like to start from scratch, you can load the prod database dump in local (see below).

To detect new migrations:
```bash
$ python manage.py makemigrations
```

To apply existing migrations:
```shell
$ python manage.py migrate
```

Create the Superuser
```bash
$ python manage.py createsuperuser
```

### Load prod database dump in local

This will download and load the latest prod database dump in local. Your psql user must be superadmin.
```bash
# Remove and recreate confessio database
$ psql postgres -c "DROP DATABASE confessio;" && psql postgres -c "CREATE DATABASE confessio;"
# Download and load the latest prod database dump
$ python manage.py dbrestore --uncompress
```

## Start the app

```bash
$ python manage.py runserver
```

At this point, the app runs at `http://127.0.0.1:8000/`.

## Continuous Integration
To install required packages for tests and linter, run:
```
pip install -r ci_requirements.txt
```

### Testing
```shell
# without django loading
python -m unittest discover scraping
# OR with django loading
python manage.py test
```
### Linter
```shell
flake8
```

### Pre-commit hook
Consider adding a pre-commit hook (`vim .git/hooks/pre-commit`), but if you don't github actions will catch you.
```shell
echo "Running flake8..."
flake8 .
if [ $? -ne 0 ]; then
    echo "flake8 failed. Please fix the above issues before committing."
    exit 1
fi

echo "Running unit tests..."
python -m unittest discover scraping
if [ $? -ne 0 ]; then
    echo "Unit tests failed. Please fix the above issues before committing."
    exit 1
fi
```

## Translations
Inside `/home` directory:
```shell
django-admin makemessages -l fr
django-admin compilemessages
```

## Commands
You'll find all self implemented commands in `home/management/commands/`. 
For example, to crawl all websites:

```shell
python manage.py crawl_websites
```

## Profiling

We use [silk](https://github.com/jazzband/django-silk) as profiling tool.
```
DJANGO_SETTINGS_MODULE=core.profiling_settings python manage.py migrate
DJANGO_SETTINGS_MODULE=core.profiling_settings python manage.py collectstatic
DJANGO_SETTINGS_MODULE=core.profiling_settings python manage.py runserver
```
Then visit http://127.0.0.1:8000/silk.

---

# Prod environment

We use ansible to deploy to production. See [ansible README](./ansible/README.md) for instructions.


### Database backup on S3
On local machine you can check S3 backups like this:
```shell
# add credentials, you will be asked for AWS access and secret key
aws configure --profile confessio
# check daily backup
aws s3 ls confessio-dbbackup-daily --profile confessio
```

### Launch Django command in prod
```shell
./prod.sh manage crawl_websites
./prod.sh manage "crawl_websites -n 'Sainte Claire Entre Loire et Rhins'"
```
and if you want to launch the command in tmux (in session "manage_tmux"):
```shell
./prod.sh manage_tmux crawl_websites
./prod.sh manage_tmux "crawl_websites -n 'Sainte Claire Entre Loire et Rhins'"
```


## Check data integrity
```postgresql
-- Check that no home_url ends with slash
select name, home_url from home_website hp where home_url like '%/';
-- Check that no home_url ends with space
select name, home_url from home_website hp where home_url like '% ';
```
---

# Legacy documentation of  [Django Pixel Bootstrap 5](https://appseed.us/product/pixel-bootstrap/django/)

This part is to be removed once the project has been entirely freed from Django Pixel module.

Open-source **Django** project crafted on top of **[Pixel Bootstrap 5](https://appseed.us/product/pixel-bootstrap/django/)**, an open-source design from `Themesberg`.
The product is designed to deliver the best possible user experience with highly customizable feature-rich pages. 

- 👉 [Django Pixel Bootstrap 5](https://appseed.us/product/pixel-bootstrap/django/) - `Product page`
- 👉 [Django Pixel Bootstrap 5](https://django-pixel-lite.appseed-srv1.com/) - `LIVE Demo`

## Codebase structure

The project is coded using a simple and intuitive structure presented below:

```bash
< PROJECT ROOT >
   |
   |-- core/                            
   |    |-- settings.py                  # Project Configuration  
   |    |-- urls.py                      # Project Routing
   |
   |-- home/
   |    |-- views.py                     # APP Views 
   |    |-- urls.py                      # APP Routing
   |    |-- models.py                    # APP Models 
   |    |-- tests.py                     # Tests  
   |    |-- templates/                   # Theme Customisation 
   |         |-- pages                   # 
   |              |-- custom-index.html  # Custom Footer      
   |     
   |-- requirements.txt                  # Project Dependencies
   |
   |-- env.sample                        # ENV Configuration (default values)
   |-- manage.py                         # Start the app - Django default start script
   |
   |-- ************************************************************************
```

<br />

## How to Customize 

When a template file is loaded, `Django` scans all template directories starting from the ones defined by the user, and returns the first match or an error in case the template is not found. 
The theme used to style this starter provides the following files: 

```bash
# This exists in ENV: LIB/theme_pixel
< UI_LIBRARY_ROOT >                      
   |
   |-- templates/                     # Root Templates Folder 
   |    |          
   |    |-- accounts/       
   |    |    |-- sign-in.html         # Sign IN Page
   |    |    |-- sign-up.html         # Sign UP Page
   |    |
   |    |-- includes/       
   |    |    |-- footer.html          # Footer component
   |    |    |-- navigation.html      # Navigation Bar
   |    |    |-- scripts.html         # Scripts Component
   |    |
   |    |-- layouts/       
   |    |    |-- base.html            # Masterpage
   |    |
   |    |-- pages/       
   |         |-- index.html           # Dashboard Page
   |         |-- about.html           # About Page
   |         |-- *.html               # All other pages
   |    
   |-- ************************************************************************
```

When the project requires customization, we need to copy the original file that needs an update (from the virtual environment) and place it in the template folder using the same path. 

> For instance, if we want to **customize the index.html** these are the steps:

- ✅ `Step 1`: create the `templates` DIRECTORY inside the `home` app
- ✅ `Step 2`: configure the project to use this new template directory
  - `core/settings.py` TEMPLATES section
- ✅ `Step 3`: copy the `index.html` from the original location (inside your ENV) and save it to the `home/templates` DIR
  - Source PATH: `<YOUR_ENV>/LIB/theme_pixel/template/pages/index.html`
  - Destination PATH: `<PROJECT_ROOT>home/templates/pages/index.html`

> To speed up all these steps, the **codebase is already configured** (`Steps 1, and 2`) and a `custom index` can be found at this location:

`home/templates/pages/custom-index.html` 

By default, this file is unused because the `theme` expects `index.html` (without the `custom-` prefix). 

In order to use it, simply rename it to `index.html`. Like this, the default version shipped in the library is ignored by Django. 

In a similar way, all other files and components can be customized easily.

---
[Django Pixel Bootstrap 5](https://appseed.us/product/pixel-bootstrap/django/) - **Django** Starter provided by **[AppSeed](https://appseed.us/)**
