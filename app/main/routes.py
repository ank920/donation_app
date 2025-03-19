from flask import render_template, redirect, url_for, jsonify, request, flash
from flask_login import current_user, login_required
from app.main import bp
from app.models.donation import Donation
from app.models.user import User
from app import db
from sqlalchemy import or_, func, and_
from datetime import datetime

@bp.route('/')
def root():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return redirect(url_for('main.landing'))

@bp.route('/index')
@login_required
def index():
    # Get current time for expiry check
    current_time = datetime.utcnow()
    print("\n=== Index Page Access ===")
    
    # Get category counts for available and non-expired donations only
    category_counts = {}
    categories = ['food', 'clothes', 'pets', 'books', 'toys', 'medical']
    
    for category in categories:
        count = Donation.query.filter(
            Donation.category == category,
            Donation.status == 'available',
            Donation.expiry_time > current_time
        ).count()
        category_counts[category] = count
        print(f"Category {category}: {count} available donations")

    # Get total counts for statistics
    total_donations = Donation.query.count()
    total_available = Donation.query.filter(
        Donation.status == 'available',
        Donation.expiry_time > current_time
    ).count()
    total_completed = Donation.query.filter_by(status='completed').count()

    # Get recent available donations
    recent_donations = Donation.query.filter(
        Donation.status == 'available',
        Donation.expiry_time > current_time
    ).order_by(
        Donation.created_at.desc()
    ).all()  # Remove limit to show all available donations

    print(f"Total donations in system: {total_donations}")
    print(f"Available non-expired donations: {total_available}")
    print(f"Completed donations: {total_completed}")
    print(f"Recent available donations: {len(recent_donations)}")
    print("=== End Index ===\n")

    return render_template('main/index.html',
                         title='Home',
                         donations=recent_donations,
                         category_counts=category_counts,
                         total_donations=total_donations,
                         total_available=total_available,
                         total_completed=total_completed)

@bp.route('/landing')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_template('main/landing.html', title='Welcome')

@bp.route('/dashboard')
@login_required
def dashboard():
    print(f"\n=== Dashboard Access ===")
    print(f"User: {current_user.username} (ID: {current_user.id}, Type: {current_user.user_type})")
    current_time = datetime.utcnow()
    
    # Query donations based on user type
    if current_user.user_type == 'donor':
        print("\nQuerying as donor...")
        # For donors, show all their created donations regardless of status
        base_query = Donation.query.filter_by(user_id=current_user.id)
        
        # Get all donations
        donations = base_query.order_by(Donation.created_at.desc()).all()
        
        # Get counts for different statuses
        available_count = base_query.filter(
            Donation.status == 'available',
            Donation.expiry_time > current_time
        ).count()
        
        reserved_count = base_query.filter_by(status='reserved').count()
        completed_count = base_query.filter_by(status='completed').count()
        expired_count = base_query.filter(Donation.expiry_time <= current_time).count()
        
        # Get pending reservations that need confirmation
        pending_reservations = [d for d in donations if d.status == 'reserved' and not d.completed_at]
        
        print(f"Total donations created by donor: {len(donations)}")
        print("Donations breakdown:")
        print(f"- Available (non-expired): {available_count}")
        print(f"- Reserved: {reserved_count}")
        print(f"- Completed: {completed_count}")
        print(f"- Expired: {expired_count}")
        print(f"- Pending confirmations: {len(pending_reservations)}")
        
    else:  # recipient
        print("\nQuerying as recipient...")
        # For recipients, show available donations and their reserved/completed ones
        available_donations = Donation.query.filter(
            Donation.status == 'available',
            Donation.expiry_time > current_time
        ).order_by(Donation.created_at.desc()).all()
        
        my_donations = Donation.query.filter(
            Donation.recipient_id == current_user.id,
            Donation.status.in_(['reserved', 'completed'])
        ).order_by(Donation.created_at.desc()).all()
        
        # Combine both lists
        donations = available_donations + my_donations
        pending_reservations = []
        
        print(f"Available donations: {len(available_donations)}")
        print(f"My reserved/completed donations: {len(my_donations)}")
        print(f"Total donations shown: {len(donations)}")
    
    print("\nDetailed donation list:")
    for donation in donations:
        print(f"- ID: {donation.id}, Title: {donation.title}")
        print(f"  Status: {donation.status}, Expiry: {donation.expiry_time}")
        print(f"  Donor: {donation.donor.username}, Recipient: {donation.recipient.username if donation.recipient else 'None'}")
    
    # Get statistics
    stats = {
        'total': len(donations),
        'available': len([d for d in donations if d.status == 'available' and d.expiry_time > current_time]),
        'reserved': len([d for d in donations if d.status == 'reserved']),
        'completed': len([d for d in donations if d.status == 'completed'])
    }
    
    print(f"\nFinal stats: {stats}")
    print("=== End Dashboard ===\n")
    
    # Prepare donations data for JSON
    donations_data = [d.to_dict() for d in donations]
    
    return render_template('main/dashboard.html',
                         title='Dashboard',
                         donations=donations,
                         donations_json=donations_data,
                         stats=stats,
                         pending_reservations=pending_reservations)

