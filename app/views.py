from os import write
from functools import wraps
from flask import render_template, redirect, url_for, flash, request, send_file, send_from_directory,session, jsonify
from unicodedata import category
from urllib3.connection import port_by_scheme

from app import app
from app.models import User, UniversityEmail, Appointment, Event, Enrollment, Psychologist, BookingLog
from app.forms import ChooseForm, LoginForm, ChangePasswordForm, ChangeEmailForm, RegisterForm, RegisterEmail, \
    RegisterEmailVerify, EventsForm
from flask_login import current_user, login_user, logout_user, login_required, fresh_login_required
import sqlalchemy as sa
from app import db
from urllib.parse import urlsplit
from sqlalchemy import or_
import csv
import io
import datetime
import random
import json
from sqlalchemy.exc import IntegrityError
import google.generativeai as genai
def admin_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.role != "Admin":
            return redirect(url_for('home'))
        return func(*args, **kwargs)
    return wrapper

@app.route("/")
def home():
    return render_template('home.html', title="Home")

@app.route("/account")
@login_required
def account():
    form = ChooseForm()
    choose_form = ChooseForm()
    q = db.select(Enrollment).where(Enrollment.username == current_user.username)
    list_of_enrollments = db.session.scalars(q)
    psychologist = db.session.get(Psychologist, current_user.id)
    p = db.select(Appointment).where(Appointment.user_name == current_user.username)
    list_of_appointments = db.session.scalars(p)
    return render_template('account.html', title="Account", list_of_enrollments = list_of_enrollments, choose_form = choose_form, psychologist =psychologist, form = form, list_of_appointments = list_of_appointments)

@app.route("/admin")
@login_required
@admin_only
def admin():
    # if current_user.role != "Admin":
    #     return redirect(url_for('home'))
    form = ChooseForm()
    q = db.select(User)
    user_lst = db.session.scalars(q)
    q = db.select(Enrollment)
    list_of_enrollments = db.session.scalars(q)
    p = db.select(Psychologist)
    list_of_psychologists = db.session.scalars(p)
    p = db.select(Appointment)
    list_of_appointments = db.session.scalars(p)
    return render_template('admin.html', title="Admin", user_lst=user_lst, form=form, list_of_enrollments = list_of_enrollments, list_of_psychologists = list_of_psychologists, list_of_appointments = list_of_appointments, choose_form = form)

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


@app.route('/toggle_user_type', methods=['POST'])
def toggle_user_type():
    form = ChooseForm()
    if form.validate_on_submit():
        u = db.session.get(User, int(form.choice.data))
        q = db.select(User).where((User.user_type == "Psychologist") & (User.id != u.id))
        first = db.session.scalars(q).first()
        if not first:
            flash("You can't drop your psychologist role if there are no other psychologist users!", "danger")
        elif u.id == current_user.id:
                logout_user()
                u.user_type = "user"
                db.session.commit()
                return redirect(url_for('home'))
        else:
            # u.role = "Normal" if u.role == "Admin" else "Admin"
            if u.user_type == "user":
                u.user_type = "Psychologist"
                #new = Psychologist(id = u.id, username = u.username, email = u.email, password_hash=u.password_hash, user_type= "Psychologist")
                #db.session.delete(u)
                #db.session.add(new)
                db.session.execute(sa.insert(Psychologist.__table__).values(id=u.id))
                db.session.commit()
            elif u.user_type == "Psychologist":
                u.user_type = "user"
               #new = User(id = u.id, username = u.username, email = u.email, password_hash=u.password_hash)
                #db.session.delete(u)
                #db.session.add(new)
                db.session.execute(sa.delete(Psychologist).where(Psychologist.id==u.id))
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

@app.route('/events',  methods=['GET', 'POST'])
@login_required
def events():
    choose_form = ChooseForm()
    q = db.select(Event)
    list_of_events = db.session.scalars(q)
    return render_template('events.html', title="Events", list_of_events = list_of_events, choose_form = choose_form)

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




