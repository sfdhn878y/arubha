from flask import Flask,render_template,request,session,redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placement.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "secret_key_123"


db = SQLAlchemy(app)



class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20), nullable=False)

    # approval for company registration
    is_approved = db.Column(db.Boolean, default=False)

    # blacklist / account status
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # student profile relationlpo
    student_profile = db.relationship(
        "StudentProfile",
        back_populates="user",
        cascade="all, delete"
    )

    # company profile relation
    company_profile = db.relationship(
        "CompanyProfile",
        back_populates="user",
        cascade="all, delete"
    )

class Adhar_nu(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    adhar_number = db.Column(db.String(200))



    # user_name_bacref = db.relationship('User_name',back_populates='adhar_number_backref')

class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    branch = db.Column(db.String(100))
    cgpa = db.Column(db.Float)
    skills = db.Column(db.String(200))

    # Relationship to User
    user = db.relationship(
        "User",
        back_populates="student_profile"
    )

    # Relationship to Application
    applications = db.relationship(
        "Application",
        back_populates="student",
        cascade="all, delete"
    )


class CompanyProfile(db.Model):
    __tablename__ = "company_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    company_name = db.Column(db.String(150))
    company_email = db.Column(db.String(120))
    contact_number = db.Column(db.String(20))
    city_name = db.Column(db.String(100))
    established_year = db.Column(db.Integer)

    user = db.relationship(
        "User",
        back_populates="company_profile"
    )

    jobs = db.relationship(
        "Job",
        back_populates="company",
        cascade="all, delete"
    )


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("company_profiles.id"),
        nullable=False
    )

    job_type = db.Column(db.String(50))
    stipend = db.Column(db.String(50))
    last_date_to_apply = db.Column(db.Date)

    is_approved = db.Column(db.Boolean, default=False)
    is_closed = db.Column(db.Boolean, default=False)

    company = db.relationship(
        "CompanyProfile",
        back_populates="jobs"
    )

    applications = db.relationship(
        "Application",
        back_populates="job",
        cascade="all, delete"
    )

class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)

    # Many applications for one job
    job_ref = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id"),
        nullable=False
    )

    # Many applications by one student
    student_ref = db.Column(
        db.Integer,
        db.ForeignKey("student_profiles.id"),
        nullable=False
    )

    # Application Status
    current_status = db.Column(
        db.String(50),
        default="Pending",
        nullable=False
    )

    # Date submitted
    date_submitted = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Extra fields (missing in your model)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    remarks = db.Column(db.String(200))

    # Relationships
    job = db.relationship(
        "Job",
        back_populates="applications"
    )

    student = db.relationship(
        "StudentProfile",
        back_populates="applications"
    )

@app.route("/")
def index():
    return render_template("index.html")


@app.route('/index',methods=['POST','GET'])
def index_page():
    # if request.method == 'POST':
    #     adhar_number  = request.form.get('adhar_number')
    #     adhar_number_bd = Adhar_nu(adhar_number=adhar_number)
    #     db.session.add(adhar_number_bd)
    #     db.session.commit()
    adhar_number= request.args.get('adhar_number')
    adhar_number_bd = Adhar_nu(adhar_number=adhar_number)
    db.session.add(adhar_number_bd)
    db.session.commit()    
    return render_template('test.html',adhar_number=adhar_number)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        if role == "admin":
            return "Admin cannot be registered"

        if User.query.filter_by(email=email).first():
            return "Email already registered"

        user = User(
            name=name,
            email=email,
            password=password,
            role=role,
            is_approved=False if role == "company" else True
        )

        db.session.add(user)
        db.session.commit()
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        print(email, password)

        user = User.query.filter_by(email=email).first()

        if not user:
            return "No user found"

        if user.password != password:
            return "Wrong password"

        # block blacklisted users
        if not user.is_active:
            return "Your account is blacklisted by admin"

        # company approval check
        if user.role == "company" and not user.is_approved:
            return "You are not approved yet"

        # create session only if everything is valid
        session["user_id"] = user.id
        session["role"] = user.role

        if user.role == "admin":
            return redirect("/admin_dashboard")

        elif user.role == "student":
            return redirect("/student_dashboard")

        elif user.role == "company":
            return redirect("/company_dashboard")

    return render_template("login.html")

