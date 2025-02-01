from flask import render_template, redirect, url_for, session, request
from car import car
from werkzeug.security import generate_password_hash, check_password_hash
from car.models.customer import Customer as User
from car.models.car import Car
from car.models.booking import Booking
from car.models.owner import Owner
from car.models.admin import Admin

from bson import ObjectId
from car.models.payment import Payment
import datetime

from flask import flash



@car.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    print("confirm_booking")
    print(request.form)

    # Retrieve data from the form
    car_id = request.form.get('car_id')
    start_date_raw = request.form.get('start_date')
    end_date_raw = request.form.get('end_date')
    total_cost_from_ui = request.form.get('total_cost', 0)
    payment_method = request.form.get('payment_method')
    card_holder_name = request.form.get('card_holder_name')
    card_number = request.form.get('card_number')
    expiration_date = request.form.get('expiration_date')
    cvv = request.form.get('cvv')
    zipcode = request.form.get('zipcode')

    # Field validation with explicit messages
    if not car_id:
        flash('Car ID is missing!', 'error')
        return redirect(url_for('customer_view_cars'))
    if not start_date_raw or not end_date_raw:
        flash('Start and End dates are required!', 'error')
        return redirect(url_for('customer_view_cars'))
    if not total_cost_from_ui:
        flash('Total cost is required!', 'error')
        return redirect(url_for('customer_view_cars'))
    if not payment_method:
        flash('Payment method is required!', 'error')
        return redirect(url_for('customer_view_cars'))
    if not all([card_holder_name, card_number, expiration_date, cvv, zipcode]):
        flash('Payment details are incomplete!', 'error')
        return redirect(url_for('customer_view_cars'))

    # Convert start and end dates to datetime
    try:
        start_date = datetime.datetime.strptime(start_date_raw.split()[0], "%Y-%m-%d")

        end_date = datetime.datetime.strptime(end_date_raw.split()[0], "%Y-%m-%d")
    except ValueError:
        flash('Invalid date format. Please ensure the dates are correct.', 'error')
        return redirect(url_for('customer_view_cars'))

    # Convert total cost to float
    try:
        total_cost = float(total_cost_from_ui)
        if total_cost <= 0:
            raise ValueError("Total cost must be greater than 0")
    except ValueError as e:
        flash(f"Invalid total cost: {str(e)}", 'error')
        return redirect(url_for('customer_view_cars'))

    # Retrieve the car details from the database
    car = Car.get_by_id(ObjectId(car_id))
    if not car:
        flash('The selected car could not be found. Please try again.', 'error')
        return redirect(url_for('customer_view_cars'))

    # Calculate admin commission and owner earnings
    admin_commission = total_cost * 0.05
    owner_earnings = total_cost - admin_commission

    # Prepare the booking data
    booking_data = {
        "car_id": ObjectId(car_id),
        "start_date": start_date,
        "end_date": end_date,
        "total_cost": total_cost,
        "payment_method": payment_method,
        "customer_id": ObjectId(session['customer_id']),
        "card_holder_name": card_holder_name,
        "card_number": card_number,
        "expiration_date": expiration_date,
        "cvv": cvv,
        "zipcode": zipcode,
        "status": "confirmed"
    }

    # Create the booking record
    try:
        booking_result = Booking.create(booking_data)
        booking_id = booking_result.inserted_id
    except Exception as e:
        flash(f"Error creating booking: {str(e)}", 'error')
        return redirect(url_for('customer_view_cars'))

    # Prepare payment data
    payment_data = {
        "booking_id": booking_id,
        "amount": total_cost,
        "payment_date": datetime.datetime.now(),
        "payment_method": payment_method,
        "customer_id": ObjectId(session['customer_id']),
        "status": "completed"
    }

    # Create the payment record
    try:
        Payment.create(payment_data)
    except Exception as e:
        flash(f"Error processing payment: {str(e)}", 'error')
        return redirect(url_for('customer_view_cars'))

    # Update admin and owner balances
    try:
        admin = Admin.get_admin()
        owner = Owner.get_by_id(car['owner_id'])

        if admin:
            admin_balance = admin.get('balance', 0) + admin_commission
            Admin.update_balance(admin['_id'], admin_commission)

        if owner:
            owner_balance = owner.get('balance', 0) + owner_earnings
            Owner.update_balance(owner['_id'], owner_earnings)

    except Exception as e:
        flash(f"Error updating balances: {str(e)}", 'error')
        return redirect(url_for('customer_view_cars'))

    flash('Booking confirmed successfully!', 'success')
    return redirect(url_for('customer_bookings'))



@car.route('/process_booking', methods=['GET'])
def process_booking():
    car_id = request.args.get('car_id')
    date_range = request.args.get('date_range')

    if not car_id or not date_range:
        flash('Missing required parameters!', 'error')
        return redirect(url_for('customer_view_cars'))

    try:
        start_date, end_date = date_range.split(' to ')
        start_date = datetime.datetime.strptime(start_date.strip(), "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date.strip(), "%Y-%m-%d")
    except ValueError:
        flash('Invalid date range!', 'error')
        return redirect(url_for('customer_view_cars'))

    car = Car.get_by_id(ObjectId(car_id))
    if not car:
        flash('Car not found!', 'error')
        return redirect(url_for('customer_view_cars'))