@app.route('/toggle_user_availability', methods=['POST'])
def toggle_user_availability():
    form = ChooseForm()
    if form.validate_on_submit():
        u = db.session.get(Psychologist, int(form.choice.data))
        #q = db.select(User).where((User.user_type == "Psychologist") & (User.id != u.id))
        #first = db.session.scalars(q).first()
        #if not first:
            #flash("You can't drop your psychologist role if there are no other psychologist users!", "danger")
        #elif u.id == current_user.id:
                #logout_user()
                #u.user_type = "user"
                #db.session.commit()
                #return redirect(url_for('home'))
        #else:
            # u.role = "Normal" if u.role == "Admin" else "Admin"
        if u.availability == "Available":
            u.availability = "Unavailable"

            Appointment.query.filter_by(id=u.id).delete()
            BookingLog.query.filter_by(id=u.id).delete()
            # new = Psychologist(id = u.id, username = u.username, email = u.email, password_hash=u.password_hash, user_type= "Psychologist")
            # db.session.delete(u)
            # db.session.add(new)
            #db.session.execute(sa.insert(Psychologist.__table__).values(id=u.id))
            db.session.commit()
        elif u.availability == "Unavailable":
            u.availability = "Available"
            # new = User(id = u.id, username = u.username, email = u.email, password_hash=u.password_hash)
            # db.session.delete(u)
            # db.session.add(new)
            #db.session.execute(sa.delete(Psychologist).where(Psychologist.id == u.id))
            db.session.commit()
    return redirect(url_for('account'))




@app.route('/toggle_user_availability_/<int:psychologist_id>', methods=['POST'])
def toggle_user_availability_(psychologist_id):
    form = ChooseForm()
    if form.validate_on_submit():
        u = db.session.get(Psychologist, int(psychologist_id))
        #q = db.select(User).where((User.user_type == "Psychologist") & (User.id != u.id))
        #first = db.session.scalars(q).first()
        #if not first:
            #flash("You can't drop your psychologist role if there are no other psychologist users!", "danger")
        #elif u.id == current_user.id:
                #logout_user()
                #u.user_type = "user"
                #db.session.commit()
                #return redirect(url_for('home'))
        #else:
            # u.role = "Normal" if u.role == "Admin" else "Admin"
        if u.availability == "Available":
            u.availability = "Unavailable"

            Appointment.query.filter_by(id=u.id).delete()
            BookingLog.query.filter_by(id=u.id).delete()
            # new = Psychologist(id = u.id, username = u.username, email = u.email, password_hash=u.password_hash, user_type= "Psychologist")
            # db.session.delete(u)
            # db.session.add(new)
            #db.session.execute(sa.insert(Psychologist.__table__).values(id=u.id))
            db.session.commit()
        elif u.availability == "Unavailable":
            u.availability = "Available"
            # new = User(id = u.id, username = u.username, email = u.email, password_hash=u.password_hash)
            # db.session.delete(u)
            # db.session.add(new)
            #db.session.execute(sa.delete(Psychologist).where(Psychologist.id == u.id))
            db.session.commit()
    return redirect(url_for('admin'))









@app.route("/booking", methods=['GET', 'POST'])
def booking():
    # chosen = -1
    form = ChooseForm()
    schedule = generate_schedule()
    unavailable_slots = check_availability()
    q = db.select(Psychologist).where(Psychologist.availability == "Available")
    list_of_psychologists = db.session.scalars(q)
    if not current_user.is_authenticated:
        flash("Please log in to book an appointment.", "warning")
        return render_template('appointment.html', title='Appointment', schedule=schedule, form=form, unavailable_slots=unavailable_slots)

    if form.validate_on_submit() and current_user.user_type == "user" and current_user.role == "Normal":
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
        date_str = date.strftime("%Y-%m-%d")
        slot_str = slot.strftime("%H:%M")
        data_ = BookingLog.query.filter_by(user_id=current_user.id).first()
        appointment_ = Appointment.query.filter_by(user_id = current_user.id).first()
        if data_ and not appointment_:
            db.session.delete(data_)
            db.session.commit()

        try:
            # schedule[day_index]["slots"][slot_index]["availability"] = False
            appointment = BookingLog(
                user_id=current_user.id,
                date=date_str,
                weekday=weekday,
                slot=slot_str
            )
            db.session.add(appointment)
            db.session.commit()
            return render_template('choose_appointment.html', title = 'Appointment Booking', list_of_psychologists = list_of_psychologists )

        except IntegrityError as e:
            db.session.rollback()
            error_msg = str(e.orig)
            if "user_id" in error_msg:
                flash("You have already booked one.", "warning")
            elif "date" in error_msg and "slot" in error_msg:
                flash("Sorry, this slot is unavailable.", "warning")

    return render_template('appointment.html', title='Appointment', schedule=schedule, form=form, unavailable_slots=unavailable_slots)