@app.route("/company_dashboard")
def company_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "company":
        return "Unauthorized", 403

    user_id = session["user_id"]

    company = CompanyProfile.query.filter_by(user_id=user_id).first()

    if not company:
        return redirect("/company_profile")

    jobs = Job.query.filter_by(company_id=company.id).all()

    job_list = []

    for j in jobs:

        total_apps = Application.query.filter_by(job_ref=j.id).count()

        job_list.append({
            "job": j,
            "total_apps": total_apps
        })

    # shortlisted students
    shortlisted = Application.query.join(Job).filter(
        Job.company_id == company.id,
        Application.current_status == "Shortlisted"
    ).all()

    # selected students
    selected = Application.query.join(Job).filter(
        Job.company_id == company.id,
        Application.current_status == "Selected"
    ).all()

    return render_template(
        "company_dashboard.html",
        company=company,
        jobs=job_list,
        shortlisted=shortlisted,
        selected=selected
    )
@app.route("/company-details/<int:company_id>")
def company_details(company_id):

    # must be logged in
    if "user_id" not in session:
        return redirect("/login")

    # only students should access
    if session.get("role") != "student":
        return "Unauthorized", 403

    # get company
    company = CompanyProfile.query.get_or_404(company_id)

    return render_template(
        "company_details.html",
        company=company
    )

@app.route("/company_profile", methods=["GET", "POST"])
def company_profile():

    user_id = session.get("user_id")

    if not user_id:
        return redirect("/login")

    company = CompanyProfile.query.filter_by(user_id=user_id).first()

    if request.method == "POST":

        
        if company:
            company.company_name = request.form["company_name"]
            company.company_email = request.form["company_email"]
            company.contact_number = request.form["contact_number"]
            company.city_name = request.form["city_name"]
            company.established_year =int(request.form["established_year"])

        
        else:
            company = CompanyProfile(
                user_id=user_id,
                company_name=request.form["company_name"],
                company_email=request.form["company_email"],
                contact_number=request.form["contact_number"],
                city_name=request.form["city_name"],
                established_year=request.form["established_year"]
            )   
            db.session.add(company)

        db.session.commit()
        return redirect("/company_dashboard")

    return render_template("company_profile.html", company=company)

@app.route("/admin/company/<int:user_id>")
def admin_view_company(user_id):

    if session.get("role") != "admin":
        return redirect("/login")

    user = User.query.get_or_404(user_id)

    company = CompanyProfile.query.filter_by(
        user_id=user.id
    ).first()

    jobs = []
    if company:
        jobs = company.jobs

    return render_template(
        "admin_company_details.html",
        user=user,
        company=company,
        jobs=jobs
    )

@app.route("/admin/company/<int:user_id>/blacklist")
def admin_blacklist_company(user_id):

    if session.get("role") != "admin":
        return redirect("/login")

    user = User.query.get_or_404(user_id)

    user.is_active = False   # blacklist

    db.session.commit()

    return redirect("/admin_dashboard")

@app.route("/admin/company/<int:user_id>/unblacklist")
def admin_unblacklist_company(user_id):

    if session.get("role") != "admin":
        return redirect("/login")

    user = User.query.get_or_404(user_id)

    user.is_active = True   # restore

    db.session.commit()

    return redirect("/admin_dashboard")


@app.route("/admin/student/<int:user_id>")
def admin_view_student(user_id):

    if session.get("role") != "admin":
        return redirect("/login")

    user = User.query.get_or_404(user_id)

    student = StudentProfile.query.filter_by(
        user_id=user.id
    ).first()

    applications = []
    if student:
        applications = student.applications

    return render_template(
        "admin_student_details.html",
        user=user,
        student=student,
        applications=applications
    )


@app.route("/admin/user/toggle/<int:user_id>")
def toggle_user_status(user_id):

    if session.get("role") != "admin":
        return redirect("/login")

    user = User.query.get_or_404(user_id)

    # toggle status
    if user.is_approved:
        user.is_approved = False
    else:
        user.is_approved = True

    db.session.commit()

    return redirect("/admin_dashboard")

@app.route("/admin/user/toggle/<int:user_id>")
def toggle_user(user_id):
    print('toogle user')
    if session.get("role") != "admin":
        return redirect("/login")

    user = User.query.get_or_404(user_id)

    user.is_approved = not user.is_approved

    db.session.commit()

    return redirect("/admin_dashboard")

