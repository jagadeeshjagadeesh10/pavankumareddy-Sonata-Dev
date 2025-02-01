from flask import render_template, request, flash
from flask import redirect, url_for, session
from car import car
from car.models.admin import Admin
from car.models.owner import Owner
from car.models.customer import Customer
from car.models.car import Car
from car.models.booking import Booking
from car.models.payment import Payment

from bson import ObjectId
from werkzeug.security import generate_password_hash


@car.route('/is_logged_in', methods=['GET'])
def is_logged_in():
    if 'customer' in session:
        return {"logged_in": True}, 200
    return {"logged_in": False}, 200



@car.route('/')
def index():
    # Fetch all cars with status "available"
    cars = list(Car.find({"status": "available"}))
    
    # Return the index page with cars
    return render_template('index.html', cars=cars)


@car.route('/associate')
def associate():
    return render_template('associate.html')



@car.route('/admin', methods=['GET'])

def admin():
    return render_template('admin/admin.html')



@car.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    print('admin_register') 
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # get admin count 
        admin_count = Admin.collection.count_documents({})
        if admin_count >= 1:
            flash('Admin already exists')
            print('Admin already exists')
            return redirect(url_for('admin_login'))
        if not Admin.exists_by_username(username):
            data = {
                "username": username,
                "password": generate_password_hash(password),
                "balance": 0
            }
            Admin.create(data)
            return redirect(url_for('admin_login'))
        else:
            return redirect(url_for('admin_register'))
    return render_template('admin/register.html')



@car.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.get_by_username(username)
        if admin and Admin.check_password(admin, password):
            session['admin'] = admin['username']
            return redirect(url_for('admin_home'))
        else:
            return redirect(url_for('admin_login'))
    return render_template('admin/admin_login.html')

