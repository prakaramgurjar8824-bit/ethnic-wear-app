from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ethnicwear2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Prakaram.2407@localhost/ethnicwear'
app.config['UPLOAD_FOLDER'] = 'static/images'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

# ── Models ──────────────────────────────
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))

class Slider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(200))
    caption = db.Column(db.String(200))
    order_num = db.Column(db.Integer, default=0)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    order_num = db.Column(db.Integer, default=0)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    image = db.Column(db.String(200))
    price = db.Column(db.Float)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# ── Public Routes ────────────────────────
@app.route('/')
def index():
    sliders = Slider.query.order_by(Slider.order_num).all()
    categories = Category.query.order_by(Category.order_num).all()
    recent_products = Product.query.order_by(Product.id.desc()).limit(8).all()
    return render_template('index.html', sliders=sliders, categories=categories, recent_products=recent_products)

@app.route('/category/<int:cat_id>')
def category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    products = Product.query.filter_by(category_id=cat_id).all()
    categories = Category.query.order_by(Category.order_num).all()
    return render_template('category.html', cat=cat, products=products, categories=categories)
@app.route('/product/<int:id>')

def product_detail(id):
    product = Product.query.get_or_404(id)
    related = Product.query.filter_by(category_id=product.category_id).filter(Product.id != id).limit(4).all()
    return render_template('product_detail.html', product=product, related=related)

# ── Admin Auth ───────────────────────────
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        admin = Admin.query.filter_by(email=request.form['email']).first()
        if admin and check_password_hash(admin.password, request.form['password']):
            login_user(admin)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

# ── Dashboard ────────────────────────────
@app.route('/admin/dashboard')
@login_required
def dashboard():
    return render_template('admin/dashboard.html',
        slider_count=Slider.query.count(),
        cat_count=Category.query.count(),
        prod_count=Product.query.count()
    )

# ── Sliders ──────────────────────────────
@app.route('/admin/sliders')
@login_required
def admin_sliders():
    return render_template('admin/sliders.html', sliders=Slider.query.all())

@app.route('/admin/sliders/add', methods=['GET', 'POST'])
@login_required
def add_slider():
    if request.method == 'POST':
        file = request.files.get('image')
        filename = secure_filename(file.filename)
        file.save(os.path.join('static/images', filename))
        db.session.add(Slider(image=f'images/{filename}', caption=request.form.get('caption'), order_num=int(request.form.get('order_num', 0))))
        db.session.commit()
        flash('Slider added!', 'success')
        return redirect(url_for('admin_sliders'))
    return render_template('admin/slider_form.html', slider=None)

@app.route('/admin/sliders/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_slider(id):
    slider = Slider.query.get_or_404(id)
    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join('static/images', filename))
            slider.image = f'images/{filename}'
        slider.caption = request.form.get('caption')
        slider.order_num = int(request.form.get('order_num', 0))
        db.session.commit()
        flash('Slider updated!', 'success')
        return redirect(url_for('admin_sliders'))
    return render_template('admin/slider_form.html', slider=slider)

@app.route('/admin/sliders/delete/<int:id>')
@login_required
def delete_slider(id):
    db.session.delete(Slider.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin_sliders'))

# ── Categories ───────────────────────────
@app.route('/admin/categories')
@login_required
def admin_categories():
    return render_template('admin/categories.html', cats=Category.query.all())

@app.route('/admin/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        db.session.add(Category(name=request.form['name'], order_num=int(request.form.get('order_num', 0))))
        db.session.commit()
        flash('Category added!', 'success')
        return redirect(url_for('admin_categories'))
    return render_template('admin/category_form.html', cat=None)

@app.route('/admin/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    cat = Category.query.get_or_404(id)
    if request.method == 'POST':
        cat.name = request.form['name']
        cat.order_num = int(request.form.get('order_num', 0))
        db.session.commit()
        flash('Category updated!', 'success')
        return redirect(url_for('admin_categories'))
    return render_template('admin/category_form.html', cat=cat)

@app.route('/admin/categories/delete/<int:id>')
@login_required
def delete_category(id):
    db.session.delete(Category.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin_categories'))

# ── Products ─────────────────────────────
@app.route('/admin/products')
@login_required
def admin_products():
    return render_template('admin/products.html', products=Product.query.order_by(Product.id.desc()).all())

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    categories = Category.query.all()
    if request.method == 'POST':
        file = request.files.get('image')
        filename = secure_filename(file.filename)
        file.save(os.path.join('static/images', filename))
        db.session.add(Product(
            name=request.form['name'],
            price=float(request.form['price']),
            description=request.form.get('description'),
            image=f'images/{filename}',
            category_id=int(request.form.get('category_id') or 0) or None
        ))
        db.session.commit()
        flash('Product added!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', product=None, categories=categories)

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    categories = Category.query.all()
    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join('static/images', filename))
            product.image = f'images/{filename}'
        product.name = request.form['name']
        product.price = float(request.form['price'])
        product.description = request.form.get('description')
        product.category_id = int(request.form.get('category_id') or 0) or None
        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', product=product, categories=categories)

@app.route('/admin/products/delete/<int:id>')
@login_required
def delete_product(id):
    db.session.delete(Product.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin_products'))

# ── Create admin user ────────────────────
def create_admin():
    with app.app_context():
        if not Admin.query.first():
            db.session.add(Admin(
                email='admin@ethnicwear.com',
                password=generate_password_hash('admin123')
            ))
            db.session.commit()
            print('Admin created: admin@ethnicwear.com / admin123')

if __name__ == '__main__':
    create_admin()
    app.run(debug=True)
 