@app.route("/admin/student/<int:user_id>/blacklist")
def admin_blacklist_student(user_id):

    if session.get("role") != "admin":
        return redirect("/login")

    user = User.query.get_or_404(user_id)

    user.is_active = False

    db.session.commit()

    return redirect("/admin_dashboard") 

@app.route("/admin/student/<int:user_id>/unblacklist")
def admin_unblacklist_student(user_id):

    if session.get("role") != "admin":
        return redirect("/login")

    user = User.query.get_or_404(user_id)

    user.is_active = True

    db.session.commit()

    return redirect("/admin_dashboard")
@app.route("/admin/job/<int:job_id>/applications")
def admin_job_applications(job_id):

    if session.get("role") != "admin":
        return redirect("/login")

    job = Job.query.get_or_404(job_id)

    applications = Application.query.filter_by(
        job_ref=job.id
    ).all()

    return render_template(
        "admin_job_applications.html",
        job=job,
        applications=applications
    )

@app.route("/post-job", methods=["GET","POST"])
def post_job():

    if "user_id" not in session:
        return redirect("/login")

    company = CompanyProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return redirect("/company_profile")

    if request.method == "POST":

        job_type = request.form["job_type"]
        stipend = request.form["stipend"]

        last_date = datetime.strptime(
            request.form["last_date_to_apply"],
            "%Y-%m-%d"
        )

        # prevent duplicate active job
        existing_job = Job.query.filter_by(
            company_id=company.id,
            job_type=job_type,
            is_closed=False
        ).first()

        if existing_job:
            return "This job already exists. Close it before posting again."

        job = Job(
            company_id=company.id,
            job_type=job_type,
            stipend=stipend,
            last_date_to_apply=last_date
        )

        db.session.add(job)
        db.session.commit()

        return redirect("/company_dashboard")

    return render_template("job_post.html")


@app.route("/apply-job/<int:job_id>")
def apply_job(job_id):

    if "user_id" not in session:
        return redirect("/login")

    # Get student profile
    student = StudentProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not student:
        return "Complete profile first!"

    # Get job
    job = Job.query.get_or_404(job_id)

    if not job.is_approved or job.is_closed:
        return "Job not available"

    # Check if already applied using correct column names
    existing = Application.query.filter_by(
        job_ref=job_id,
        student_ref=student.id
    ).first()

    if existing:
        return "Already applied!"

    # Create new application
    new_application = Application(
        job_ref=job_id,
        student_ref=student.id
    )

    db.session.add(new_application)
    db.session.commit()

    return redirect("/student_dashboard")

    
@app.route("/delete-job/<int:job_id>", methods=["POST"])
def delete_job(job_id):

    if "user_id" not in session or session.get("role") != "company":
        return redirect("/login")

    company = CompanyProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return "Company profile not found", 404

    job = Job.query.filter_by(
        id=job_id,
        company_id=company.id
    ).first()

    if not job:
        return "Job not found", 404

    # Check if applications exist (using job_ref)
    application_count = Application.query.filter_by(
        job_ref=job.id
    ).count()

    if application_count > 0:
        return render_template(
            "delete_warning.html",
            job=job,
            application_count=application_count
        )

    db.session.delete(job)
    db.session.commit()

    return redirect("/company_dashboard")

@app.route("/confirm-delete/<int:job_id>", methods=["POST"])
def confirm_delete(job_id):

    if "user_id" not in session or session.get("role") != "company":
        return redirect("/login")

    company = CompanyProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return "Company not found", 404

    job = Job.query.filter_by(
        id=job_id,
        company_id=company.id
    ).first()

    if not job:
        return "Job not found", 404

    # Delete related applications first
    Application.query.filter_by(
        job_ref=job.id
    ).delete()

    db.session.delete(job)
    db.session.commit()

    return redirect("/company_dashboard")



@app.route("/job-applications/<int:job_id>")
def view_applications(job_id):

    # Check login
    if "user_id" not in session:
        return redirect("/login")

    # Get the job
    job = Job.query.get(job_id)

    if not job:
        return "Job not found"

    # Make sure logged-in company owns this job
    company = CompanyProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company or job.company_id != company.id:
        return "Not authorized"

    # Get applications using correct column name
    applications = Application.query.filter_by(
        job_ref=job_id
    ).all()

    return render_template(
        "applications.html",
        job=job,
        applications=applications
    ) 


