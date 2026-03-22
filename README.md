# FRIDGEVENTORY

Open-source app that allows you to keep track of your pantry item. Check it out! 

## Overview


# Setup

1. Create venv
2. Install requirements by running `pip install -r requirements.txt`
3. Follow the env file example to create the variables to be used


## Functions
### User process

1. User creates a Household and starts storing items
2. User can invite a ner member by generating a 6-digit code

### Security on Authentication

This app uses JWT token, which has a limit on token storage that triggers a blocklist function to revoke access

## TO DO NEXT
1. Finish the Open API doc once routes and db are modified
2. Work on the frontend (Jinja + Tailwind)
3. Docker deployment for personal use
