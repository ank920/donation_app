from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SubmitField, FloatField, SelectField, IntegerField, DateTimeField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from datetime import datetime

class DonationForm(FlaskForm):
    category = SelectField('Category', 
                         choices=[
                             ('food', 'Food Donation'),
                             ('clothes', 'Clothes Donation'),
                             ('pets', 'Pet Adoption'),
                             ('books', 'Books & Education'),
                             ('toys', 'Toys & Games'),
                             ('medical', 'Medical Supplies')
                         ],
                         validators=[DataRequired()])
    
    title = StringField('Title', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description', validators=[DataRequired()])
    quantity = StringField('Quantity', validators=[DataRequired(), Length(max=50)])
    condition = SelectField('Condition',
                          choices=[
                              ('new', 'New'),
                              ('excellent', 'Excellent'),
                              ('good', 'Good'),
                              ('fair', 'Fair')
                          ],
                          validators=[DataRequired()])
    
    contact_phone = StringField('Contact Phone', validators=[DataRequired(), Length(max=20)], description='Phone number for donation coordination')
    
    # Food-specific fields
    food_type = SelectField('Food Type',
                          choices=[
                              ('fresh', 'Fresh Produce'),
                              ('packaged', 'Packaged Food'),
                              ('cooked', 'Cooked Meals'),
                              ('beverages', 'Beverages'),
                              ('other', 'Other')
                          ],
                          validators=[Optional()])
    
    # Pet-specific fields
    pet_type = SelectField('Pet Type',
                         choices=[
                              ('dog', 'Dog'),
                              ('cat', 'Cat'),
                              ('bird', 'Bird'),
                              ('fish', 'Fish'),
                              ('other', 'Other')
                         ],
                         validators=[Optional()])
    pet_age = IntegerField('Pet Age (months)', validators=[Optional(), NumberRange(min=0)])
    
    # Book-specific fields
    book_type = SelectField('Book Type',
                         choices=[
                              ('textbook', 'Textbook'),
                              ('fiction', 'Fiction'),
                              ('non-fiction', 'Non-Fiction'),
                              ('children', 'Children\'s Books'),
                              ('other', 'Other')
                         ],
                         validators=[Optional()])
    
    # Medical supplies specific fields
    medical_type = SelectField('Medical Supply Type',
                           choices=[
                               ('equipment', 'Medical Equipment'),
                               ('supplies', 'Medical Supplies'),
                               ('medicines', 'Medicines'),
                               ('other', 'Other')
                           ],
                           validators=[Optional()])
    
    expiry_time = DateTimeField('Expiry Date & Time', 
                               format='%Y-%m-%dT%H:%M',  # Format for datetime-local input
                               validators=[Optional()],
                               render_kw={"type": "datetime-local"})
    pickup_location = StringField('Pickup Location', validators=[DataRequired(), Length(max=200)])
    latitude = FloatField('Latitude', validators=[Optional()])
    longitude = FloatField('Longitude', validators=[Optional()])
    special_instructions = TextAreaField('Special Instructions', validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('Submit Donation')

class ReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[(str(i), str(i)) for i in range(1, 6)], validators=[DataRequired()])
    comment = TextAreaField('Comment', validators=[DataRequired(), Length(min=10, max=500)])
    submit = SubmitField('Submit Review')