@app.route("/toggle-status/<int:app_id>/<string:action>")
def toggle_status(app_id, action):

    if "user_id" not in session:
        return redirect("/login")

    application = Application.query.get_or_404(app_id)

    # Optional: check if company owns this job
    company = CompanyProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company or application.job.company_id != company.id:
        return "Not authorized"

    # ===============================
    # TOGGLE LOGIC (using current_status)
    # ===============================

    if action == "shortlist":
        if application.current_status == "Shortlisted":
            application.current_status = "Pending"
        else:
            application.current_status = "Shortlisted"

    elif action == "select":
        if application.current_status == "Selected":
            application.current_status = "Shortlisted"
        else:
            application.current_status = "Selected"

    elif action == "reject":
        if application.current_status == "Rejected":
            application.current_status = "Pending"
        else:
            application.current_status = "Rejected"

    db.session.commit()

    return redirect(request.referrer)

    
@app.route("/student_dashboard")
def student_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    # get search value from URL
    search = request.args.get("search")

    # get student profile
    student = StudentProfile.query.filter_by(user_id=user_id).first()

    # base query
    query = Job.query.filter_by(is_approved=True, is_closed=False)

    # apply search filter
    if search:
        query = query.join(CompanyProfile).filter(
            (Job.job_type.ilike(f"%{search}%")) |
            (CompanyProfile.company_name.ilike(f"%{search}%"))
        )

    jobs = query.all()

    applied_jobs_dict = {}

    if student:
        for app in student.applications:
            applied_jobs_dict[app.job_ref] = app

    return render_template(
        "student_dashboard.html",
        student=student,
        jobs=jobs,
        applied_jobs_dict=applied_jobs_dict
    )
    
@app.route("/company/student/<int:student_id>")
def view_student_profile(student_id):
    # Check if logged in
    if "user_id" not in session:
        return redirect("/login")

    # Check if the user is a company
    if session.get("role") != "company":
        return "Unauthorized", 403

    # Get the company profile of logged-in user
    company = CompanyProfile.query.filter_by(user_id=session["user_id"]).first()
    if not company:
        return "Company profile not found", 404

    # Get the student profile
    student = StudentProfile.query.filter_by(id=student_id).first()
    if not student:
        return "Student not found", 404

    # Get only the applications of this student to this company's jobs
    applications = [
        app for app in student.applications
        if app.job.company_id == company.id
    ]

    total_applied = len(applications)

    # Render the simple template
    return render_template(
        "student_details.html",  # make sure this matches your HTML filename
        student=student,
        applications=applications,
        total_applied=total_applied
    )



@app.route("/student_profile", methods=["GET", "POST"])
def student_profile():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    student = StudentProfile.query.filter_by(
        user_id=user_id
    ).first()

    if request.method == "POST":

        if not student:
            student = StudentProfile(user_id=user_id)
            db.session.add(student)

        # ✅ Match your actual columns
        student.branch = request.form["branch"]
        student.cgpa = float(request.form["cgpa"])
        student.skills = request.form["skills"]

        db.session.commit()

        return redirect("/student_dashboard")

    return render_template(
        "student_profile.html",
        student=student
    ) 

# ==============================
# ADMIN DASHBOARD
# ==============================

@app.route("/admin_dashboard")
def admin_dashboard():

    if session.get("role") != "admin":
        return redirect("/login")

    # ===== Search values =====
    company_search = request.args.get("company_search")
    student_search = request.args.get("student_search")

    # ===== Stats =====
    total_students = User.query.filter_by(role="student").count()
    total_companies = User.query.filter_by(role="company").count()
    total_jobs = Job.query.count()
    total_applications = Application.query.count()

    # ===== Pending =====
    pending_companies = User.query.filter_by(
        role="company",
        is_approved=False
    ).all()

    pending_jobs = Job.query.filter_by(
        is_approved=False
    ).all()

    # ===== Companies Search =====
    if company_search:
        all_companies = User.query.filter(
            User.role == "company",
            (User.name.ilike(f"%{company_search}%")) |
            (User.email.ilike(f"%{company_search}%"))
        ).all()
    else:
        all_companies = User.query.filter_by(role="company").all()

    # ===== Students Search =====
    if student_search:
        all_students = User.query.filter(
            User.role == "student",
            (User.name.ilike(f"%{student_search}%")) |
            (User.email.ilike(f"%{student_search}%"))            
        ).all()
    else:
        all_students = User.query.filter_by(role="student").all()

    # ===== Jobs =====
    all_jobs = Job.query.all()

    return render_template(
        "admin_dashboard.html",
        total_students=total_students,
        total_companies=total_companies,
        total_jobs=total_jobs,
        total_applications=total_applications,
        pending_companies=pending_companies,
        pending_jobs=pending_jobs,
        all_students=all_students,
        all_companies=all_companies,
        all_jobs=all_jobs
    )