@car.route('/admin_home', methods=['GET'])
def admin_home():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # Fetch owners and calculate total balance
    owners = list(Owner.find_all())
    owners_count = len(owners)
    owners_balance = sum(owner.get('balance', 0) for owner in owners)

    # Fetch customers
    customers = list(Customer.find_all())
    customers_count = len(customers)

    # Fetch total bookings and cancellations
    total_bookings = Booking.collection.count_documents({})
    cancelled_bookings = Booking.collection.count_documents({"status": "cancelled"})

    # Fetch completed and pending transactions
    completed_payments = Payment.collection.aggregate([
        {"$match": {"status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    completed_total = next(completed_payments, {}).get('total', 0)

    pending_payments = Payment.collection.aggregate([
        {"$match": {"status": "pending"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    pending_total = next(pending_payments, {}).get('total', 0)

    return render_template(
        'admin/admin_home.html',
        owners=owners,
        customers=customers,
        owners_count=owners_count,
        owners_balance=owners_balance,
        customers_count=customers_count,
        total_bookings=total_bookings,
        cancelled_bookings=cancelled_bookings,
        completed_total=completed_total,
        pending_total=pending_total
    )


@car.route('/admin_logout', methods=['GET'])
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))





# Route to View All Cars of the Owner
@car.route('/admin_view_cars', methods=['GET'])
def admin_view_cars():
    if 'admin' not in session:
        return redirect(url_for('owner_login'))
    
    # Fetch all cars from the database
    cars = Car.find_all()

    # Convert cars to a list if it is not already
    cars = list(cars)

    # Loop through each car to fetch owner details
    for car in cars:
        owner = Owner.get_by_id(ObjectId(car['owner_id']))  # Fetch owner by ObjectId
        if owner:
            car['owner_name'] = owner.get('username', 'Unknown')  # Add owner name to car details
        else:
            car['owner_name'] = 'Unknown'  # Fallback if owner not found
    print(cars)
    return render_template('admin/cars.html', cars=cars)



@car.route('/admin_owners', methods=['GET'])
def admin_owners():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    owners = list(Owner.find_all())  # Assuming find_all fetches all owner records
    return render_template('admin/owners.html', owners=owners)



@car.route('/update_owner_status/<owner_id>', methods=['POST'])
def update_owner_status(owner_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    try:
        # Get the action (approve or disapprove) from the form
        action = request.form.get('action')
        if action == 'approve':
            new_status = 'approved'
        elif action == 'disapprove':
            new_status = 'disapproved'
        else:
            flash('Invalid action!', 'error')
            return redirect(url_for('admin_owners'))

        # Update the owner's status in the database
        Owner.update_status(ObjectId(owner_id), new_status)
        flash(f"Owner status updated to '{new_status}'!", 'success')
    except Exception as e:
        flash(f"An error occurred while updating owner status: {str(e)}", 'error')

    return redirect(url_for('admin_owners'))



@car.route('/approve_owner/<owner_id>', methods=['POST'])
def approve_owner(owner_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
 
    # Fetch the owner as a dictionary
    owner = Owner.find_by_id(owner_id)
    if owner and owner.get('status') == "pending":  # Use .get() for safe access
        owner['status'] = "approved"  # Update the status directly in the dictionary
        Owner.update(owner_id, owner)  # Assuming `Owner.update` updates the record in the database
 
    return redirect(url_for('admin_owners'))


@car.route('/admin_customers', methods=['GET'])
def admin_customers():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    customers = list(Customer.find_all())
    return render_template('admin/customers.html', customers=customers)


@car.route('/admin_payments', methods=['GET'])
def admin_payments():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    payments = list(Payment.find_all())
    return render_template('admin/payments.html', payments=payments)


@car.route('/admin_bookings', methods=['GET'])
def admin_bookings():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # Fetch all bookings
    bookings = list(Booking.collection.find({}))

    # Enrich bookings with car and customer details
    enriched_bookings = []
    for booking in bookings:
        car = Car.get_by_id(booking['car_id'])
        customer = Customer.get_by_id(booking['customer_id'])
        enriched_bookings.append({
            "car_model": car['model'] if car else "Unknown",
            "customer_name": customer['username'] if customer else "Unknown",
            "start_date": booking['start_date'],
            "end_date": booking['end_date'],
            "total_cost": booking['total_cost'],
            "status": booking.get('status', 'active')  # Default to active if no status exists
        })

    return render_template('admin/bookings.html', bookings=enriched_bookings)
        return redirect(url_for('admin_login'))

    # Fetch all bookings
    bookings = list(Booking.collection.find({}))

    # Enrich bookings with car and customer details
    enriched_bookings = []
    for booking in bookings:
        car = Car.get_by_id(booking['car_id'])
        customer = Customer.get_by_id(booking['customer_id'])
        enriched_bookings.append({
            "car_model": car['model'] if car else "Unknown",
            "customer_name": customer['username'] if customer else "Unknown",
            "start_date": booking['start_date'],
            "end_date": booking['end_date'],
            "total_cost": booking['total_cost'],
            "status": booking.get('status', 'active')  # Default to active if no status exists
        })

                return redirect(url_for('admin_login'))

    # Fetch all bookings
    bookings = list(Booking.collection.find({}))

    # Enrich bookings with car and customer details
    enriched_bookings = []
    for booking in bookings:
        car = Car.get_by_id(booking['car_id'])
        customer = Customer.get_by_id(booking['customer_id'])
        enriched_bookings.append({
            "car_model": car['model'] if car else "Unknown",
            "customer_name": customer['username'] if customer else "Unknown",
            "start_date": booking['start_date'],
            "end_date": booking['end_date'],
            "total_cost": booking['total_cost'],
            "status": booking.get('status', 'active')  # Default to active if no status exists
        })

                return redirect(url_for('admin_login'))

    # Fetch all bookings
    bookings = list(Booking.collection.find({}))

    # Enrich bookings with car and customer details
    enriched_bookings = []
    for booking in bookings:
        car = Car.get_by_id(booking['car_id'])
        customer = Customer.get_by_id(booking['customer_id'])
        enriched_bookings.append({
            "car_model": car['model'] if car else "Unknown",
            "customer_name": customer['username'] if customer else "Unknown",
            "start_date": booking['start_date'],
            "end_date": booking['end_date'],
            "total_cost": booking['total_cost'],
            "status": booking.get('status', 'active')  # Default to active if no status exists
        })


                return redirect(url_for('admin_login'))

    # Fetch all bookings
    bookings = list(Booking.collection.find({}))

    # Enrich bookings with car and customer details
    enriched_bookings = []
    for booking in bookings:
        car = Car.get_by_id(booking['car_id'])
        customer = Customer.get_by_id(booking['customer_id'])
        enriched_bookings.append({
            "car_model": car['model'] if car else "Unknown",
            "customer_name": customer['username'] if customer else "Unknown",
            "start_date": booking['start_date'],
            "end_date": booking['end_date'],
            "total_cost": booking['total_cost'],
            "status": booking.get('status', 'active')  # Default to active if no status exists
        })        return redirect(url_for('admin_login'))

    # Fetch all bookings
    bookings = list(Booking.collection.find({}))

    # Enrich bookings with car and customer details
    enriched_bookings = []
    for booking in bookings:
        car = Car.get_by_id(booking['car_id'])
        customer = Customer.get_by_id(booking['customer_id'])
        enriched_bookings.append({
            "car_model": car['model'] if car else "Unknown",
            "customer_name": customer['username'] if customer else "Unknown",
            "start_date": booking['start_date'],
            "end_date": booking['end_date'],
            "total_cost": booking['total_cost'],
            "status": booking.get('status', 'active')  # Default to active if no status exists
        })
                return redirect(url_for('admin_login'))

    # Fetch all bookings
    bookings = list(Booking.collection.find({}))

    # Enrich bookings with car and customer details
    enriched_bookings = []
    for booking in bookings:
        car = Car.get_by_id(booking['car_id'])
        customer = Customer.get_by_id(booking['customer_id'])
        enriched_bookings.append({
            "car_model": car['model'] if car else "Unknown",
            "customer_name": customer['username'] if customer else "Unknown",
            "start_date": booking['start_date'],
            "end_date": booking['end_date'],
            "total_cost": booking['total_cost'],
            "status": booking.get('status', 'active')  # Default to active if no status exists
        })
        