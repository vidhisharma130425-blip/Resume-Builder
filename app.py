from weasyprint import HTML
from flask import Flask, render_template, request , redirect , session , url_for
from werkzeug.security import generate_password_hash , check_password_hash
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "sabkijoblagegi_secret_key"

try:
    import os

    db = mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT"))
    )

    print("Database Connected Successfully!")

except Exception as e:
    print("Database Connection Error:")
    print(e)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/signin", methods=["GET", "POST"])
def signin():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect("/dashboard")
        
        else:
            return render_template(
                "signin.html",
                error="Invalid email or password"
            )

    return render_template("signin.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(
            request.form["password"]
        )

        cursor = db.cursor()

        query = """
        INSERT INTO users(name, email, password)
        VALUES(%s, %s, %s)
        """

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            return render_template(
                "signup.html",
                error="*Email already registered!"
            )

        cursor.execute(
            query,
            (name, email, password)
        )

        db.commit()

        cursor.close()

        return redirect("/signin")

        print("User Saved Successfully!")

    return render_template("signup.html")

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/signin")

    cursor = db.cursor()

    cursor.execute(
    """
    SELECT id, resume_name
    FROM resumes
    WHERE user_id=%s
    ORDER BY created_at DESC
    """,
    (session["user_id"],)
    )


    resumes = cursor.fetchall()

    return render_template(
        "dashboard.html",
        resumes=resumes
    )

@app.route("/choose_template")
def choose_template():

    if "user_id" not in session:
        return redirect("/signin")

    return render_template("choose_template.html")

@app.route("/template/<int:template_id>")
def select_template(template_id):

    if "user_id" not in session:
        return redirect("/signin")

    session["selected_template"] = template_id

    return redirect("/resume")

@app.route("/resume")
def resume():

    if "user_id" not in session:
        return redirect("/signin")

    template = session.get("selected_template", 1)

    return render_template(
        "index.html",
        template=template
    )

@app.route("/generate_resume", methods=["POST"])
def generate_resume():

    if "user_id" not in session:
        return redirect("/signin")

    template = session.get("selected_template", 1)

    form = request.form

    session["resume_data"] = {
        "name": form.get("name"),
        "email": form.get("email"),
        "phone": form.get("phone"),
        "linkedin": form.get("linkedin"),
        "degree": form.get("degree"),
        "college": form.get("college"),
        "cgpa": form.get("cgpa"),
        "summary": form.get("summary"),
        "skills": form.get("skills"),
        "projects": form.get("projects"),
        "certifications": form.get("certifications"),
        "achievements": form.get("achievements"),
        "languages": form.get("languages"),
        "interests": form.get("interests"),
        "template": template
    }

    if template == 1:
        return render_template(
            "template1.html",
            data=form
        )

    elif template == 2:
        return render_template(
            "template2.html",
            data=form
        )

    elif template == 3:
        return render_template(
            "template3.html",
            data=form
        )

    else:
        return render_template(
            "template4.html",
            data=form
        )

@app.route("/save_resume")
def save_resume():

    if "user_id" not in session:
        return redirect("/signin")

    data = session.get("resume_data")

    if not data:
        return "No resume data found."

    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO resumes(

            user_id,
            resume_name,
            full_name,
            email,
            phone,
            linkedin,
            degree,
            college,
            cgpa,
            summary,
            skills,
            projects,
            certifications,
            achievements,
            languages,
            interests,
            template

        )
        VALUES(
            %s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s
            ) 
        """,
        (

            session["user_id"],

            request.args.get("resume_name"),

            data["name"],

            data["email"],

            data["phone"],

            data["linkedin"],

            data["degree"],

            data["college"],

            data["cgpa"],

            data["summary"],

            data["skills"],

            data["projects"],

            data["certifications"],

            data["achievements"],

            data["languages"],

            data["interests"],

            data["template"]

        )
    )

    db.commit()

    cursor.close()

    return redirect("/dashboard")

@app.route("/resume/<int:resume_id>")
def open_resume(resume_id):

    print("Resume ID:", resume_id)
    print("Logged in User ID:", session["user_id"])

    if "user_id" not in session:
        return redirect("/signin")

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT *
        FROM resumes
        WHERE id=%s
        AND user_id=%s
    """,
    (
        resume_id,
        session["user_id"]
    ))

    resume = cursor.fetchone()

    resume["name"] = resume["full_name"]

    print("Resume Data:", resume)

    cursor.close()

    if not resume:
        return "Resume not found."

    return render_template(
        f"template{resume['template']}.html",
        data=resume
    )

@app.route("/download_resume/<int:resume_id>")
def download_resume(resume_id):

    if "user_id" not in session:
        return redirect("/signin")

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM resumes
        WHERE id=%s
        AND user_id=%s
        """,
        (
            resume_id,
            session["user_id"]
        )
    )

    resume = cursor.fetchone()

    print(resume)

    cursor.close()

    if not resume:
        return "Resume not found."

    resume["name"] = resume["full_name"]

    html = render_template(
        f"template{resume['template']}.html",
        data=resume,
        pdf=True
    )

    pdf = HTML(string=html).write_pdf()

    return app.response_class(
        pdf,
        mimetype="application/pdf",
        headers={
            "Content-Disposition":
            f'attachment; filename="{resume["resume_name"]}.pdf"'
        }
    )

@app.route("/delete_resume/<int:resume_id>")
def delete_resume(resume_id):


    if "user_id" not in session:
        return redirect("/signin")

    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM resumes
        WHERE id=%s
        AND user_id=%s
        """,
        (
            resume_id,
            session["user_id"]
        )
    )

    db.commit()

    cursor.close()

    return redirect("/dashboard")




@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)