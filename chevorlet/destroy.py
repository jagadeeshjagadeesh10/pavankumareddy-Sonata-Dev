from flask import render_template, redirect, url_for, session, request
from car import car
from werkzeug.security import generate_password_hash, check_password_hash
from car.models.customer import Customer as User
from car.models.car import Car
from car.models.booking import Booking
from car.models.owner import Owner
from bson.objectid import ObjectId  # Import ObjectId for MongoDB _ids
from flask import flash


@car.route('/owner_register', methods=['GET', 'POST'])
def owner_register():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form['phone_number']
        
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        zipcode = request.form['zipcode']
        dob = request.form['dob']
        ssn = request.form['ssn']
        driving_license = request.form['driving_license']

        # Check if the username is unique
        if not Owner.exists_by_username(username):
            data = {
                "firstname": firstname,
                "lastname": lastname,
                "username": username,
                "email": email,
                "password": generate_password_hash(password),
                "phone_number": phone_number,
                "address": address,
                "city": city,
                "state": state,
                "zipcode": zipcode,
                "dob": dob,
                "ssn": ssn,
                "driving_license": driving_license,
                "status": "pending",
                "balance": 0  # Default balance
            }
            Owner.create(data)
            return redirect(url_for('owner_login'))
        else:
            return redirect(url_for('owner_register'))
    return render_template('owner/register.html')








from flask import flash

@car.route('/owner_login', methods=['GET', 'POST'])
def owner_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        owner = Owner.get_by_username(username)  # Assuming this fetches the owner by username

        if owner:
            if owner['status'] == 'pending':
                # Status is pending; flash a message and render the login page
                flash("Your account is pending approval. Please wait for admin approval.", "error")
                return redirect(url_for('owner_login'))

            if Owner.check_password(owner, password):  # Check password
                # Status is approved, allow login
                session['owner'] = owner['username']
                session['owner_id'] = str(owner['_id'])
                flash("Login successful!", "success")
                return redirect(url_for('owner_home'))

        # Invalid credentials
        flash("Invalid username or password.", "error")
        return redirect(url_for('owner_login'))

    return render_template('owner/login.html')


# Owner Home Route
@car.route('/owner_home', methods=['GET'])
def owner_home():
    if 'owner' not in session:
        return redirect(url_for('owner_login'))

    owner_id = session['owner_id']

    # Fetch owner details
    owner = Owner.get_by_id(ObjectId(owner_id))
    total_balance = owner.get('balance', 0)

    return render_template('owner/home.html', total_balance=total_balance)

# Owner Logout Route
@car.route('/owner_logout', methods=['GET'])
def owner_logout():
    session.pop('owner', None)
    return redirect(url_for('owner_login'))


# Route to Add a Car
@car.route('/owner_add_car', methods=['GET', 'POST'])
def owner_add_car():
    if 'owner' not in session:  # Check if the owner is logged in
        return redirect(url_for('owner_login'))
    
    owner_id = session['owner_id']  # Get the owner's ID from the session
    
    if request.method == 'POST':
        owner_email = session['owner']
        owner = Owner.get_by_email(owner_email)  # Fetch owner by email

        # Prepare car data from the form
        car_data = {
            "owner_id": ObjectId(owner_id),
            "make": request.form['make'],  # Car make (e.g., Toyota)
            "model": request.form['model'],  # Car model (e.g., Corolla)
            "type": request.form['type'],  # Car type (SUV, Sedan, etc.)
            "license_plate": request.form['license_plate'],  # License plate number
            "current_odometer": float(request.form['current_odometer']),  # Current odometer reading
            "rental_price_per_day": float(request.form['rental_price_per_day']),
            "availability_status": request.form['availability_status'],  # Availability status (Weekends, Weekdays, etc.)
            "insurance_available": request.form['insurance_available'] == 'true',
            "insurance_cost": float(request.form['insurance_cost']),
            "state": request.form['state'],  # New field for the car's state
            "status": "available"  # Default status for the car
        }

        Car.create(car_data)  # Create a new car entry
        flash("Car added successfully!")
        return redirect(url_for('owner_view_cars'))

    return render_template('owner/add_car.html')


# Route to View All Cars of the Owner
@car.route('/owner_view_cars', methods=['GET'])
def owner_view_cars():
    if 'owner' not in session:
        return redirect(url_for('owner_login'))
    
    owner_id = session['owner_id']
    
    owner = Owner.get_by_id(ObjectId(owner_id))  # Fetch owner by ObjectId
    cars = Car.get_by_owner_id(ObjectId(owner_id))  # Fetch cars linked to the owner using ObjectId

    return render_template('owner/view_cars.html', cars=cars)



