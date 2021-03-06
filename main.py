from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask import Flask, render_template, redirect, request, abort
from forms.user import RegisterForm
from forms.login import LoginForm
from forms.job import JobsForm
from data import db_session, jobs_api
from data.users import User
from data.jobs import Jobs

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init(f"db/mars_db.sqlite")
    app.register_blueprint(jobs_api.blueprint)
    app.run()


@app.route('/')
def index():
    try:
        db_sess = db_session.create_session()
        works = db_sess.query(Jobs).all()
        team_leaders = [(" ").join(element) for element
                        in db_sess.query(User.surname,
                                         User.name).filter(User.id == Jobs.team_leader).all()]
    except AttributeError:
        works = []
        team_leaders = []
    return render_template('index.html', title="Главная страница", jobs=works, team_leaders=team_leaders)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            surname=form.surname.data,
            age=form.age.data,
            speciality=form.speciality.data,
            address=form.address.data,
            position=form.position.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/jobs', methods=['GET', 'POST'])
@login_required
def jobs():
    form = JobsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        jobs = Jobs()
        jobs.team_leader = form.team_leader.data
        jobs.job = form.jobs.data
        jobs.work_size = form.work_size.data
        jobs.collaborators = form.collaborators.data
        jobs.is_finished = form.is_finished.data
        current_user.jobs.append(jobs)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('jobs.html', title='Добавление работы',
                           form=form)


@app.route("/jobs_edit/<int:id>", methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = JobsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        action = db_sess.query(Jobs).filter(Jobs.id == id,
                                            Jobs.user == current_user
                                            ).first()
        if action:
            form.team_leader.data = action.team_leader
            form.jobs.data = action.job
            form.work_size.data = action.work_size
            form.collaborators.data = action.collaborators
            form.is_finished.data = action.is_finished
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        action = db_sess.query(Jobs).filter(Jobs.id == id,
                                            Jobs.user == current_user
                                            ).first()
        if action:
            action.team_leader = form.team_leader.data
            action.job = form.jobs.data
            action.work_size = form.work_size.data
            action.collaborators = form.collaborators.data
            action.is_finished = form.is_finished.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('jobs'
                           '.html',
                           title='Редактирование работ',
                           form=form)


@app.route('/jobs_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    action = db_sess.query(Jobs).filter(Jobs.id == id,
                                        Jobs.user == current_user
                                        ).first()
    if action:
        db_sess.delete(action)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    main()
