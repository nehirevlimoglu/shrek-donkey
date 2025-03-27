# Team Shrek & Donkey Large Group project

## Team members
The members of the team are:
- Junjie (JJ) Zhou
- Damla Sen
- Mert Ayranci
- Finn Corney
- Nehir Evlimoglu
- Rares Filimon
- Liam Ferran
- Trong Vu
- Tan Yukseloglu



## Installation instructions
To install the software and use it in your local development environment, you must first set up and activate a local development environment.  From the root of the project:

```
$ virtualenv venv
$ source venv/bin/activate
```

Install all required packages:

```
$ pip3 install -r requirements.txt
```

Create the migrations for database:
```
$ python3 manage.py makemigrations
```

Migrate the database:

```
$ python3 manage.py migrate
```

Seed the development database with:

```
$ python3 manage.py seed
```

Run all tests with:
```
$ python3 manage.py test
```

## Project structure
The project is called `task_manager`.  It currently consists of a single app `tasks`.

## Deployed version of the application
The deployed version of the application can be found at (https://junjiezhou1.pythonanywhere.com/log_in/).

## Installation instructions
To install the software and use it in your local development environment, you must first set up and activate a local development environment.  From the root of the project:
