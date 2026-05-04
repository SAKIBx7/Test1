from flask import request, jsonify, current_app
from models import db, Admin, Opportunity
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer


def register_routes(app):

    # -------------------- BASIC CHECK --------------------
    @app.route('/')
    def home():
        return jsonify({"message": "Backend is running"})


    # -------------------- SIGNUP --------------------
    @app.route('/api/signup', methods=['POST'])
    def signup():
        data = request.get_json()

        full_name = data.get('full_name')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if not all([full_name, email, password, confirm_password]):
            return jsonify({"error": "All fields are required"}), 400

        if password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400

        if Admin.query.filter_by(email=email).first():
            return jsonify({"error": "Account already exists"}), 400

        hashed_password = generate_password_hash(password)

        new_user = Admin(
            full_name=full_name,
            email=email,
            password_hash=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "Signup successful"}), 201


    # -------------------- LOGIN --------------------
    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()

        email = data.get('email')
        password = data.get('password')
        remember = data.get('remember', False)

        user = Admin.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid email or password"}), 401

        login_user(user, remember=remember)

        return jsonify({"message": "Login successful"}), 200


    # -------------------- FORGOT PASSWORD --------------------
    @app.route('/api/forgot-password', methods=['POST'])
    def forgot_password():
        data = request.get_json()
        email = data.get('email')

        response = {"message": "If email exists, reset link sent"}

        user = Admin.query.filter_by(email=email).first()

        if user:
            serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = serializer.dumps(email, salt='password-reset')

            reset_link = f"http://127.0.0.1:5000/reset/{token}"
            print("🔗 Reset Link:", reset_link)

        return jsonify(response), 200


    # -------------------- RESET TOKEN CHECK --------------------
    @app.route('/reset/<token>', methods=['GET'])
    def reset_token(token):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

        try:
            email = serializer.loads(token, salt='password-reset', max_age=3600)
            return jsonify({"message": "Token valid", "email": email})
        except:
            return jsonify({"error": "Token expired or invalid"}), 400


    # -------------------- RESET PASSWORD (NEW ADD) --------------------
    @app.route('/api/reset-password', methods=['POST'])
    def reset_password():
        data = request.get_json()

        token = data.get('token')
        new_password = data.get('new_password')

        if not token or not new_password:
            return jsonify({"error": "Token and new password required"}), 400

        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

        try:
            email = serializer.loads(token, salt='password-reset', max_age=3600)
        except:
            return jsonify({"error": "Invalid or expired token"}), 400

        user = Admin.query.filter_by(email=email).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        user.password_hash = generate_password_hash(new_password)
        db.session.commit()

        return jsonify({"message": "Password reset successful"}), 200


    # -------------------- GET ALL OPPORTUNITIES --------------------
    @app.route('/api/opportunities', methods=['GET'])
    @login_required
    def get_opportunities():
        user_ops = Opportunity.query.filter_by(admin_id=current_user.id).all()

        result = []
        for op in user_ops:
            result.append({
                "id": op.id,
                "title": op.title,
                "category": op.category,
                "duration": op.duration,
                "start_date": op.start_date,
                "description": op.description
            })

        return jsonify(result), 200


    # -------------------- ADD OPPORTUNITY --------------------
    @app.route('/api/opportunities', methods=['POST'])
    @login_required
    def add_opportunity():
        data = request.get_json()

        required_fields = [
            "title", "duration", "start_date",
            "description", "skills", "category", "future_opportunities"
        ]

        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        new_op = Opportunity(
            title=data.get('title'),
            duration=data.get('duration'),
            start_date=data.get('start_date'),
            description=data.get('description'),
            skills=data.get('skills'),
            category=data.get('category'),
            future_opportunities=data.get('future_opportunities'),
            max_applicants=data.get('max_applicants'),
            admin_id=current_user.id
        )

        db.session.add(new_op)
        db.session.commit()

        return jsonify({"message": "Opportunity created"}), 201


    # -------------------- VIEW SINGLE --------------------
    @app.route('/api/opportunities/<int:id>', methods=['GET'])
    @login_required
    def get_single_opportunity(id):
        op = Opportunity.query.filter_by(id=id, admin_id=current_user.id).first()

        if not op:
            return jsonify({"error": "Not found"}), 404

        return jsonify({
            "id": op.id,
            "title": op.title,
            "duration": op.duration,
            "start_date": op.start_date,
            "description": op.description,
            "skills": op.skills,
            "category": op.category,
            "future_opportunities": op.future_opportunities,
            "max_applicants": op.max_applicants
        })


    # -------------------- EDIT --------------------
    @app.route('/api/opportunities/<int:id>', methods=['PUT'])
    @login_required
    def edit_opportunity(id):
        op = Opportunity.query.filter_by(id=id, admin_id=current_user.id).first()

        if not op:
            return jsonify({"error": "Not found"}), 404

        data = request.get_json()

        op.title = data.get('title', op.title)
        op.duration = data.get('duration', op.duration)
        op.start_date = data.get('start_date', op.start_date)
        op.description = data.get('description', op.description)
        op.skills = data.get('skills', op.skills)
        op.category = data.get('category', op.category)
        op.future_opportunities = data.get('future_opportunities', op.future_opportunities)
        op.max_applicants = data.get('max_applicants', op.max_applicants)

        db.session.commit()

        return jsonify({"message": "Updated successfully"})


    # -------------------- DELETE --------------------
    @app.route('/api/opportunities/<int:id>', methods=['DELETE'])
    @login_required
    def delete_opportunity(id):
        op = Opportunity.query.filter_by(id=id, admin_id=current_user.id).first()

        if not op:
            return jsonify({"error": "Not found"}), 404

        db.session.delete(op)
        db.session.commit()

        return jsonify({"message": "Deleted successfully"})
    