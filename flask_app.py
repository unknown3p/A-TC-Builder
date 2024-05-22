import os
import io
from flask import Flask, request, render_template, session, flash, redirect, url_for,Response
import mysql.connector
from flask_session import Session
from sdmail import sendmail
from tokenreset import token
from key import secret_key, salt, salt2
from itsdangerous import URLSafeTimedSerializer
import stripe
from flask_weasyprint import HTML, render_pdf
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
stripe.api_key = 'sk_test_51MzcVYSDVehZUuDTkwGUYe8hWu2LGN0krI8iO5QOAEqoRYXx3jgRVgkY7WzXqQmpN62oMWM59ii76NKPrRzg3Gtr005oVpiW82'
app = Flask(__name__)
secret_key=secret_key
app.config['SESSION_TYPE'] = 'filesystem'
mydb= mysql.connector.connect(user='root', password='Venky@1437',host='localhost',database='tc')
Session(app)
# mysql=MySQL(app)

@app.route('/')
def index():
    cursor = mydb.cursor(buffered=True)
    cursor.execute('SELECT notication FROM notifications')
    data = cursor.fetchall()
    cursor.close()
    return render_template('index.html',data=data)
@app.route('/user',methods=['GET','POST'])
def user():
    if request.method=='POST':
        first=request.form['first']
        last=request.form['last']
        username=request.form['username']
        emailid=request.form['email']
        phno=request.form['phno']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from user where username=%s',[username])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from user where email=%s',[emailid])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('username already in use')
            return render_template('register.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('register.html')
        data={'first':first,'last':last,'username':username,'emailid':emailid,'phno':phno,'password':password}
        subject='Email Confirmation'
        body=f"Thanks for signing up\n\nfollow this link for further steps-{url_for('confirm',token=token(data,salt),_external=True)}"
        sendmail(to=emailid,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('userlogin'))
    return render_template('register.html')
@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception as e:
        #print(e)
        return 'Link Expired register again'
    else:
        cursor=mydb.cursor(buffered=True)
        name=data['username']
        cursor.execute('select count(*) from user where username=%s',[name])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('userlogin'))
        else:
            cursor.execute('insert into user(first,last,username,email,phno,password )values(%s,%s,%s,%s,%s,%s)',[data['first'],data['last'],data['username'],data['emailid'],data['phno'],data['password']])
            mydb.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('userlogin'))
@app.route('/userlogin',methods=['GET','POST'])
def userlogin():
    if request.method=='POST':
        print(request.form)
        email=request.form['email']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('SELECT count(*) from user where email=%s and password=%s',[email,password])
        count=cursor.fetchone()[0]
        cursor.close()
        if count == 1:
            session['user'] = email
            return redirect(url_for('userpanel'))

        else:
            flash('Invalid username or password')
            return render_template('userlogin.html')
    return render_template('userlogin.html')
@app.route('/adminlogout')
def adminlogout():
    return redirect(url_for('adminlogin'))
@app.route('/adminlogin',methods=['GET','POST'])
def adminlogin():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']

        hardcoded_username = "admin"
        hardcoded_password = "admin"

        if username == hardcoded_username and password == hardcoded_password:
            return render_template('adminpannel.html')
        else:
            print("Login failed. Please check your credentials.")
    return render_template('adminlogin.html')
@app.route('/adminpannel')
def adminpannel():
    return render_template('adminpannel.html')
    

@app.route('/userpanel')
def userpanel():
    return render_template('userpanel.html')
# @app.route('/dashboard')
# def dashboard():
#     cursor=mydb.cursor(buffered=True)
#     cursor.execute('select * from user')
#     new=cursor.fetchall()
#     cursor.close()
#     return render_template('dashboard.html',new=new)

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user')

    if user_id:
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT * FROM user WHERE email = %s', (user_id,))
        new = cursor.fetchone()
        cursor.close()
        return render_template('dashboard.html', new=new)

    return redirect(url_for('userlogin'))