@app.route("/cancel_appointment", methods=['POST'])
def cancel_appointment():
    form = ChooseForm()
    if form.validate_on_submit():
        appo = Appointment.query.filter_by(id = form.appo_id.data, user_id = form.user_id.data).first()
        log = BookingLog.query.filter_by(date= appo.date , slot=appo.slot).first()
        db.session.delete(log)
        db.session.delete(appo)
        db.session.commit()
    return redirect(url_for('account'))




@app.route("/delete_appointment", methods=['POST'])
def delete_appointment():
    form = ChooseForm()
    if form.validate_on_submit():
        appo = Appointment.query.filter_by(id = form.appo_id.data, user_id = form.user_id.data).first()
        log = BookingLog.query.filter_by(date= appo.date , slot=appo.slot).first()
        db.session.delete(log)
        db.session.delete(appo)
        db.session.commit()
    return redirect(url_for('account'))




@app.route("/delete_appointment_", methods=['POST'])
def delete_appointment_():
    form = ChooseForm()
    if form.validate_on_submit():
        appo = Appointment.query.filter_by(id = form.appo_id.data, user_id = form.user_id.data).first()
        log = BookingLog.query.filter_by(date= appo.date , slot=appo.slot).first()
        db.session.delete(log)
        db.session.delete(appo)
        db.session.commit()
    return redirect(url_for('admin'))




@app.route('/manager', methods=['GET', 'POST'])
def manager():
    form = EventsForm()
    choose_form = ChooseForm()
    if form.validate_on_submit() and int(form.edit.data) == -1:
        new_event = Event(title=form.title.data, text=form.text.data, username=current_user.username, status = form.status.data, date = form.date.data, start_time = form.start_time.data, end_time = form.end_time.data, address = form.address.data )
        db.session.add(new_event)
        db.session.commit()
        return redirect(url_for('manager'))
    q = db.select(Enrollment)
    list_of_enrollments = db.session.scalars(q)
    q = db.select(Event).where(Event.username == current_user.username)
    list_of_events = db.session.scalars(q)
    return render_template('manager.html', title="Event Management", form=form, list_of_events=list_of_events, list_of_enrollments = list_of_enrollments,
                           choose_form=choose_form)



@app.route("/delete_event", methods=['POST'])
def delete_event():
    form = ChooseForm()
    id = form.choice.data
    if form.validate_on_submit():
        event = db.session.get(Event, id )
        enroll = Enrollment.query.filter_by(title = event.title).first()
        if enroll is None:
            db.session.delete(event)
            db.session.commit()
            return redirect(url_for('manager'))
        else:
            db.session.delete(event)
            db.session.delete(enroll)
            db.session.commit()
            return redirect(url_for('manager'))



@app.route("/delete_event_", methods=['POST'])
def delete_event_():
    form = ChooseForm()
    id = form.choice.data
    if form.validate_on_submit():
        event = db.session.get(Event, id )
        enroll = Enrollment.query.filter_by(title = event.title).first()
        if enroll is None:
            db.session.delete(event)
            db.session.commit()
            return redirect(url_for('events'))
        else:
            db.session.delete(event)
            db.session.delete(enroll)
            db.session.commit()
            return redirect(url_for('events'))


@app.route("/edit_event/<int:event_id>", methods=['GET','POST'])
def edit_event(event_id):
    choose_form = ChooseForm()
    event_first = db.session.get(Event, event_id)
    form = EventsForm(edit = event_first.id,title=event_first.title, text=event_first.text, username = event_first.username, status = event_first.status, date = event_first.date, start_time = event_first.start_time, end_time = event_first.end_time, address = event_first.address )
    if form.validate_on_submit():
        event = db.session.get(Event, int(form.edit.data))
        enroll = Enrollment.query.filter_by(title=event_first.title).first()
        event.title = form.title.data
        event.text = form.text.data
        event.status = form.status.data
        event.date = form.date.data
        event.start_time = form.start_time.data
        event.end_time = form.end_time.data
        event.address = form.address.data
        if enroll is None:
            db.session.commit()
            return redirect(url_for('manager'))
        else:
            enroll.title = form.title.data
            enroll.status = form.status.data
            enroll.date = form.date.data
            enroll.start_time = form.start_time.data
            enroll.end_time = form.end_time.data
            enroll.address = form.address.data
            db.session.commit()
            return redirect(url_for('manager'))
    q = db.select(Event).where(Event.username == current_user.username)
    list_of_events = db.session.scalars(q)
    return render_template("manager.html", title="Event Management", form=form, choose_form=choose_form,
                           list_of_events = list_of_events)


