# Welcome to Confessio repository

## Local env with pyenv
```
pyenv virtualenv 3.9.11 confessio
pyenv activate confessio
pip install -r requirements.txt
```

### Install GIS dependencies
Follow instructions [here](https://mits003.github.io/studio_null/2021/07/install-gdal-on-macos/)

## Run unit tests
```shell
python -m unittest
```

## Translations
Inside `/home` directory:
```shell
django-admin makemessages -l fr
django-admin compilemessages
```

## Scraping

```shell
python manage.py scrap_parishes
```


TODO clean the following part
# [Django Pixel Bootstrap 5](https://appseed.us/product/pixel-bootstrap/django/)

Open-source **Django** project crafted on top of **[Pixel Bootstrap 5](https://appseed.us/product/pixel-bootstrap/django/)**, an open-source design from `Themesberg`.
The product is designed to deliver the best possible user experience with highly customizable feature-rich pages. 

- 👉 [Django Pixel Bootstrap 5](https://appseed.us/product/pixel-bootstrap/django/) - `Product page`
- 👉 [Django Pixel Bootstrap 5](https://django-pixel-lite.appseed-srv1.com/) - `LIVE Demo`
- 🛒 **[Django Pixel PRO](https://appseed.us/product/pixel-bootstrap-pro/django/)** - `Premium Version`

<br />

> Features: 

- ✅ `Up-to-date Dependencies`
- ✅ Theme: [Django Theme Pixel](https://github.com/app-generator/django-theme-pixel)
- ✅ **Authentication**: `Django.contrib.AUTH`, Registration
- 🚀 `Deployment` 
  - `CI/CD` flow via `Render`

<br />

![Pixel Bootstrap Lite - Full-Stack Starter generated by AppSeed.](https://user-images.githubusercontent.com/51070104/168753915-d61b2f97-57b2-4d14-a774-d217d120ff62.png)

<br />

## Manual Build 

> 👉 Download the code  

```bash
$ git clone https://github.com/app-generator/django-pixel.git
$ cd django-pixel
```

<br />

> 👉 Install modules via `VENV`  

```bash
$ virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt
```

<br />

> 👉 Set Up Database

```bash
$ python manage.py makemigrations
$ python manage.py migrate
```

<br />

> 👉 Create the Superuser

```bash
$ python manage.py createsuperuser
```

<br />

> 👉 Start the app

```bash
$ python manage.py runserver
```

At this point, the app runs at `http://127.0.0.1:8000/`. 

<br />

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

<br />

## Deploy on [Render](https://render.com/)

- Create a Blueprint instance
  - Go to https://dashboard.render.com/blueprints this link.
- Click `New Blueprint Instance` button.
- Connect your `repo` which you want to deploy.
- Fill the `Service Group Name` and click on `Update Existing Resources` button.
- After that your deployment will start automatically.

At this point, the product should be LIVE.

<br />

## [PRO Version](https://appseed.us/product/pixel-bootstrap-pro/django)   

Seed project powered by **Django** Framework on top of **Pixel PRO** design. `Pixel` is a premium [Bootstrap 5](https://www.admin-dashboards.com/bootstrap-5-templates/) UI Kit featuring over 200 fully coded UI elements and example pages that will help you prototype and build a website for your next project.

![Pixel Bootstrap PRO - Full-Stack Starter generated by AppSeed](https://user-images.githubusercontent.com/51070104/168760719-f0e45406-2b2a-43e0-badf-fa953edb62b8.png)

<br />

---
[Django Pixel Bootstrap 5](https://appseed.us/product/pixel-bootstrap/django/) - **Django** Starter provided by **[AppSeed](https://appseed.us/)**
