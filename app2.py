class User_name(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(200))

    # adhar_number_backref = db.relationship('Adhar_nu',back_populates='user_name_bacref')


    adhar_number = db.relationship('Adhar_nu',backref='user_name_bacref')





