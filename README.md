# FRIDGEVENTORY

This open-source app that allows you to keep track of your pantry item, expiration date and stock levels. Built with Flask following RESTful principles, this app has session-based authentication and household-scoped data isolation. Frontend implementation in progress. Contributions are welcome.

# Tech Stack

### Backend

| Tool    | Function |
| -------- | ------- |
| Flask  | Web framework |
| Flask-RESTful | REST API structure |
| Flask-SQLAlchemy | ORM |
| SQLite | Database |
| Werkzeug | password hashing |
| Flask Sessions | Authentication with httpOnly cookies |
| Flasgger | Swagger/OpenAPI documentation |

### Frontend

| Tool    | Function |
| -------- | ------- |
| Jinja2  | Server-side templating |
| HTMX | Dynamic interactions |
| Tailwind CSS | Styling |


# Endpoints

![APIReference](/static/img/api.png)

### Authentication

* POST /users/
Registers a new user

* POST /users/login/
User login and sets session cookie

* POST /users/logout/
User logout and clears session

### Users

* GET /users/
Lists all users

* GET /users/<username>/
Get certain user profile

* PUT /users/<username>/
Updates profile or password

* DELETE /users/<username>/
Deletes account info

### Households

* GET /households/
List of house user belongs ("summer cottage", "main home" and so on)

* POST /households/
Creates a new "house"

* GET /households/<id>/
Get house details and generates "join" invite code

* PUT /households/<id>/
Renames a house (owner-limited only)

* DELETE /households/<id>/
Deletes house entirely (owner-limited only)

* GET /households/<id>/members/
Lists house members

* POST /join/
Join a "house" using an invite code.

### Pantry Items

* GET /households/<id>/items/
All items in a house

* POST /households/<id>/items/
Adds a new item to pantry

* GET /households/<id>/items/<name>/
Get single item

* PUT /households/<id>/items/<name>/
Updates item or quantity

* DELETE /households/<id>/items/<name>/
Removes item

* GET /households/<id>/items/search/?q=
Search items by name (case insensitive)

* GET /households/<id>/items/expires/
Items already past expiration date

* GET /households/<id>/items/refills/
Items near or below minimum refill

* GET /households/<id>/items/expiring/<date>/
All items expiring in specific date

### Categories

* GET /households/<id>/categories/
Lists all categories in a house

* POST /households/<id>/categories/
Creates a new category

* GET /households/<id>/categories/<id>/
Gets a single category

* DELETE /households/<id>/categories/<id>/
Deletes a category

* POST /households/<id>/items/<name>/categories/
Assigns a category to an item

* DELETE /households/<id>/items/<name>/categories/
Removes a category from an item


## Security

* Session stored in httpOnly cookies
* All routes are protected except for `POST /api/users/` and `POST /api/users/login/`
* Household scoping - users only see data of the "house" they belong to


## Setup

1. Create venv
2. Install requirements by running `pip install -r requirements.txt`
3. Follow the env file example to create the variables to be used


## Functions


- Multi-user "household" system with "join" code. 
- Track your house food items quantity, expiration date, storing location (like "fridge" or "freezer") and brand
- "Minimum stock" alert system
- "Categories": user defines how they organized their own items! (like "vegetables", "oils", "dried fruits").
- Case-insensitive search: "tomatoes", "tomato", "Tomato" -> all leads to the same item registered
- Swagger UI documentation at `/apidocs/`
- Mobile-accessible via PWA (in progress)



## TO CONTRIBUTE
1. Fork this repository
2. Create a feature branch
`git checkout -b feature/your-feature`
3. Commit your changes
`git commit -m "Add your feature"`
4. Push to your branch
`git push origin feature/your-feature`
5. Open a pull request
