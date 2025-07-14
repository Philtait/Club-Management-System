from app.extensions import db

class Student(db.Model):
    __tablename__ = 'students'

    student_id              = db.Column(db.Integer, primary_key=True)
    user_id                 = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=True, nullable=False)
    school                  = db.Column(db.String(100))
    program                 = db.Column(db.String(100))
    year_of_study           = db.Column(db.Integer)
    expected_graduation_year= db.Column(db.Integer)
    interests               = db.Column(db.Text)

    user        = db.relationship('User', back_populates='student', uselist=False)
    memberships = db.relationship(
        'Membership',
        back_populates='student',
        cascade='all, delete-orphan'
    )
    payments    = db.relationship(
        'MpesaPayment',
        back_populates='student',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Student id={self.student_id} user_id={self.user_id}>"