@bp.route('/map')
def map():
    return render_template('main/map.html', title='Donation Map')

@bp.route('/api/donations')
def get_donations():
    # Return available donations as JSON; ensure your Donation model has a to_dict() method.
    donations = Donation.query.filter_by(status='available').all()
    return jsonify([donation.to_dict() for donation in donations])

@bp.route('/api/search')
def search_donations():
    search_term = request.args.get('q', '').lower().strip()
    category = request.args.get('category', '').lower().strip()
    current_time = datetime.utcnow()
    
    print(f"\n=== Search Request ===")
    print(f"Search term: '{search_term}'")
    print(f"Category filter: '{category}'")
    
    # Base query for available and non-expired donations
    base_query = Donation.query.filter(
        Donation.status == 'available',
        Donation.expiry_time > current_time
    )
    
    # Apply category filter if specified
    if category and category != 'all':
        base_query = base_query.filter(Donation.category == category)
    
    # Get all donations that match the base criteria
    donations = base_query.all()
    results = []
    
    for donation in donations:
        donation_dict = donation.to_dict()
        matches = []  # Use list instead of set
        related_matches = []  # Use list instead of set
        
        if not search_term:
            # If no search term, include all donations with empty matches
            donation_dict['matches'] = matches
            donation_dict['related_matches'] = related_matches
            results.append(donation_dict)
            continue
            
        # Helper function to check and record matches
        def check_field(field_name, field_value, search_words):
            if not field_value:
                return False
            
            field_value = str(field_value).lower()
            exact_match = any(word in field_value for word in search_words)
            
            if exact_match:
                matches.append(field_name)  # Add to list instead of set
            
            # Check for related terms
            related_terms = {
                'food': ['meal', 'grocery', 'fruit', 'vegetable', 'snack', 'drink'],
                'clothes': ['clothing', 'wear', 'apparel', 'dress', 'shirt', 'pants'],
                'medical': ['medicine', 'health', 'healthcare', 'hospital', 'pharmacy'],
                'books': ['book', 'textbook', 'novel', 'reading', 'literature'],
                'toys': ['toy', 'game', 'play', 'children', 'kids'],
                'pets': ['pet', 'animal', 'dog', 'cat', 'puppy', 'kitten']
            }
            
            # Check each search word against related terms
            for word in search_words:
                for category, terms in related_terms.items():
                    if word in terms or any(term in field_value for term in terms):
                        if category not in related_matches:  # Avoid duplicates
                            related_matches.append(category)
            
            return exact_match
        
        # Split search term into words
        search_words = search_term.split()
        
        # Check each field for matches
        has_match = False
        
        # Check title (given higher priority)
        if check_field('title', donation.title, search_words):
            has_match = True
        
        # Check description
        if check_field('description', donation.description, search_words):
            has_match = True
        
        # Check category
        if check_field('category', donation.category, search_words):
            has_match = True
        
        # Check quantity
        if check_field('quantity', donation.quantity, search_words):
            has_match = True
        
        # Check condition
        if check_field('condition', donation.condition, search_words):
            has_match = True
        
        # Check location
        if check_field('location', donation.pickup_location, search_words):
            has_match = True
        
        # Check details (JSON field)
        if donation.details:
            for key, value in donation.details.items():
                if check_field(f'details_{key}', value, search_words):
                    has_match = True
        
        # Only include donations that had at least one match
        if has_match or not search_term:
            donation_dict['matches'] = matches
            donation_dict['related_matches'] = related_matches
            results.append(donation_dict)
    
    # Sort results by relevance
    results.sort(key=lambda x: (
        'title' in x['matches'],  # Title matches first
        len(x['matches']),        # Then by number of exact matches
        len(x['related_matches']) # Then by number of related matches
    ), reverse=True)
    
    print("\nSearch results:")
    print(f"Found {len(results)} matching donations")
    for result in results:
        print(f"- {result['title']}")
        print(f"  Matches: {result['matches']}")
        print(f"  Related: {result['related_matches']}")
    print("=== End Search ===\n")
    
    return jsonify(results)

