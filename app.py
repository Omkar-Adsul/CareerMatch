from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config


app = Flask(__name__)
app.config.from_object(Config)


# -------------------------------------------------
# DATABASE CONNECTION
# -------------------------------------------------

def get_db_connection():
    return psycopg2.connect(
        host=app.config["DB_HOST"],
        port=app.config["DB_PORT"],
        database=app.config["DB_NAME"],
        user=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"]
    )


# -------------------------------------------------
# HOME PAGE
# -------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -------------------------------------------------
# REGISTER
# -------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not full_name or not email or not password:
            flash("Please fill all fields.", "danger")
            return redirect(url_for("register"))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            conn.close()

            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (%s, %s, %s, 'user')
            RETURNING id
            """,
            (full_name, email, password_hash)
        )

        user_id = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO user_profiles (user_id)
            VALUES (%s)
            """,
            (user_id,)
        )

        conn.commit()

        cursor.close()
        conn.close()

        flash("Registration successful. Please login.", "success")

        return redirect(url_for("login"))

    return render_template("register.html")


# -------------------------------------------------
# LOGIN
# -------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, full_name, email, password_hash, role
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user[3], password):

            session["user_id"] = user[0]
            session["full_name"] = user[1]
            session["email"] = user[2]
            session["role"] = user[4]

            flash("Login successful.", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            u.full_name,
            u.email,
            p.education,
            p.degree,
            p.graduation_year,
            p.experience,
            p.preferred_role,
            p.preferred_location,
            p.bio
        FROM users u
        LEFT JOIN user_profiles p
            ON u.id = p.user_id
        WHERE u.id = %s
        """,
        (session["user_id"],)
    )

    profile = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        profile=profile
    )


# -------------------------------------------------
# PROFILE
# -------------------------------------------------

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # ---------------------------------------------
    # SAVE PROFILE
    # ---------------------------------------------

    if request.method == "POST":

        education = request.form.get("education", "").strip()
        degree = request.form.get("degree", "").strip()
        graduation_year = request.form.get("graduation_year", "").strip()
        experience = request.form.get("experience", "").strip()
        preferred_role = request.form.get("preferred_role", "").strip()
        preferred_location = request.form.get("preferred_location", "").strip()
        bio = request.form.get("bio", "").strip()

        if graduation_year:
            try:
                graduation_year = int(graduation_year)
            except ValueError:
                flash("Graduation year must be a number.", "danger")
                cursor.close()
                conn.close()
                return redirect(url_for("profile"))
        else:
            graduation_year = None

        if experience:
            try:
                experience = float(experience)
            except ValueError:
                flash("Experience must be a number.", "danger")
                cursor.close()
                conn.close()
                return redirect(url_for("profile"))
        else:
            experience = None

        cursor.execute(
            """
            UPDATE user_profiles
            SET
                education = %s,
                degree = %s,
                graduation_year = %s,
                experience = %s,
                preferred_role = %s,
                preferred_location = %s,
                bio = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
            """,
            (
                education,
                degree,
                graduation_year,
                experience,
                preferred_role,
                preferred_location,
                bio,
                user_id
            )
        )

        conn.commit()

        # -----------------------------------------
        # SAVE SKILLS
        # -----------------------------------------

        selected_skills = request.form.getlist("skills")

        cursor.execute(
            """
            DELETE FROM user_skills
            WHERE user_id = %s
            """,
            (user_id,)
        )

        for skill_id in selected_skills:

            try:
                skill_id = int(skill_id)

                cursor.execute(
                    """
                    INSERT INTO user_skills (user_id, skill_id)
                    VALUES (%s, %s)
                    """,
                    (user_id, skill_id)
                )

            except ValueError:
                continue

        conn.commit()

        flash("Profile updated successfully.", "success")

        cursor.close()
        conn.close()

        return redirect(url_for("profile"))

    # ---------------------------------------------
    # GET PROFILE
    # ---------------------------------------------

    cursor.execute(
        """
        SELECT
            education,
            degree,
            graduation_year,
            experience,
            preferred_role,
            preferred_location,
            bio
        FROM user_profiles
        WHERE user_id = %s
        """,
        (user_id,)
    )

    profile_data = cursor.fetchone()

    # ---------------------------------------------
    # GET ALL SKILLS
    # ---------------------------------------------

    cursor.execute(
        """
        SELECT id, name
        FROM skills
        ORDER BY name
        """
    )

    skills = cursor.fetchall()

    # ---------------------------------------------
    # GET USER'S SELECTED SKILLS
    # ---------------------------------------------

    cursor.execute(
        """
        SELECT skill_id
        FROM user_skills
        WHERE user_id = %s
        """,
        (user_id,)
    )

    selected_skill_rows = cursor.fetchall()

    selected_skills = [
        row[0]
        for row in selected_skill_rows
    ]

    cursor.close()
    conn.close()

    return render_template(
        "profile.html",
        profile=profile_data,
        skills=skills,
        selected_skills=selected_skills
    )


# -------------------------------------------------
# LOGOUT
# -------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("home"))


# -------------------------------------------------
# DATABASE TEST
# -------------------------------------------------

@app.route("/test-db")
def test_db():

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT version();")

        version = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return f"""
        <h2>CareerMatch Database Connected</h2>
        <p>{version}</p>
        """

    except Exception as e:

        return f"""
        <h2>Database Connection Failed</h2>
        <p>{e}</p>
        """


# -------------------------------------------------
# RUN APPLICATION
# -------------------------------------------------

if __name__ == "__main__":

    print("CareerMatch Starting...")

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT version();")

        version = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        print("CareerMatch Database Connected")
        print("PostgreSQL:")
        print(version)

    except Exception as e:

        print("Database Connection Failed")
        print(e)

    print("Open in browser:")
    print("http://127.0.0.1:5000")

    app.run(debug=True)