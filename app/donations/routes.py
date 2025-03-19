from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_required
from app.donations import bp
from app.donations.forms import DonationForm, ReviewForm
from app.models.donation import Donation, Review
from app import db, csrf
from datetime import datetime, timedelta

# ------------------ Create Donation ------------------
@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    print(f"Create donation accessed by: {current_user.username} (ID: {current_user.id}, Type: {current_user.user_type})")
    
    if current_user.user_type != 'donor':
        flash('Only donors can create donations.', 'error')
        return redirect(url_for('main.index'))
    
    form = DonationForm()

    if form.validate_on_submit():
        try:
            # Handle expiry time for food and medical supplies/medicines
            needs_expiry = (
                form.category.data == 'food' or 
                (form.category.data == 'medical' and 
                 form.medical_type.data in ['supplies', 'medicines'])
            )
            
            if needs_expiry:
                if not form.expiry_time.data:
                    flash('Expiry date and time is required for this type of donation.', 'error')
                    return render_template('donations/create.html', title='Create Donation', form=form, datetime=datetime)
                
                if form.expiry_time.data < datetime.now():
                    flash('Expiry date and time cannot be in the past.', 'error')
                    return render_template('donations/create.html', title='Create Donation', form=form, datetime=datetime)
            else:
                # For other categories, set a default expiry time far in the future
                form.expiry_time.data = datetime.now() + timedelta(days=365)  # One year from now

            # Prepare category-specific details
            details = {}
            if form.category.data == 'food':
                details['food_type'] = form.food_type.data
            elif form.category.data == 'pets':
                details['pet_type'] = form.pet_type.data
                details['pet_age'] = form.pet_age.data
            elif form.category.data == 'books':
                details['book_type'] = form.book_type.data
            elif form.category.data == 'medical':
                details['medical_type'] = form.medical_type.data
            
            if form.special_instructions.data:
                details['special_instructions'] = form.special_instructions.data
            
            # Create the donation object
            donation = Donation(
                user_id=current_user.id,
                title=form.title.data,
                description=form.description.data,
                category=form.category.data,
                quantity=form.quantity.data,
                condition=form.condition.data,
                contact_phone=form.contact_phone.data,
                expiry_time=form.expiry_time.data,
                pickup_location=form.pickup_location.data,
                latitude=form.latitude.data,
                longitude=form.longitude.data,
                details=details
            )
            
            db.session.add(donation)
            db.session.commit()
            
            flash('Your donation has been created!', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating donation: {str(e)}")  # For debugging
            flash('An error occurred while creating the donation. Please try again.', 'error')
            return render_template('donations/create.html', title='Create Donation', form=form, datetime=datetime)
    
    # If form validation failed, print the errors for debugging
    if form.errors:
        print("Form validation errors:", form.errors)
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'error')
    
    return render_template('donations/create.html', title='Create Donation', form=form, datetime=datetime)

# ------------------ View Donation ------------------
@bp.route('/view/<int:id>')
def view(id):
    donation = Donation.query.get_or_404(id)
    review_form = ReviewForm()
    reviews = Review.query.filter_by(donation_id=id).all()
    
    # Check for expired donations
    is_expired = donation.expiry_time and donation.expiry_time < datetime.now()
    
    return render_template('donations/view.html', 
                         title=donation.title, 
                         donation=donation,
                         is_expired=is_expired,
                         review_form=review_form,
                         reviews=reviews)

# ------------------ Reserve Donation (For Recipients) ------------------
@bp.route('/<int:id>/reserve', methods=['POST'])
@login_required
def reserve(id):
    try:
        donation = Donation.query.get_or_404(id)
        
        # Check if user can reserve this donation
        if not donation.can_be_reserved_by(current_user):
            if donation.is_expired():
                db.session.delete(donation)
                db.session.commit()
                return jsonify({'error': 'This donation has expired and was removed.'}), 400
            elif donation.status != 'available':
                return jsonify({'error': 'This donation is no longer available.'}), 400
            elif donation.user_id == current_user.id:
                return jsonify({'error': 'You cannot reserve your own donation.'}), 400
            else:
                return jsonify({'error': 'You are not authorized to reserve this donation.'}), 403
        
        # Store the original donor's ID
        original_donor_id = donation.user_id
        
        # Attempt to reserve the donation
        success, message = donation.reserve(current_user)
        
        if success:
            # Restore the original donor's ID since reserve() changes it
            donation.user_id = original_donor_id
            # Add recipient_id field
            donation.recipient_id = current_user.id
            db.session.commit()
            # Send notification to donor (you can implement this later)
            return jsonify({'message': message})
        else:
            db.session.rollback()
            return jsonify({'error': message}), 400
            
    except Exception as e:
        db.session.rollback()
        print(f"Error reserving donation: {str(e)}")  # For debugging
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

# ------------------ Mark Donation as Completed (By Donor) ------------------
@bp.route('/<int:id>/complete', methods=['POST'])
@login_required
def complete(id):
    try:
        print(f"Complete route called for donation ID: {id}")
        print(f"Request headers: {request.headers}")
        print(f"Request data: {request.get_data()}")
        
        donation = Donation.query.get_or_404(id)
        print(f"Donation found: {donation.title}, status: {donation.status}")
        
        # Attempt to complete the donation using the model method
        success, message = donation.complete(current_user)
        print(f"Complete result: success={success}, message={message}")
        
        if success:
            db.session.commit()
            print("Database committed successfully")
            return jsonify({'message': message})
        else:
            db.session.rollback()
            print(f"Database rolled back: {message}")
            return jsonify({'error': message}), 400
            
    except Exception as e:
        db.session.rollback()
        print(f"Error completing donation: {str(e)}")  # For debugging
        import traceback
        traceback.print_exc()  # Print full traceback for debugging
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

