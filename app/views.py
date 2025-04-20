from flask import render_template, redirect, url_for, flash, request, send_file, send_from_directory,session
from app import app
from app.models import User, UniversityEmail, Appointment
from app.forms import ChooseForm, LoginForm, ChangePasswordForm, ChangeEmailForm, RegisterForm, RegisterEmail, \
    RegisterEmailVerify
from flask_login import current_user, login_user, logout_user, login_required, fresh_login_required
import sqlalchemy as sa
from app import db
from urllib.parse import urlsplit
from sqlalchemy import or_
import csv
import io
import datetime
import random
from sqlalchemy.exc import IntegrityError


@app.route("/")
def home():
    return render_template('home.html', title="Home")

@app.route("/account")
@login_required
def account():
    return render_template('account.html', title="Account")

@app.route("/admin")
@login_required
def admin():
    if current_user.role != "Admin":
        return redirect(url_for('home'))
    form = ChooseForm()
    q = db.select(User)
    user_lst = db.session.scalars(q)
    return render_template('admin.html', title="Admin", user_lst=user_lst, form=form)

@app.route('/delete_user', methods=['POST'])
def delete_user():
    form = ChooseForm()
    if form.validate_on_submit():
        u = db.session.get(User, int(form.choice.data))
        q = db.select(User).where((User.role == "Admin") & (User.id != u.id))
        first = db.session.scalars(q).first()
        if not first:
            flash("You can't delete your own account if there are no other admin users!", "danger")
        elif u.id == current_user.id:
            logout_user()
            db.session.delete(u)
            db.session.commit()
            return redirect(url_for('home'))
        else:
            db.session.delete(u)
            db.session.commit()
    return redirect(url_for('admin'))

@app.route('/toggle_user_role', methods=['POST'])
def toggle_user_role():
    form = ChooseForm()
    if form.validate_on_submit():
        u = db.session.get(User, int(form.choice.data))
        q = db.select(User).where((User.role == "Admin") & (User.id != u.id))
        first = db.session.scalars(q).first()
        if not first:
            flash("You can't drop your admin role if there are no other admin users!", "danger")
        elif u.id == current_user.id:
                logout_user()
                u.role = "Normal"
                db.session.commit()
                return redirect(url_for('home'))
        else:
            # u.role = "Normal" if u.role == "Admin" else "Admin"
            if u.role == "Normal":
                u.role = "Organiser"
            elif u.role == "Organiser":
                u.role = "Admin"
            elif u.role == "Admin":
                u.role = "Normal"
            db.session.commit()
    return redirect(url_for('admin'))

@app.route("/change_pw",methods=['POST','GET'])
def change_pw():
    form = ChangePasswordForm()
    if form.validate_on_submit() and current_user.check_password(form.password.data):
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Password has been changed!",'success')
        return redirect(url_for('account'))
    return render_template('generic_form.html',title='Change Password', form=form)

@app.route("/change_email",methods=['POST','GET'])
def change_email():
    form = ChangeEmailForm()
    if form.validate_on_submit() and current_user.check_password(form.password.data):
        current_user.email = form.new_email.data
        db.session.commit()
        flash("Email has been updated!",'success')
        return redirect(url_for('account'))
    return render_template('generic_form.html',title='Change Email', form=form)

