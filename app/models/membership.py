from app.extensions import db

class Membership(db.Model):
    __tablename__ = 'memberships'

    membership_id = db.Column(db.Integer, primary_key=True)
    student_id    = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    club_id       = db.Column(db.Integer, db.ForeignKey('clubs.club_id'), nullable=False)
    joined_on     = db.Column(db.DateTime, server_default=db.func.now())
    left_on       = db.Column(db.DateTime, nullable=True)
    status        = db.Column(db.Enum('Pending','Approved','Rejected', name='membership_status'),default='Pending',nullable=False)


    # Relationship to Student and Club
    student = db.relationship(
        'Student',
        back_populates='memberships'
    )
    club = db.relationship(
        'Club',
        back_populates='memberships'
    )

    def __repr__(self):
        return f"<Membership student_id={self.student_id} club_id={self.club_id}>"
