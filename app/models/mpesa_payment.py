# File: app/models/mpesa_payment.py

from app.extensions import db

class MpesaPayment(db.Model):
    __tablename__ = 'mpesa_payments'

    payment_id       = db.Column(db.Integer, primary_key=True)
    student_id       = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    transaction_code = db.Column(db.String(100), unique=True, nullable=False)
    amount           = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date     = db.Column(db.DateTime, server_default=db.func.now())
    purpose          = db.Column(db.Enum('Membership', 'Event', 'Donation'), nullable=False)
    related_id       = db.Column(db.Integer)  # club_id or event_id
    status           = db.Column(db.Enum('Pending', 'Completed', 'Failed'), default='Pending')

    # link back to the student who paid
    student = db.relationship(
        'Student',
        back_populates='payments'
    )

    # when purpose=='Membership', treat related_id as club_id
    club = db.relationship(
        'Club',
        primaryjoin='MpesaPayment.related_id == Club.club_id',
        foreign_keys=[related_id],
        viewonly=True
    )

    # when purpose=='Event', treat related_id as event_id
    event = db.relationship(
        'Event',
        primaryjoin='MpesaPayment.related_id == Event.event_id',
        foreign_keys=[related_id],
        viewonly=True
    )

    

    def __repr__(self):
        return f"<MpesaPayment id={self.payment_id} student={self.student_id} amount={self.amount}>"
