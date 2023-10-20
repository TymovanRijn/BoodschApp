from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session, make_response
from flask_bcrypt import Bcrypt
import regex as re
import mysql.connector
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt()

# Database configuration
db_config = {
    'user': 'root',
    'password': 'rootroot',
    'host': 'localhost',
    'database': 'boodschapp',
}
conn = mysql.connector.connect(**db_config)


def is_valid_email(email):
    # Eenvoudige reguliere expressie om een e-mailadres te valideren
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

# Functie om spaties uit een string te verwijderen


def strip_spaces(text):
    return text.replace(" ", "")


@app.route('/aanmelden', methods=['GET', 'POST'])
def aanmelden():
    if request.method == 'POST':
        voornaam = strip_spaces(request.form.get('voornaam'))
        achternaam = strip_spaces(request.form.get('achternaam'))
        # Zet e-mail om naar hoofdletters
        email = strip_spaces(request.form.get('email')).upper()
        wachtwoord = request.form.get('wachtwoord')
        wachtwoord2 = request.form.get('herhaal-wachtwoord')

        # Controleer of wachtwoorden overeenkomen
        if wachtwoord != wachtwoord2:
            flash('Wachtwoorden komen niet overeen')
            return render_template('aanmelden.html')

        # Controleer de geldigheid van het e-mailadres
        if not is_valid_email(email):
            flash('Ongeldig e-mailadres')
            return render_template('aanmelden.html')

        # Controleer of het e-mailadres al in de database staat
        cursor = conn.cursor(buffered=True, dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE UPPER(usr_Email) = %s", (email,))
        user = cursor.fetchone()

        if user:
            flash('E-mailadres is al in gebruik')
            return render_template('aanmelden.html')
        hashed_wachtwoord = bcrypt.generate_password_hash(
            wachtwoord).decode('utf-8')

        print(hashed_wachtwoord)
        # Voeg gebruiker toe aan de gebruikerstabel
        cursor.execute("INSERT INTO users (usr_FirstName, usr_LastName, usr_Email, usr_Password) VALUES (%s, %s, %s, %s)",
                       (voornaam, achternaam, email, hashed_wachtwoord))
        cursor.close()
        conn.commit()
        print("Gelukt!")

        return redirect('/login')

    # Als het een GET-verzoek is, render je gewoon de aanmeldpagina
    return render_template('aanmelden.html')


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


@app.route('/deelnemenaangroep', methods=['GET', 'POST'])
def deelnemenaangroep():
    if 'user_id' in session:
        pass
    else:
        return redirect(url_for('login'))

    if request.method == 'POST':
        invite_code = request.form.get('invite_code')
        print(invite_code)

        # Zoek naar de groep met de opgegeven uitnodigingscode
        cursor = conn.cursor(buffered=True, dictionary=True)
        cursor.execute(
            "SELECT * FROM `groups` WHERE group_InviteCode = %s ", (str(invite_code),))
        group = cursor.fetchone()
        if group:
            cursor.execute("UPDATE users SET usr_groupID = %s WHERE usr_ID = %s",
                           (group['group_ID'], session['user_id']))
            cursor.close()
            conn.commit()
            session['user_groupid'] = group['group_ID']
            session['user_groupname'] = group['group_Name']
            session['user_groupinvitecode'] = group['group_InviteCode']

            # Redirect naar de accountpagina of een andere gewenste pagina
            return redirect('/mijnaccount')

    return render_template('deelnemenaangroep.html')


@app.route('/verlaatgroep', methods=['GET'])
def verlaat_groep():
    if 'user_id' in session:
        user_id = session['user_id']

        # Controleer of de gebruiker een groep heeft
        if session['user_groupid'] is not None:
            cursor = conn.cursor(buffered=True, dictionary=True)
            cursor.execute(
                "UPDATE users SET usr_groupID = NULL WHERE usr_ID = %s", (user_id,))
            cursor.close()
            conn.commit()
            session.pop('user_groupid', None)
            session.pop('user_groupname', None)

            # Hier kun je verdere verwerkingsstappen toevoegen, zoals het bijwerken van de database

            # Redirect naar de accountpagina of een andere gewenste pagina
            return redirect('/mijnaccount')

    # Redirect naar de inlogpagina als de gebruiker niet is ingelogd
    return redirect('/login')


@app.route('/maakgroep', methods=['GET', 'POST'])
def maak_groep():
    if 'user_id' in session:
        user_id = session['user_id']
        group_name = request.form.get('group_name')

        if request.method == 'POST':
            # Maak een nieuwe groep en wijs een unieke ID toe
            # ...

            # Maak een unieke group_InviteCode:
            code = str(uuid.uuid4())[:6]  # Haal de eerste 6 tekens van de UUID

            # Verwijder eventuele streepjes
            code = code.replace('-', '')
            cursor = conn.cursor(buffered=True, dictionary=True)
            cursor.execute(
                "INSERT INTO `groups` (group_Name, group_InviteCode) VALUES (%s, %s)",
                (group_name, code))

            cursor.execute(
                "SELECT group_ID FROM `groups` WHERE group_InviteCode = %s", (code,))
            group_id = cursor.fetchone()['group_ID']
            cursor.execute(
                "UPDATE users SET usr_groupID = %s WHERE usr_ID = %s", (group_id, user_id))

            # Voeg de groepgegevens toe aan de sessie (optioneel)
            session['user_groupid'] = group_id
            session['user_groupname'] = group_name
            session['user_groupinvitecode'] = code
            cursor.close()
            conn.commit()

            # Hier kun je verdere verwerkingsstappen toevoegen, zoals het bijwerken van de database
            # Redirect naar de accountpagina of een andere gewenste pagina
            return redirect('/mijnaccount')

        return render_template('maakgroep.html')

    # Redirect naar de inlogpagina als de gebruiker niet is ingelogd
    return redirect('/login')


@app.route('/niet_in_groep', methods=['GET'])
def not_in_group():
    return render_template('niet_in_groep.html')


# LOGIN LOGICS
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Query the database to check if the user exists with the provided username and password
        cursor = conn.cursor(buffered=True, dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE UPPER(usr_Email) = %s", (email.upper(),))
        user = cursor.fetchone()
        cursor.close()

        if user and bcrypt.check_password_hash(user['usr_Password'], password):
            # Store user information in the session
            session['user_id'] = user['usr_ID']
            session['user_email'] = user['usr_Email']
            session['user_firstname'] = user['usr_FirstName']
            session['user_lastname'] = user['usr_LastName']
            if user['usr_groupID'] is not None:
                session['user_groupid'] = user['usr_groupID']
                cursor = conn.cursor(buffered=True, dictionary=True)
                cursor.execute(
                    "SELECT * FROM `groups` WHERE group_ID = %s", (user['usr_groupID'],))
                groupid = cursor.fetchone()
                session['user_groupinvitecode'] = groupid['group_InviteCode']
                session['user_groupname'] = groupid['group_Name']
                cursor.close()
            else:
                session['user_groupid'] = None
            # Create a response object
            resp = make_response(redirect(url_for('home')))

            # Set a cookie with user information (e.g., user ID)
            resp.set_cookie('user_id', str(user['usr_ID']))
            resp.set_cookie('user_email', user['usr_Email'])
            resp.set_cookie('user_firstname', user['usr_FirstName'])
            resp.set_cookie('user_lastname', user['usr_LastName'])
            if user['usr_groupID'] is not None:
                resp.set_cookie('user_groupid', str(user['usr_groupID']))
                cursor = conn.cursor(buffered=True, dictionary=True)
                cursor.execute(
                    "SELECT * FROM `groups` WHERE group_ID = %s", (user['usr_groupID'],))
                groupid = cursor.fetchone()
                resp.set_cookie('user_groupinvitecode',
                                groupid['group_InviteCode'])
                resp.set_cookie('user_groupname', groupid['group_Name'])
                cursor.close()

            return resp  # Return the response object with the cookie

        else:
            flash('Login failed. Check your username and password.', 'danger')

    return render_template('login.html')


@app.route('/add_category', methods=['POST'])
def add_category():
    if 'user_groupid' not in session:
        # Stuur gebruiker naar de loginpagina als er geen groep-ID in de sessie is
        return redirect('/login')

    new_category = request.form.get('new_category')

    if new_category:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories (cat_Name, cat_groupID) VALUES (%s, %s)",
                       (new_category, session['user_groupid']))
        conn.commit()
        cursor.close()

    return redirect('/lijstjeinstellingen')


@app.route('/lijstjeinstellingen', methods=['GET'])
def lijstjeinstellingen():
    if session.get('user_groupid') is None:
        return redirect('/login')
    else:
        return render_template('lijstjeinstellingen.html')


@app.route('/remove_category', methods=['POST'])
def remove_category():
    if 'user_groupid' not in session:
        # Stuur gebruiker naar de loginpagina als er geen groep-ID in de sessie is
        return redirect('/login')

    category_to_remove = request.form.get('category_to_remove')

    if category_to_remove:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE cat_Name = %s AND cat_groupID = %s",
                       (category_to_remove, session['user_groupid']))
        conn.commit()
        cursor.close()

    return redirect('/lijstjeinstellingen')