@app.route("/register",methods=['POST','GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('account'))
    form = RegisterForm()
    if form.validate_on_submit():
        query_email = db.select(UniversityEmail).where(UniversityEmail.email == form.email.data)
        check_email = db.session.scalars(query_email).first()
        if check_email:
            new_user=User(username=form.username.data, email=form.email.data)
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
            login_user(user=new_user)
        else:
            flash("Error: not a valid university email!",'danger')
            return redirect(url_for('register_email'))
        return redirect(url_for('account'))

    return render_template('generic_form.html', title='Register',form=form)

@app.route("/register_email",methods=['POST','GET'])
def register_email():
    if current_user.is_authenticated:
        return redirect(url_for('account'))
    form = RegisterEmail()
    if form.validate_on_submit():
        query_email = db.select(UniversityEmail).where(UniversityEmail.email==form.email.data)
        check_email = db.session.scalars(query_email).first()
        if check_email:
            verify_code = str(random.randint(100000,999999))
            session['email'] = form.email.data
            session['verify_code'] = verify_code

            form = RegisterEmailVerify(email=check_email.email)
            flash(f"Verification code {verify_code} was emailed to you. Check your email!",'success')
            return render_template('register_verify.html', title='Verify', form=form)
        else:
            flash("Email not found! Try to check your university email again!",'danger')
            return redirect(url_for('register_email'))
    return render_template('generic_form.html', title='Register',form=form)

@app.route("/register_verify",methods=['POST','GET'])
def register_verify():
    if current_user.is_authenticated:
        return redirect(url_for('account'))
    form = RegisterEmailVerify()
    if form.validate_on_submit() and form.verify.data == session['verify_code']:
        query_email = db.select(UniversityEmail).where(UniversityEmail.email==form.email.data)
        check_email = db.session.scalars(query_email).first()
        if check_email:
            form = RegisterForm(username=check_email.username, email=check_email.email)
            return render_template('register_complete.html', title='Register', form=form)
    else:
        flash("Verification code not correct!",'danger')
        return render_template('register_verify.html', title='Verify', form=form)
    return render_template('register_verify.html', title='Verify',form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(or_(User.username == form.username.data, User.email == form.username.data)))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    return render_template('generic_form.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/events')
def events():
    return redirect(url_for('home'))

def generate_schedule():
    today = datetime.datetime.today().date()
    slots_per_day = ["09:00", "11:00", "14:00", "16:00"]
    # slots_per_day = [
    #     {"start": "09:00", "availability": True},
    #     {"start": "11:00", "availability": True},
    #     {"start": "14:00", "availability": True},
    #     {"start": "16:00", "availability": True},
    # ]
    schedule = []
    for i in range(7):
        date = today + datetime.timedelta(days=i)
        schedule.append({
            "weekday": date.strftime("%A"),
            "date": date.strftime("%m-%d"),
            "slots": slots_per_day
        })
    return schedule

def check_availability():
    q = db.select(Appointment).order_by(Appointment.date, Appointment.slot)
    unavailable_slots = db.session.scalars(q).all()
    return unavailable_slots

@app.route('/appointments')
def appointments():
    form = ChooseForm()
    schedule = generate_schedule()
    unavailable_slots = check_availability()
    return render_template('appointment.html', title='Appointment', schedule=schedule, form=form, unavailable_slots=unavailable_slots)

@app.route("/book", methods=['GET', 'POST'])
def book():
    # chosen = -1
    form = ChooseForm()
    schedule = generate_schedule()
    unavailable_slots = check_availability()
    if not current_user.is_authenticated:
        flash("Please log in to book an appointment.", "warning")
        return render_template('appointment.html', title='Appointment', schedule=schedule, form=form, unavailable_slots=unavailable_slots)

    if form.validate_on_submit():
        slot_id = form.choice.data
        # previous = form.current_choice.data or -1
        # if slot_id == previous:
        #     chosen = -1
        # else:
        #     chosen = slot_id

        day_index, slot_index = map(int, slot_id.split("-"))
        slot_str = schedule[day_index]["slots"][slot_index]
        date_str = schedule[day_index]["date"]
        weekday = schedule[day_index]["weekday"]

        # day_index, slot_index = map(int, slot_id.split("-"))
        # slot_str = schedule[day_index]["slots"][slot_index]["start"]
        # date_str = schedule[day_index]["date"]
        # weekday = schedule[day_index]["weekday"]

        this_year = datetime.datetime.today().year
        date = datetime.datetime.strptime(date_str, "%m-%d").date().replace(year=this_year)
        slot = datetime.datetime.strptime(slot_str, "%H:%M").time()

        try:
            # schedule[day_index]["slots"][slot_index]["availability"] = False
            appointment = Appointment(
                user_id=current_user.id,
                date=date,
                weekday=weekday,
                slot=slot
            )
            current_user.appointments.append(appointment)
            db.session.commit()
            return render_template('appointment_booked.html', title = 'Appointment Booked', appointment=appointment)

        except IntegrityError as e:
            db.session.rollback()
            error_msg = str(e.orig)
            if "user_id" in error_msg:
                flash("You have already booked one.", "warning")
            elif "date" in error_msg and "slot" in error_msg:
                flash("Sorry, this slot is unavailable.", "warning")

    return render_template('appointment.html', title='Appointment', schedule=schedule, form=form, unavailable_slots=unavailable_slots)


# Error handlers
# See: https://en.wikipedia.org/wiki/List_of_HTTP_status_codes

# Error handler for 403 Forbidden
@app.errorhandler(403)
def error_403(error):
    return render_template('errors/403.html', title='Error'), 403

# Handler for 404 Not Found
@app.errorhandler(404)
def error_404(error):
    return render_template('errors/404.html', title='Error'), 404

@app.errorhandler(413)
def error_413(error):
    return render_template('errors/413.html', title='Error'), 413

# 500 Internal Server Error
@app.errorhandler(500)
def error_500(error):
    return render_template('errors/500.html', title='Error'), 500