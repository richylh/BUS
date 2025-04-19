from os import write

from flask import render_template, redirect, url_for, flash, request, send_file, send_from_directory,session
from unicodedata import category

from app import app
from app.models import User, UniversityEmail, Event, Enrollment
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


@app.route("/")
def home():
    return render_template('home.html', title="Home")

@app.route("/account")
@login_required
def account():
    choose_form = ChooseForm()
    q = db.select(Enrollment).where(Enrollment.username == current_user.username)
    list_of_enrollments = db.session.scalars(q)
    return render_template('account.html', title="Account", list_of_enrollments = list_of_enrollments, choose_form = choose_form)

@app.route("/admin")
@login_required
def admin():
    if current_user.role != "Admin":
        return redirect(url_for('home'))
    form = ChooseForm()
    q = db.select(User)
    user_lst = db.session.scalars(q)
    q = db.select(Enrollment)
    list_of_enrollments = db.session.scalars(q)
    return render_template('admin.html', title="Admin", user_lst=user_lst, form=form, list_of_enrollments = list_of_enrollments)

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

@app.route('/events',  methods=['GET', 'POST'])
@login_required
def events():
    choose_form = ChooseForm()
    q = db.select(Event)
    list_of_events = db.session.scalars(q)
    return render_template('events.html', title="Events", list_of_events = list_of_events, choose_form = choose_form)

@app.route('/appointments')
def appointments():
    return redirect(url_for('home'))

@app.route('/manager', methods=['GET', 'POST'])
def manager():
    form = EventsForm()
    choose_form = ChooseForm()
    if form.validate_on_submit() and int(form.edit.data) == -1:
        new_event = Event(title=form.title.data, text=form.text.data, username=current_user.username, status = form.status.data, date = form.date.data, start_time = form.start_time.data, end_time = form.end_time.data, address = form.address.data )
        db.session.add(new_event)
        db.session.commit()
        return redirect(url_for('manager'))
    q = db.select(Event).where(Event.username == current_user.username)
    list_of_events = db.session.scalars(q)
    return render_template('manager.html', title="Event Management", form=form, list_of_events=list_of_events,
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
    items = Enrollment.query.filter_by(title = event_first.title).all()
    if not items:
        enroll = Enrollment(title=event_first.title, username=current_user.username,  date = event_first.date, start_time = event_first.start_time, end_time = event_first.end_time, address = event_first.address )
        db.session.add(enroll)
        db.session.commit()
        flash('Successfully enrolled in the event!', 'success')
        return redirect(url_for('events'))
    else:
        flash('Already enrolled in the event', 'warning')
        return redirect(url_for('events'))





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