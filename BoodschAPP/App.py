from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import mysql.connector
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database configuration
db_config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'boodschapp',
}
conn = mysql.connector.connect(**db_config)



#Home page
@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('home.html')
    else:
        return redirect(url_for('login'))
    
@app.route('/home')
def home():
    if 'user_id' in session:
        return render_template('home.html')
    else:
        return redirect(url_for('login'))

@app.route('/instellingen')
def instellingen():
    if 'user_id' in session:
        return render_template('instellingen.html')
    else:
        return redirect(url_for('login'))
    
@app.route('/mijnaccount')
def mijnaccount():
    if 'user_id' in session:
        return render_template('mijnaccount.html')
    else:
        return redirect(url_for('login'))
    
@app.route('/deelnemenaanfamilie', methods=['GET', 'POST'])
def deelnemenaanfamilie():
    if 'user_id' in session:
        pass
    else:
        return redirect(url_for('login'))

    if request.method == 'POST':
        invite_code = request.form.get('invite_code')
        print(invite_code)

        # Zoek naar de familie met de opgegeven uitnodigingscode
        cursor = conn.cursor(buffered=True, dictionary=True)
        cursor.execute("SELECT * FROM families WHERE fam_InviteCode = %s ", (str(invite_code),))
        family = cursor.fetchone()
        if family:
            cursor.execute("UPDATE users SET usr_FamID = %s WHERE usr_ID = %s", (family['fam_ID'], session['user_id']))
            cursor.close()
            conn.commit()
            session['user_famid'] = family['fam_ID']
            session['user_familyname'] = family['fam_Name']
            session['user_faminvitecode'] = family['fam_InviteCode']



       

            return redirect('/mijnaccount')  # Redirect naar de accountpagina of een andere gewenste pagina

    return render_template('deelnemenaanfamilie.html')


@app.route('/verlaatfamilie', methods=['GET'])
def verlaat_familie():
    if 'user_id' in session:
        user_id = session['user_id']

        # Controleer of de gebruiker een familie heeft
        if session['user_famid'] is not None:
            cursor = conn.cursor(buffered=True, dictionary=True)
            cursor.execute("UPDATE users SET usr_FamID = NULL WHERE usr_ID = %s", (user_id,))
            cursor.close()
            conn.commit()
            session.pop('user_famid', None)
            session.pop('user_familyname', None)

            # Hier kun je verdere verwerkingsstappen toevoegen, zoals het bijwerken van de database

            return redirect('/mijnaccount')  # Redirect naar de accountpagina of een andere gewenste pagina

    return redirect('/login')  # Redirect naar de inlogpagina als de gebruiker niet is ingelogd


@app.route('/maakfamilie', methods=['GET', 'POST'])
def maak_familie():
    if 'user_id' in session:
        user_id = session['user_id']
        family_name = request.form.get('family_name')

        if request.method == 'POST':
            # Maak een nieuwe familie en wijs een unieke ID toe
            # ...

            # Maak een unieke fam_InviteCode:
            code = str(uuid.uuid4())[:6]  # Haal de eerste 6 tekens van de UUID

            # Verwijder eventuele streepjes
            code = code.replace('-', '')
            cursor = conn.cursor(buffered=True, dictionary=True)
            cursor.execute("INSERT INTO families (fam_Name, fam_InviteCode) VALUES (%s, %s)", (family_name, code))

            cursor.execute("SELECT fam_ID FROM families WHERE fam_InviteCode = %s", (code,))
            family_id = cursor.fetchone()['fam_ID']
            cursor.execute("UPDATE users SET usr_FamID = %s WHERE usr_ID = %s", (family_id, user_id))
            
            # Voeg de familiegegevens toe aan de sessie (optioneel)
            session['user_famid'] = family_id
            session['user_familyname'] = family_name
            session['user_faminvitecode'] = code
            cursor.close()
            conn.commit()

            # Hier kun je verdere verwerkingsstappen toevoegen, zoals het bijwerken van de database
            return redirect('/mijnaccount')  # Redirect naar de accountpagina of een andere gewenste pagina

        return render_template('maakfamilie.html')

    return redirect('/login')  # Redirect naar de inlogpagina als de gebruiker niet is ingelogd

@app.route('/niet_in_familie', methods=['GET'])
def not_in_family():
    return render_template('niet_in_familie.html')



