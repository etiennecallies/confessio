# Confessio
A search engine for confession hours by scraping parish websites.

# Dev environment
### Local env with pyenv
```shell
pyenv virtualenv 3.11.4 confessio
pyenv activate confessio
pip install -r requirements.txt
```

### Install GIS dependencies
For MacOS, follow instructions [here](https://mits003.github.io/studio_null/2021/07/install-gdal-on-macos/)

Also, you can configure GDAL_LIBRARY_PATH and GEOS_LIBRARY_PATH env var in .env.

### Postgresql database
Works currently on postgresql 15.4, and requires postgis extension.

To apply existing migrations:
```shell
$ python manage.py migrate
```

To detect new migrations:
```bash
$ python manage.py makemigrations
```

### Create the Superuser

```bash
$ python manage.py createsuperuser
```

### Start the app

```bash
$ python manage.py runserver
```

At this point, the app runs at `http://127.0.0.1:8000/`.
## Testing
```shell
python -m unittest
OR
python manage.py test
```

## Translations
Inside `/home` directory:
```shell
django-admin makemessages -l fr
django-admin compilemessages
```

## Scraping

```shell
python manage.py scrape_parishes
```

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
./prod.sh manage crawl_parishes
```

## Check data integrity
```postgresql
-- Check that no home_url ends with slash
select name, home_url from home_parish hp where home_url like '%/';
-- Check that no home_url ends with space
select name, home_url from home_parish hp where home_url like '% ';
```
---

# Legacy documentation of  [Django Pixel Bootstrap 5](https://appseed.us/product/pixel-bootstrap/django/)

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