@app.route("/enrollment/<int:event_id>", methods=['GET','POST'])
def enrollment(event_id):
    event_first = db.session.get(Event, event_id)
    items = Enrollment.query.filter_by(title = event_first.title, username = current_user.username).all()

    if not items:
        enroll = Enrollment(title=event_first.title, username=current_user.username,  date = event_first.date, start_time = event_first.start_time, end_time = event_first.end_time, address = event_first.address )
        db.session.add(enroll)
        db.session.commit()
        flash('Successfully enrolled in the event!', 'success')
        return redirect(url_for('events'))
    else:
        flash('Already enrolled in the event', 'warning')
        return redirect(url_for('events'))




@app.route("/book_an_appointment/<int:psychologist_id>", methods=['GET','POST'])
def book_an_appointment(psychologist_id):
    psychologist_first = db.session.get(Psychologist, psychologist_id)
    latest = db.session.query(BookingLog).order_by(BookingLog.id.desc()).first()
    data_ = Appointment.query.filter_by(id = psychologist_id, date= latest.date , slot=latest.slot).all()
    if not data_:
        appointment = Appointment(
            id=psychologist_first.id,
            user_id = current_user.id,
            date=latest.date,
            weekday=latest.weekday,
            slot=latest.slot,
            user_name = psychologist_first.username
        )
        #latest.id = psychologist_id
        db.session.add(appointment)
        db.session.commit()
        flash('Successfully booked the appointment!', 'success')
        return render_template('appointment_booked.html', title = 'Appointment Booked', appointment=appointment)

    else:
        db.session.delete(latest)
        db.session.commit()
        flash('Appointment has been booked', 'warning')
        return redirect(url_for('booking'))


@app.route("/delete_enrollment", methods=['POST'])
def delete_enrollment():
    form = ChooseForm()
    id = form.choice.data
    if form.validate_on_submit():
        enroll = db.session.get(Enrollment, id )
        db.session.delete(enroll)
        db.session.commit()
        return redirect(url_for('account'))
    return redirect(url_for('admin'))



@app.route("/delete_enrollment_", methods=['POST'])
def delete_enrollment_():
    form = ChooseForm()
    id = form.choice.data
    if form.validate_on_submit():
        enroll = db.session.get(Enrollment, id )
        db.session.delete(enroll)
        db.session.commit()
        return redirect(url_for('admin'))
    return redirect(url_for('admin'))



@app.route("/download_enrollments_csv", methods=['GET', 'POST'])
def download_enrollments_csv():
    enrollment = Enrollment.query.all()
    if not enrollment:
        headers_ = ['id', 'title', 'username']
        mem_str = io.StringIO()
        writer_ = csv.writer(mem_str)
        writer_.writerow(headers_)
        mem_bytes = io.BytesIO()
        mem_bytes.write(mem_str.getvalue().encode(encoding="utf-8"))
        mem_bytes.seek(0)
        return send_file(mem_bytes, as_attachment=True, download_name='enrollments.csv', mimetype='text/csv')
    else:
        headers_ = ['id', 'title', 'username']
        rows = [enrol.to_dict().values() for enrol in enrollment]
        mem_str = io.StringIO()
        writer_ = csv.writer(mem_str)
        writer_.writerow(headers_)
        writer_.writerows(rows)
        mem_bytes = io.BytesIO()
        mem_bytes.write(mem_str.getvalue().encode(encoding="utf-8"))
        mem_bytes.seek(0)
        return send_file(mem_bytes, as_attachment=True, download_name='enrollments.csv', mimetype='text/csv')