@app.route('/mijnlijstje', methods=['GET'])
def mijnlijstje():
    if session.get('user_groupid') is None:
        return redirect('/niet_in_groep')  # Redirect to the warning page
    else:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM products WHERE prod_groupID = %s", (session['user_groupid'],))
        products = cursor.fetchall()
        cursor.close()
        return render_template('mijnlijstje.html', products=products)


@app.route('/add_item', methods=['POST'])
def add_item():
    if 'user_groupid' not in session:
        # Stuur gebruiker naar de loginpagina als er geen groep-ID in de sessie is
        return redirect('/login')

    new_item = request.form.get('new_item')
    new_category = request.form.get('new_item_category')

    if new_item and new_category:
        # Get the category ID
        cursor = conn.cursor(buffered=True, dictionary=True)
        cursor.execute("SELECT * FROM categories WHERE cat_Name = %s AND cat_groupID = %s",
                       (new_category, session['user_groupid']))
        category = cursor.fetchone()
        print(category['cat_ID'])
        cursor.close()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (prod_Name, prod_groupID, prod_CatID) VALUES (%s, %s, %s)",
                       (new_item, session['user_groupid'], category['cat_ID']))
        conn.commit()
        cursor.close()

    return redirect('/mijnlijstje')


@app.route('/remove_item/<int:item_id>', methods=['GET'])
def remove_item(item_id):
    if 'user_groupid' not in session:
        # Stuur gebruiker naar de loginpagina als er geen groep-ID in de sessie is
        return redirect('/login')

    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE prod_ID = %s", (item_id,))
    conn.commit()
    cursor.close()

    return redirect('/mijnlijstje')