# Route to Edit a Car
@car.route('/owner_edit_car/<car_id>', methods=['GET', 'POST'])
def owner_edit_car(car_id):
    if 'owner' not in session:
        return redirect(url_for('owner_login'))

    # Fetch car by ObjectId
    car = Car.get_by_id(ObjectId(car_id))

    if request.method == 'POST':
        # Update car details from form data
        car['make'] = request.form['make']
        car['model'] = request.form['model']
        car['type'] = request.form['type']
        car['license_plate'] = request.form['license_plate']
        car['current_odometer'] = float(request.form['current_odometer'])
        car['rental_price_per_day'] = float(request.form['rental_price_per_day'])
        car['insurance_available'] = request.form['insurance_available'] == 'true'
        car['insurance_cost'] = float(request.form['insurance_cost'])

        # Update the car in the database
        Car.update(ObjectId(car_id), car)
        flash("Car details updated successfully!")
        return redirect(url_for('owner_view_cars'))

    return render_template('owner/edit_car.html', car=car)


# Route to Delete a Car
@car.route('/owner_delete_car/<car_id>', methods=['POST'])
def owner_delete_car(car_id):
    if 'owner' not in session:
        return redirect(url_for('owner_login'))

    car = Car.get_by_id(ObjectId(car_id))  # Fetch car by ObjectId

    if car:
        Car.delete(ObjectId(car_id))  # Delete the car entry using ObjectId
        flash("Car deleted successfully!")

    return redirect(url_for('owner_view_cars'))

@car.route('/owner_view_bookings', methods=['GET'])
def owner_view_bookings():
    if 'owner' not in session:
        return redirect(url_for('owner_login'))

    # Debugging session owner_id
    owner_id = session.get('owner_id')
    print("Owner ID from session:", owner_id)

    if not owner_id:
        flash("Owner ID not found in session.", "error")
        return redirect(url_for('owner_login'))

    try:
        # Fetch cars owned by the owner
        cars = list(Car.get_by_owner_id(ObjectId(owner_id)))
        print("Cars fetched for owner:", cars)

        if not cars:
            flash("No cars found for this owner.", "info")
            return render_template('owner/view_bookings.html', bookings=[])

        # Create a dictionary of cars for quick lookup
        car_dict = {str(car['_id']): car for car in cars}
        print("Car Dictionary:", car_dict)

        # Get car IDs as ObjectIds
        car_ids = [car['_id'] for car in cars]
        print("Car IDs for owner:", car_ids)

        # Fetch all bookings for these cars
        bookings = list(Booking.collection.find({"car_id": {"$in": car_ids}}))
        print("Bookings fetched:", bookings)

        # Enrich bookings with car model and customer details
        enriched_bookings = []
        for booking in bookings:
            car_model = car_dict.get(str(booking['car_id']), {}).get('model', 'Unknown')
            customer = User.get_by_id(booking['customer_id'])
            customer_name = customer['username'] if customer else 'Unknown'
            booking['car_model'] = car_model
            booking['customer_name'] = customer_name
            enriched_bookings.append(booking)

        return render_template('owner/view_bookings.html', bookings=enriched_bookings)

    except Exception as e:
        print("Error occurred:", str(e))
        flash("An error occurred while fetching bookings.", "error")
        return redirect(url_for('owner_home'))




@car.route('/owner_manage_booking/<booking_id>', methods=['GET', 'POST'])
def owner_manage_booking(booking_id):
    if 'owner' not in session:
        return redirect(url_for('owner_login'))

    try:
        # Fetch the booking details
        booking = Booking.get_by_id(ObjectId(booking_id))
        if not booking:
            flash("Booking not found!", "error")
            return redirect(url_for('owner_view_bookings'))

        # Fetch the car details
        car = Car.get_by_id(booking['car_id'])
        if not car:
            flash("Car associated with this booking not found!", "error")
            return redirect(url_for('owner_view_bookings'))

        if request.method == 'POST':
            # Capture form data
            current_mileage = request.form.get('current_mileage')
            gas_level = request.form.get('gas_level')
            pickup_location = request.form.get('pickup_location')
            dropoff_location = request.form.get('dropoff_location')
            penalty = request.form.get('penalty', '0')
            action = request.form.get('action')

            if not current_mileage or not gas_level or not pickup_location or not dropoff_location:
                flash("Please provide all required fields.", "error")
                return redirect(url_for('owner_manage_booking', booking_id=booking_id))

            # Update booking with the provided data
            update_data = {
                "current_mileage": int(current_mileage),
                "gas_level": gas_level,
                "pickup_location": pickup_location,
                "dropoff_location": dropoff_location,
                "penalty": float(penalty) if penalty else 0.0,
            }

            # Handle Checkout (returning the car)
            if action == "checkout":
                update_data["status"] = "returned"
                Car.update(car['_id'], {"current_odometer": int(current_mileage)})

            Booking.update(ObjectId(booking_id), update_data)
            flash(f"Booking {action} successfully updated!", "success")
            return redirect(url_for('owner_view_bookings'))

        return render_template('owner/manage_booking.html', booking=booking, car=car)

    except Exception as e:
        print("Error:", str(e))
        flash("An error occurred while managing the booking.", "error")
        return redirect(url_for('owner_view_bookings'))