@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    if 'user' in session:
        user_id = session['user']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT * FROM user WHERE email = %s', [user_id])
        data = cursor.fetchone()
        cursor.close()
        print(data)

        if request.method == 'POST':
            first = request.form['first']
            last = request.form['last']
            username = request.form['username']
            emailid = request.form['email']
            phno = request.form['phno']
            password = request.form['password']

            cursor = mydb.cursor(buffered=True)
            cursor.execute('UPDATE user SET first=%s,last=%s,username=%s, email=%s, phno=%s, password=%s WHERE email=%s', [first,last,username, emailid, phno, password,user_id])
            mydb.commit()
            cursor.close()

            flash('Information updated successfully.')
            return redirect(url_for('dashboard'))

        return render_template('edit.html', data=data)
    else:
        flash('Please log in to edit your information.')
        return redirect(url_for('userlogin'))
@app.route('/userlogout')
def userlogout():
    if session.get('user'):
        session.pop('user')
        flash('Successfully logged out')
        return redirect(url_for('userlogin'))
    else:
        return redirect(url_for('userlogin'))


@app.route('/submit_documents')
def submit_documents():
    return render_template('submit_documents.html')
@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file1 = request.files['file1']
        file2 = request.files['file2']

        if file1 and file2:
            # Ensure that the static folder exists
            static_folder = os.path.join(app.root_path, 'static')
            if not os.path.exists(static_folder):
                os.makedirs(static_folder)

            # Save the files to the static folder
            file1.save(os.path.join(static_folder, file1.filename))
            file2.save(os.path.join(static_folder, file2.filename))

            user_email = session.get('user')

            if user_email:
                cursor = mydb.cursor(buffered=True)
                cursor.execute(
                    'INSERT INTO uploaded_files (file1_name, file2_name, email) VALUES (%s, %s, %s)',
                    (file1.filename, file2.filename, user_email)
                )
                mydb.commit()
                cursor.close()

                flash('Files uploaded and associated with your account successfully.', 'success')  # 'success' is the message category
            else:
                flash('User session not found. Please log in.', 'danger')  # 'danger' for error message
        else:
            flash('Please provide both files.', 'danger')  # 'danger' for error message
    return redirect(url_for('make_payment'))

@app.route('/make_payment')
def make_payment():
    if session.get('user'):
        user_email = session.get('user')
        amount = 100

        checkout_session = stripe.checkout.Session.create(
            success_url=url_for('success_payment', _external=True),
            cancel_url=url_for('cancel_payment', _external=True),
            payment_method_types=['card'],
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': 'Transfer Certificate',
                    },
                    'unit_amount': amount*100,
                },
                'quantity': 1,
            }],
            customer_email=user_email,
        )

        return redirect(checkout_session.url)

    else:
        return redirect(url_for('userlogin'))

@app.route('/success_payment')
def success_payment():

    if session.get('user'):
        user_email = session.get('user')
        cursor = mydb.cursor(buffered=True)
        cursor.execute('UPDATE user SET paid_certificate = "paid" WHERE email = %s', [user_email])
        mydb.commit()
        cursor.close()

        flash('Payment successful. You can now process the certificate.')
        return redirect(url_for('apply_download_tc'))

    return 'Payment successful.'

@app.route('/cancel_payment')
def cancel_payment():
    return 'Payment canceled.'