@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    import google.genai as genai
    from google.genai import types
    from flask import session
    system_instruction = (
        "You are UniSupport Bot, an empathetic AI assistant for UK university students on the UniSupport app. "
        "Your job is to provide initial guidance, reliable information, and helpful resources about mental wellbeing, stress, study habits, and student life. "
        "- Be calm, supportive, and non-judgmental. "
        "- You can share general wellbeing info, simple coping tips, and guide users to UniSupport app features. "
        "- Do NOT give medical advice, diagnosis, or act as a replacement for professional help. "
        "- In crisis (e.g., self-harm, suicide risk), clearly state your limits and provide UK emergency contacts: 999 and Samaritans 116 123. Do not try to counsel in crisis. "
        "- For ongoing/serious mental health issues, gently encourage seeking professional support. "
        "Always prioritize user safety and stay within your defined role."
    )
    if request.method == 'GET':
        session['chat_history'] = []
        return render_template('chat.html', title='Chat')
    if request.method == 'POST':
        data = request.get_json()
        user_message = data.get('message', '')
        api_key = "AIzaSyCvpZfGKLrpJsawpiM5KmsX6uu0vJvxru8"
        client = genai.Client(api_key=api_key)
        history = session.get('chat_history', [])
        contents = []
        for msg in history:
            if msg['role'] == 'user':
                contents.append({"role": "user", "parts": [{"text": msg['text']}]})
            elif msg['role'] == 'ai':
                contents.append({"role": "model", "parts": [{"text": msg['text']}]})
        contents.append({"role": "user", "parts": [{"text": user_message}]})
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-04-17",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            ai_text = response.text if hasattr(response, 'text') else str(response)
            session['chat_history'].append({'role': 'user', 'text': user_message})
            session['chat_history'].append({'role': 'ai', 'text': ai_text})
            session.modified = True
            return jsonify({'response': ai_text, 'history': session['chat_history']})
        except Exception as e:
            return jsonify({'response': f'Request failed: {str(e)}'}), 500


@app.route('/diagnose', methods=['POST'])
def diagnose():
    api_key = "AIzaSyCvpZfGKLrpJsawpiM5KmsX6uu0vJvxru8"
    import google.generativeai as genai
    genai.configure(api_key=api_key)

    # Get all chat history
    history = session.get('chat_history', [])
    chat_text = "\n".join([
        f"User: {msg['text']}" if msg['role']=='user' else f"AI: {msg['text']}" for msg in history
    ])

    prompt = (
        "Based on the following conversation between the user and the mental health chatbot, "
        "determine whether the user shows signs of psychological health problems. "
        "Respond with a JSON object: {\"has_psychological_problem\": true/false}.\n"
        + chat_text
    )
    model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")
    try:
        response = model.generate_content(
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            generation_config={
                "temperature": 0,
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "has_psychological_problem": {
                            "type": "boolean",
                            "description": "Whether the user has psychological health problems."
                        }
                    },
                    "required": ["has_psychological_problem"]
                }
            }
        )
        import json
        result = response.text
        data = json.loads(result)
        has_problem = data.get("has_psychological_problem", False)
        return jsonify({"has_psychological_problem": has_problem})
    except Exception:
        return jsonify({"error": "Diagnosis failed. Please try again."}), 500

    '''
    # Define function declaration
    diagnose_function = {
        "name": "diagnose_psychological_problem",
        "description": "Determine whether the user shows signs of psychological health problems.",
        "parameters": {
            "type": "object",
            "properties": {
                "has_psychological_problem": {
                    "type": "boolean",
                    "description": "Whether the user has psychological health problems. true means yes, false means no."
                }
            },
            "required": ["has_psychological_problem"]
        }
    }
    tools = [{
        "function_declarations": [diagnose_function]
    }]
    prompt = (
        "Based on the following conversation between the user and the mental health chatbot, determine whether the user shows signs of psychological health problems. "
        "Please only return a function call, do not output any extra text.\n"
        + chat_text
    )
    contents = [
        {
            "role": "user",
            "parts": [
                {"text": prompt}
            ]
        }
    ]
    response = model.generate_content(
        contents=contents,
        tools=tools,
        generation_config={"temperature": 0}
    )
    function_call = None
    try:
        function_call = response.candidates[0].content.parts[0].function_call
    except Exception:
        return jsonify({"error": "Diagnosis failed. Please try again."}), 500
    if function_call and function_call.name == "diagnose_psychological_problem":
        has_problem = function_call.args.get("has_psychological_problem", False)
        return jsonify({"has_psychological_problem": has_problem})
    return jsonify({"error": "Diagnosis failed. Please try again."}), 500
    '''


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