#LOGIN LOGICS
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        print(email, password)
        # Query the database to check if the user exists with the provided username and password
        cursor = conn.cursor(buffered=True, dictionary=True)
        cursor.execute("SELECT * FROM users WHERE usr_Email = %s AND usr_Password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        

        if user:
            # Store user information in the session
            session['user_id'] = user['usr_ID']
            session['user_email'] = user['usr_Email']
            session['user_firstname'] = user['usr_FirstName']
            session['user_lastname'] = user['usr_LastName']
            if user['usr_FamID'] is not None:
                session['user_famid'] = user['usr_FamID']
                cursor = conn.cursor(buffered=True, dictionary=True)
                cursor.execute("SELECT * FROM families WHERE fam_ID = %s", (user['usr_FamID'],))
                famid = cursor.fetchone()
                session['user_faminvitecode'] = famid['fam_InviteCode']
                session['user_familyname'] = famid['fam_Name']
                cursor.close()
            else:
                session['user_famid'] = None
            # Create a response object
            resp = make_response(redirect(url_for('home')))
            
            # Set a cookie with user information (e.g., user ID)
            resp.set_cookie('user_id', str(user['usr_ID']))
            resp.set_cookie('user_email', user['usr_Email'])
            resp.set_cookie('user_firstname', user['usr_FirstName'])
            resp.set_cookie('user_lastname', user['usr_LastName'])
            if user['usr_FamID'] is not None:
                resp.set_cookie('user_famid', str(user['usr_FamID']))
                cursor = conn.cursor(buffered=True, dictionary=True)
                cursor.execute("SELECT * FROM families WHERE fam_ID = %s", (user['usr_FamID'],))
                famid = cursor.fetchone()
                resp.set_cookie('user_faminvitecode', famid['fam_InviteCode'])
                resp.set_cookie('user_familyname', famid['fam_Name'])
                cursor.close()

            
            
            
            return resp  # Return the response object with the cookie

        else:
            flash('Login failed. Check your username and password.', 'danger')

    return render_template('login.html')

@app.route('/add_category', methods=['POST'])
def add_category():
    if 'user_famid' not in session:
        return redirect('/login')  # Stuur gebruiker naar de loginpagina als er geen familie-ID in de sessie is

    new_category = request.form.get('new_category')

    if new_category:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories (cat_Name, cat_FamID) VALUES (%s, %s)", (new_category, session['user_famid']))
        conn.commit()
        cursor.close()

    return redirect('/lijstjeinstellingen')

@app.route('/lijstjeinstellingen', methods=['GET'])
def lijstjeinstellingen():
    if session.get('user_famid') is None:
        return redirect('/login')
    else:
        return render_template('lijstjeinstellingen.html')

@app.route('/remove_category', methods=['POST'])
def remove_category():
    if 'user_famid' not in session:
        return redirect('/login')  # Stuur gebruiker naar de loginpagina als er geen familie-ID in de sessie is

    category_to_remove = request.form.get('category_to_remove')

    if category_to_remove:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE cat_Name = %s AND cat_FamID = %s", (category_to_remove, session['user_famid']))
        conn.commit()
        cursor.close()

    return redirect('/lijstjeinstellingen')

@app.route('/mijnlijstje', methods=['GET'])
def mijnlijstje():
    if session.get('user_famid') is None:
        return redirect('/niet_in_familie')  # Redirect to the warning page
    else:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE prod_FamID = %s", (session['user_famid'],))
        products = cursor.fetchall()
        cursor.close()
        return render_template('mijnlijstje.html', products=products)


@app.route('/add_item', methods=['POST'])
def add_item():
    if 'user_famid' not in session:
        return redirect('/login')  # Stuur gebruiker naar de loginpagina als er geen familie-ID in de sessie is

    new_item = request.form.get('new_item')
    new_category = request.form.get('new_item_category')


    if new_item and new_category:
        # Get the category ID
        cursor = conn.cursor(buffered=True, dictionary=True)
        cursor.execute("SELECT * FROM categories WHERE cat_Name = %s AND cat_FamID = %s", (new_category, session['user_famid']))
        category = cursor.fetchone()
        print(category['cat_ID'])
        cursor.close()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (prod_Name, prod_FamID, prod_CatID) VALUES (%s, %s, %s)", (new_item, session['user_famid'], category['cat_ID']))
        conn.commit()
        cursor.close()

    return redirect('/mijnlijstje')

@app.route('/remove_item/<int:item_id>', methods=['GET'])
def remove_item(item_id):
    if 'user_famid' not in session:
        return redirect('/login')  # Stuur gebruiker naar de loginpagina als er geen familie-ID in de sessie is

    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE prod_ID = %s", (item_id,))
    conn.commit()
    cursor.close()

    return redirect('/mijnlijstje')

@app.route('/get_categories', methods=['GET'])
def get_categories():
    if 'user_famid' not in session:
        return jsonify({'categories': []})  # Geef een lege lijst terug als de gebruiker niet is ingelogd

    cursor = conn.cursor()
    cursor.execute("SELECT cat_Name FROM categories WHERE cat_FamID = %s", (session['user_famid'],))
    categories = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return jsonify({'categories': categories})

@app.route('/get_products_by_category/<category>', methods=['GET'])
def get_products_by_category(category):
    if 'user_famid' not in session:
        return jsonify({'products': []})  # Geef een lege lijst terug als de gebruiker niet is ingelogd

    cursor = conn.cursor(dictionary=True)
    print(category)
    print(session['user_famid'])
    cursor.execute("SELECT * FROM categories WHERE cat_Name = %s AND cat_FamID = %s", (category, session['user_famid']))
    result = cursor.fetchone()
    print(result)

    if result:
        category_id = result['cat_ID']
        cursor.execute("SELECT * FROM products WHERE prod_FamID = %s AND prod_CatID = %s", (session['user_famid'], category_id))
        products = cursor.fetchall()
    else:
        products = []

    cursor.close()
    return jsonify({'products': products})


@app.route('/loguit', methods=['GET'])
def loguit():
    return render_template('loguit.html')

@app.route('/logout')
def logout():
    # Clear the user's session
    session.pop('user_id', None)
    session.pop('user_firstname', None)
    session.pop('user_lastname', None)
    session.pop('user_email', None)
    session.pop('user_famid', None)
    session.pop('user_familyname', None)
    session.pop('user_faminvitecode', None)
    
    # Create a response object
    resp = make_response(redirect(url_for('login')))
    
    # Remove the 'user_id' cookie
    resp.delete_cookie('user_id')
    resp.delete_cookie('user_email')
    resp.delete_cookie('user_firstname')
    resp.delete_cookie('user_lastname')
    resp.delete_cookie('user_famid')
    resp.delete_cookie('user_familyname')
    


    
    flash('Logged out successfully!', 'success')
    return resp  # Return the response object with the removed cookie


if __name__ == '__main__':
    app.run(debug=True)