@app.route('/apply_download_tc', methods=['GET', 'POST'])
def apply_download_tc():
    if 'user' in session:
        emailid = session['user']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT approval_status FROM approval_status WHERE user_email=%s', [emailid])
        result = cursor.fetchone()

        if result is not None:
            approval_status = result[0]

            if approval_status == "Approved":
                if request.method == 'POST':
                    name = request.form['name']
                    gender = request.form['gender']
                    father = request.form['father']
                    mother = request.form['mother']
                    dob = request.form['dob']
                    nationality = request.form['nationality']
                    belong = request.form['belong']
                    admission = request.form['admission']
                    classes = request.form['classes']
                    froms = request.form['froms']
                    tos = request.form['tos']
                    studies = request.form['studies']
                    dues = request.form['dues']
                    gc = request.form['gc']
                    certificate = request.form['certificate']
                    reason = request.form['reason']
                    remarks = request.form['remarks']
                    email = request.form['email']
                    cursor = mydb.cursor(buffered=True)
                    cursor.execute('INSERT INTO student_info (name, gender, father, mother, dob, nationality, belong, admission, classes, froms, tos, studies, dues, gc, certificate, reason, remarks,email) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(name, gender, father, mother, dob, nationality, belong, admission, classes, froms, tos,studies, dues, gc, certificate, reason, remarks,email))
                    mydb.commit()
                    cursor.close()
                    return redirect(url_for('download'))
                else:
                    return render_template('apply_download_tc.html')

            elif approval_status == "Not approved":
                flash( "sorry your details is rejected.")
                return redirect(url_for('userpanel'))

        else:
            flash( "Wait for your details to be processed.")
            return redirect(url_for('userpanel'))

    else:
        flash( "Please log in to access this page.")
        return redirect(url_for('userpanel'))


@app.route('/download')
def download():
    if session.get('user'):
        user_email = session.get('user')
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT * FROM student_info WHERE email = %s', [user_email])
        user_data = cursor.fetchone()
        cursor.close()
        if user_data:
            html = render_template('download.html', new=user_data)
            return render_pdf(HTML(string=html))
        else:
            return 'No user data found for download.'
    return 'Please login to access this page.'


# @app.route('/allusers')
# def allusers():
#     cursor = mydb.cursor(buffered=True)
#     cursor.execute('SELECT u.first, u.last, u.email,u.paid_certificate,uf.file1_name, uf.file2_name FROM user AS u INNER JOIN uploaded_files AS uf ON u.email = uf.email')
#     new = cursor.fetchall()
#     cursor.close()
#     return render_template('allusers.html', new=new)
@app.route('/allusers')
def allusers():
    cursor = mydb.cursor(buffered=True)
    cursor.execute('SELECT u.first, u.last, u.email, u.paid_certificate, uf.file1_name, uf.file2_name, a.approval_status FROM user AS u INNER JOIN uploaded_files AS uf ON u.email = uf.email LEFT JOIN approval_status AS a ON u.email = a.user_email')
    new = cursor.fetchall()
    cursor.close()
    return render_template('allusers.html', new=new)



@app.route('/approve/<emailid>', methods=['POST'])
def approve(emailid):
    cursor = mydb.cursor(buffered=True)
    cursor.execute('SELECT * FROM approval_status WHERE user_email=%s', [emailid])
    result = cursor.fetchone()


    if result is not None:
        current_approval = result[1]
        new_approval = "Approved" if current_approval == "Not approved" else "Not approved"

        cursor.execute('UPDATE approval_status SET approval_status=%s WHERE user_email=%s', (new_approval, emailid))
    else:
        cursor.execute('INSERT INTO approval_status (user_email, approval_status) VALUES (%s, %s)', (emailid, "Approved"))
    mydb.commit()
    cursor.close()
    flash( "Successfully upadated")
    return redirect(url_for('allusers'))

@app.route('/forgetpassword',methods=['GET','POST'])
def forget():
    if request.method=='POST':
        email=request.form['id']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email from user')
        data=cursor.fetchall()
        if (email,) in data:
            cursor.execute('select email from user where email=%s',[email])
            data=cursor.fetchone()[0]
            cursor.close()
            session['pass']=email
            sendmail(data,subject='Reset password',body=f'Reset the password here -{request.host+url_for("createpassword")}')
            flash('reset link sent to your mail')
            return redirect(url_for('userlogin'))
        else:
            return 'Invalid user id'
    return render_template('forgot.html')
@app.route('/createpassword',methods=['GET','POST'])
def createpassword():
    if request.method=='POST':
        oldp=request.form['npassword']
        newp=request.form['cpassword']
        if oldp==newp:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update user set password=%s where email=%s',[newp,session.get('pass')])
            mydb.commit()
            flash('Password changed successfully')
            return redirect(url_for('userlogin'))
        else:
            flash('New password and confirm passwords should be same')
            return render_template('newpassword.html')
    return render_template('newpassword.html')


@app.route('/notifications', methods=['GET', 'POST'])
def notifications():
    if request.method == 'POST':
        notification = request.form['text']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('INSERT INTO notifications (notication) VALUES (%s)', (notification,))
        mydb.commit()
        cursor.close()
        return redirect(url_for('display'))

    return render_template('notifications.html')
@app.route('/display', methods=['GET', 'POST'])
def display():
    cursor = mydb.cursor(buffered=True)
    cursor.execute('SELECT * FROM notifications')
    new = cursor.fetchall()
    cursor.close()
    return render_template('display.html', new=new)

@app.route('/notficationupdate/<int:id>', methods=['GET', 'POST'])
def notficationupdate(id):
    cursor = mydb.cursor(buffered=True)
    cursor.execute('SELECT * FROM notifications WHERE id = %s', [id])
    data = cursor.fetchone()
    #print(data)
    cursor.close()

    if request.method == 'POST':
        #print('hi')
        notification = request.form['notification']
        id=request.form['id']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('UPDATE notifications SET notication = %s WHERE id = %s', [notification, id])
        mydb.commit()
        cursor.close()
        flash('Updated successfully')
        return redirect(url_for('display'))
    return render_template('notify.html', data=data)
@app.route('/notficationdelete/<int:id>', methods=['GET', 'POST'])
def notficationdelete(id):
    cursor = mydb.cursor(buffered=True)
    cursor.execute('SELECT * FROM notifications WHERE id = %s', [id])
    data = cursor.fetchone()
    cursor.close()

    if request.method == 'POST':
        notification = request.form['notification']
        id=request.form['id']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('DELETE FROM notifications WHERE id = %s', [id])
        mydb.commit()
        cursor.close()
        flash('Updated successfully')
        return redirect(url_for('display'))
    return render_template('notify.html', data=data)

@app.route('/generate-invoice/<email>', methods=['POST'])
def generate_invoice(email):
    # Fetch user information from the database based on the provided email
    cursor = mydb.cursor(buffered=True)
    cursor.execute('SELECT first, last, username, email, phno, paid_certificate FROM user WHERE email = %s', [email])
    user_info = cursor.fetchone()
    cursor.close()

    if user_info:
        # Check if the user's paid_certificate status is "paid"
        if user_info[5] == "paid":
            # Create a PDF invoice using ReportLab
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)

            # Populate the invoice content with user information
            p.drawString(100, 750, f"Name: {user_info[0]} {user_info[1]}")
            p.drawString(100, 720, f"Username: {user_info[2]}")
            p.drawString(100, 690, f"Email: {user_info[3]}")
            p.drawString(100, 660, f"Phone Number: {user_info[4]}")
            p.drawString(100, 630, f"Status: {user_info[5]}")  # Adjusted y-coordinate

            # Add more invoice content as needed

            p.showPage()
            p.save()

            # Get the PDF content from the buffer
            buffer.seek(0)
            invoice_content = buffer.read()
            buffer.close()

            # Return the PDF as a response with the correct content type
            response = Response(invoice_content, content_type='application/pdf')
            response.headers['Content-Disposition'] = 'inline; filename=invoice.pdf'
            return response
        else:
            flash("User's is not 'paid'.")
            return redirect(url_for('allusers'))
    else:
        flash("User not found.")
        return redirect(url_for('allusers'))

if __name__ == '__main__':
    app.run(debug=True)