# ------------------ Delete Donation (By Donor) ------------------
@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    try:
        donation = Donation.query.get_or_404(id)
        
        # Check if user is authorized to delete
        if donation.user_id != current_user.id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'You are not authorized to delete this donation.'}), 403
            flash('You are not authorized to delete this donation.', 'danger')
            return redirect(url_for('donations.view', id=id))
        
        # Store donation info for flash message
        donation_title = donation.title
        
        # Delete the donation
        db.session.delete(donation)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'message': f'Donation "{donation_title}" has been deleted successfully.',
                'redirect_url': url_for('main.dashboard')
            })
        
        flash(f'Donation "{donation_title}" has been deleted successfully.', 'success')
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        print(f"Error deleting donation: {str(e)}")  # For debugging
        db.session.rollback()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'An error occurred while deleting the donation.'}), 500
            
        flash('An error occurred while deleting the donation.', 'danger')
        return redirect(url_for('main.dashboard'))

# ------------------ Edit Donation (By Donor) ------------------
@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    donation = Donation.query.get_or_404(id)
    if donation.user_id != current_user.id:
        flash('You can only edit your own donations.', 'danger')
        return redirect(url_for('donations.view', id=id))
    
    form = DonationForm()
    if form.validate_on_submit():
        try:
            # Update basic fields
            donation.title = form.title.data
            donation.description = form.description.data
            donation.category = form.category.data
            donation.quantity = form.quantity.data
            donation.condition = form.condition.data
            donation.contact_phone = form.contact_phone.data
            donation.pickup_location = form.pickup_location.data
            donation.latitude = form.latitude.data
            donation.longitude = form.longitude.data
            
            # Handle expiry time
            needs_expiry = (
                form.category.data == 'food' or 
                (form.category.data == 'medical' and 
                 form.medical_type.data in ['supplies', 'medicines'])
            )
            
            if needs_expiry:
                if not form.expiry_time.data:
                    flash('Expiry date and time is required for this type of donation.', 'error')
                    return render_template('donations/edit.html', title='Edit Donation', form=form, donation=donation, datetime=datetime)
                
                if form.expiry_time.data < datetime.now():
                    flash('Expiry date and time cannot be in the past.', 'error')
                    return render_template('donations/edit.html', title='Edit Donation', form=form, donation=donation, datetime=datetime)
                
                donation.expiry_time = form.expiry_time.data
            else:
                # For other categories, set a default expiry time far in the future
                donation.expiry_time = datetime.now() + timedelta(days=365)
            
            # Prepare category-specific details
            details = {}
            if form.category.data == 'food':
                details['food_type'] = form.food_type.data
            elif form.category.data == 'pets':
                details['pet_type'] = form.pet_type.data
                details['pet_age'] = form.pet_age.data
            elif form.category.data == 'books':
                details['book_type'] = form.book_type.data
            elif form.category.data == 'medical':
                details['medical_type'] = form.medical_type.data
            
            if form.special_instructions.data:
                details['special_instructions'] = form.special_instructions.data
            
            donation.details = details
            
            db.session.commit()
            flash('Your donation has been updated!', 'success')
            return redirect(url_for('donations.view', id=id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the donation.', 'danger')
            print(f"Error updating donation: {str(e)}")  # For debugging
            return render_template('donations/edit.html', title='Edit Donation', form=form, donation=donation, datetime=datetime)
            
    elif request.method == 'GET':
        # Populate basic fields
        form.title.data = donation.title
        form.description.data = donation.description
        form.category.data = donation.category
        form.quantity.data = donation.quantity
        form.condition.data = donation.condition
        form.contact_phone.data = donation.contact_phone
        form.pickup_location.data = donation.pickup_location
        form.latitude.data = donation.latitude
        form.longitude.data = donation.longitude
        
        # Format expiry_time to match the expected datetime-local format
        if donation.expiry_time:
            form.expiry_time.data = donation.expiry_time
        
        # Populate category-specific fields from details JSON
        if donation.details:
            if donation.category == 'food':
                form.food_type.data = donation.details.get('food_type')
            elif donation.category == 'pets':
                form.pet_type.data = donation.details.get('pet_type')
                form.pet_age.data = donation.details.get('pet_age')
            elif donation.category == 'books':
                form.book_type.data = donation.details.get('book_type')
            elif donation.category == 'medical':
                form.medical_type.data = donation.details.get('medical_type')
            
            if 'special_instructions' in donation.details:
                form.special_instructions.data = donation.details.get('special_instructions')

    return render_template('donations/edit.html', title='Edit Donation', form=form, donation=donation, datetime=datetime)

@bp.route('/list')
def list():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', None)
    query = Donation.query

    if category:
        query = query.filter_by(category=category)

    donations = query.order_by(Donation.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False)
    return render_template('donations/list.html', 
                         title='Donations', 
                         donations=donations)

@bp.route('/review/<int:id>', methods=['POST'])
@login_required
def review(id):
    donation = Donation.query.get_or_404(id)
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(
            user_id=current_user.id,
            donation_id=id,
            rating=form.rating.data,
            comment=form.comment.data
        )
        db.session.add(review)
        db.session.commit()
        flash('Your review has been posted!', 'success')
    return redirect(url_for('donations.view', id=id))

@bp.route('/api/donations')
def api_list():
    category = request.args.get('category', None)
    query = Donation.query

    if category:
        query = query.filter_by(category=category)

    donations = query.order_by(Donation.created_at.desc()).all()
    return jsonify([donation.to_dict() for donation in donations])

@bp.route('/api/donations/<int:id>')
def api_view(id):
    donation = Donation.query.get_or_404(id)
    return jsonify(donation.to_dict())