@bp.route('/search')
def search():
    search_term = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    
    # Base query for available donations
    query = Donation.query.filter(
        Donation.status == 'available',
        Donation.expiry_time > datetime.utcnow()
    )
    
    # Apply search filter if search term is provided
    if search_term:
        query = query.filter(or_(
            Donation.title.ilike(f'%{search_term}%'),
            Donation.description.ilike(f'%{search_term}%'),
            Donation.pickup_location.ilike(f'%{search_term}%'),
            Donation.quantity.ilike(f'%{search_term}%'),
            Donation.condition.ilike(f'%{search_term}%'),
            Donation.category.ilike(f'%{search_term}%'),
            # Search in JSON details using PostgreSQL JSON operators
            Donation.details.cast(db.String).ilike(f'%{search_term}%')
        ))
    
    # Apply category filter if category is provided
    if category:
        query = query.filter(Donation.category == category)
    
    # Order by creation date, newest first
    query = query.order_by(Donation.created_at.desc())
    
    # Execute query and convert to list of dictionaries
    donations = [donation.to_dict() for donation in query.all()]
    
    return jsonify(donations)

@bp.route('/donations/delete/<int:id>', methods=['POST'])
@login_required
def delete_donation(id):
    donation = Donation.query.get_or_404(id)
    
    # Check if the current user is the donor of this donation
    if donation.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        db.session.delete(donation)
        db.session.commit()
        return jsonify({'message': 'Donation deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/donations/<int:id>/complete', methods=['POST'])
@login_required
def complete_donation(id):
    donation = Donation.query.get_or_404(id)
    
    # Check if user is the donor
    if donation.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized to complete this donation'}), 403
    
    # Check if donation is in reserved state
    if donation.status != 'reserved':
        return jsonify({'error': 'Only reserved donations can be completed'}), 400
    
    try:
        donation.status = 'completed'
        donation.completed_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Donation marked as completed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to complete donation'}), 500

@bp.route('/donations/<int:id>/cancel-reservation', methods=['POST'])
@login_required
def cancel_reservation(id):
    donation = Donation.query.get_or_404(id)
    
    # Check if user is the recipient
    if donation.recipient_id != current_user.id:
        return jsonify({'error': 'Unauthorized to cancel this reservation'}), 403
    
    # Check if donation is in reserved state
    if donation.status != 'reserved':
        return jsonify({'error': 'Only reserved donations can be cancelled'}), 400
    
    try:
        donation.status = 'available'
        donation.recipient_id = None
        donation.reserved_at = None
        db.session.commit()
        return jsonify({'message': 'Reservation cancelled successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to cancel reservation'}), 500

@bp.route('/donations/<int:id>/delete-reservation', methods=['POST'])
@login_required
def delete_reservation(id):
    donation = Donation.query.get_or_404(id)
    
    # Check if user is the donor or recipient
    if donation.user_id != current_user.id and donation.recipient_id != current_user.id:
        return jsonify({'error': 'Unauthorized to delete this reservation'}), 403
    
    # Check if donation is in reserved state
    if donation.status != 'reserved':
        return jsonify({'error': 'Only reserved donations can be deleted'}), 400
    
    try:
        # Reset the donation to available state
        donation.status = 'available'
        donation.recipient_id = None
        donation.reserved_at = None
        db.session.commit()
        return jsonify({'message': 'Reservation deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete reservation'}), 500

@bp.route('/donations/<int:id>/delete-completion', methods=['POST'])
@login_required
def delete_completion(id):
    donation = Donation.query.get_or_404(id)
    
    # Check if user is the donor
    if donation.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized to delete completion status'}), 403
    
    # Check if donation is in completed state
    if donation.status != 'completed':
        return jsonify({'error': 'Only completed donations can be reverted'}), 400
    
    try:
        # Reset the donation to reserved state
        donation.status = 'reserved'
        donation.completed_at = None
        db.session.commit()
        return jsonify({'message': 'Completion status deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete completion status'}), 500