@app.route('/get_categories', methods=['GET'])
def get_categories():
    if 'user_groupid' not in session:
        # Geef een lege lijst terug als de gebruiker niet is ingelogd
        return jsonify({'categories': []})

    cursor = conn.cursor()
    cursor.execute(
        "SELECT cat_Name FROM categories WHERE cat_groupID = %s", (session['user_groupid'],))
    categories = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return jsonify({'categories': categories})


@app.route('/get_products_by_category/<category>', methods=['GET'])
def get_products_by_category(category):
    if 'user_groupid' not in session:
        # Geef een lege lijst terug als de gebruiker niet is ingelogd
        return jsonify({'products': []})

    cursor = conn.cursor(dictionary=True)
    print(category)
    print(session['user_groupid'])
    cursor.execute("SELECT * FROM categories WHERE cat_Name = %s AND cat_groupID = %s",
                   (category, session['user_groupid']))
    result = cursor.fetchone()
    print(result)

    if result:
        category_id = result['cat_ID']
        cursor.execute("SELECT * FROM products WHERE prod_groupID = %s AND prod_CatID = %s",
                       (session['user_groupid'], category_id))
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
    session.pop('user_groupid', None)
    session.pop('user_groupname', None)
    session.pop('user_groupinvitecode', None)

    # Create a response object
    resp = make_response(redirect(url_for('login')))

    # Remove the 'user_id' cookie
    resp.delete_cookie('user_id')
    resp.delete_cookie('user_email')
    resp.delete_cookie('user_firstname')
    resp.delete_cookie('user_lastname')
    resp.delete_cookie('user_groupid')
    resp.delete_cookie('user_groupname')
    resp.delete_cookie('user_groupinvitecode')

    return resp  # Return the response object with the removed cookie


if __name__ == '__main__':
    app.run(debug=True)