@app.route("/my-applications")
def my_applications():

    # check login
    if "user_id" not in session:
        return redirect("/login")

    # get student profile
    student = StudentProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not student:
        return "Complete your profile first"

    # get all applications
    applications = Application.query.filter_by(
        student_ref=student.id
    ).all()

    return render_template(
        "my_applications.html",
        applications=applications
    )

@app.route("/toggle-job/<int:job_id>")
def toggle_job(job_id):

    # check login
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "company":
        return "Unauthorized", 403

    # get company profile
    company = CompanyProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return "Company profile not found"

    # get job that belongs to this company
    job = Job.query.filter_by(
        id=job_id,
        company_id=company.id
    ).first()

    if not job:
        return "Job not found"

    # toggle status
    if job.is_closed:
        job.is_closed = False
    else:
        job.is_closed = True

    db.session.commit()

    return redirect("/company_dashboard")


@app.route("/edit-job/<int:job_id>", methods=["GET","POST"])
def edit_job(job_id):

    # check login
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "company":
        return "Unauthorized", 403

    # get company
    company = CompanyProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return "Company profile not found"

    # get job that belongs to this company
    job = Job.query.filter_by(
        id=job_id,
        company_id=company.id
    ).first()

    if not job:
        return "Job not found"

    if request.method == "POST":

        # update values
        job.job_type = request.form["job_type"]
        job.stipend = request.form["stipend"]

        job.last_date_to_apply = datetime.strptime(
            request.form["last_date_to_apply"],
            "%Y-%m-%d"
        )

        db.session.commit()

        return redirect("/company_dashboard")

    return render_template("edit_job.html", job=job)


@app.route("/admin/company/<int:user_id>/approve")
def approve_company(user_id):

    if session.get("role") != "admin":
        return redirect("/login")

    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()

    return redirect("/admin_dashboard")
@app.route("/admin/company/<int:user_id>/reject")
def reject_company(user_id):

    if session.get("role") != "admin":
        return redirect("/login")

    user = User.query.get_or_404(user_id)

    # delete company completely (since no is_active column exists)
    db.session.delete(user)
    db.session.commit()

    return redirect("/admin_dashboard")
@app.route("/admin/job/<int:job_id>/approve")
def approve_job(job_id):

    if session.get("role") != "admin":
        return redirect("/login")

    job = Job.query.get_or_404(job_id)
    job.is_approved = True
    db.session.commit()

    return redirect("/admin_dashboard")
@app.route("/admin/job/<int:job_id>/reject")
def reject_job(job_id):

    if session.get("role") != "admin":
        return redirect("/login")

    job = Job.query.get_or_404(job_id)
    job.is_closed = True
    db.session.commit()

    return redirect("/admin_dashboard")
@app.route("/admin/students")
def view_students():

    if session.get("role") != "admin":
        return redirect("/login")

    search = request.args.get("search")

    query = User.query.filter_by(role="student")

    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )

    students = query.all()

    return render_template("admin_students.html", students=students)

@app.route("/admin/companies")
def view_companies():

    if session.get("role") != "admin":
        return redirect("/login")

    search = request.args.get("search")

    query = CompanyProfile.query

    if search:
        query = query.filter(
            (CompanyProfile.company_name.ilike(f"%{search}%")) |
            (CompanyProfile.city_name.ilike(f"%{search}%"))
        )

    companies = query.all()

    return render_template("admin_companies.html", companies=companies)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    with app.app_context():

        db.create_all()

        existing_admin = User.query.filter_by(
            email="admin@gmail.com"
        ).first()

        if not existing_admin:

            admin_db = User(
                name="admin",
                email="admin@gmail.com",
                password="admin",
                role="admin",
                is_approved=True   # ✅ important
            )

            db.session.add(admin_db)
            db.session.commit()

    app.run(debug=True)