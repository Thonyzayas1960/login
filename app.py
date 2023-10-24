from flask import Flask, render_template, request, session, redirect, url_for
from flask import flash
from flask_mysqldb import MySQL
from flask_bcrypt import check_password_hash
import bcrypt

app = Flask(__name__, template_folder='template')

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "login"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

# FUNCION DE LOGIN
@app.route('/acceso-login', methods=["GET", "POST"])
def login():
    if request.method == 'POST' and 'txtCorreo' in request.form and 'txtPassword' in request.form:
        _correo = request.form['txtCorreo']
        _password = request.form['txtPassword']

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM usuarios WHERE correo = %s', (_correo,))
        account = cur.fetchone()

        if account and check_password_hash(account['password'], _password):
            session['logeado'] = True
            session['id'] = account['id']
            session['id_rol'] = account['id_rol']

            if session['id_rol'] == 1:
                return render_template("admin.html")
            elif session['id_rol'] == 2:
                return render_template("usuario.html")
        else:
            return render_template('index.html', mensaje="Usuario o contraseña incorrectos")

    return render_template('index.html')

# Ruta para registrar afiliaciones
@app.route('/registrar-afiliacion', methods=['GET', 'POST'])
def registrar_afiliacion():
    if request.method == 'POST':
        if 'logeado' in session and session['id_rol'] == 1: # Asegúrate de que el administrador esté logeado
            _nombre_completo = request.form['nombre_completo']
            _cedula_identidad = request.form['cedula_identidad']
            _edad = request.form['edad']
            _sexo = request.form['sexo']
            _telefono = request.form['telefono']
            _domicilio = request.form['domicilio']
            _partido = request.form['partido']

            cur = mysql.connection.cursor()

            # Verificar si la cédula ya existe en la base de datos
            cur.execute('SELECT * FROM afiliaciones WHERE cedula_identidad = %s', (_cedula_identidad,))
            existing_afiliation = cur.fetchone()

            if existing_afiliation:
                flash(("Cédula ya existente.", "error"))
            else:
                cur.execute('INSERT INTO afiliaciones (nombre_completo, cedula_identidad, edad, sexo, telefono, domicilio, partido) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                            (_nombre_completo, _cedula_identidad, _edad, _sexo, _telefono, _domicilio, _partido))
                mysql.connection.commit()
                flash(("Afiliación Registrada con Éxito.", "success"))
                
            cur.close()

        else:
            flash(("Acceso denegado.", "error"))

    return render_template('registro_afiliacion.html')

# Ruta para consultar afiliación
@app.route('/consultar-afiliacion', methods=['GET', 'POST'])
def consultar_afiliacion():
    if request.method == 'POST':
        _cedula_identidad = request.form['cedula_identidad']
        # Realiza una consulta a la base de datos para buscar al usuario
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM afiliaciones WHERE cedula_identidad = %s', (_cedula_identidad,))
        usuario_afiliado = cur.fetchone()
        cur.close()

        if usuario_afiliado:
            # Si el usuario está afiliado, muestra sus datos
            return render_template('resultado_afiliacion.html', usuario=usuario_afiliado)
        else:
            # Si el usuario no está afiliado, muestra un mensaje de error
            mensaje_error = "Ops, acércate a un punto de afiliación de tu partido."
            return render_template('resultado_afiliacion.html', mensaje_error=mensaje_error)

    return render_template('consulta_afiliacion.html')

@app.route('/usuario')
def usuario():
    return render_template('index.html')

# Consulta de tabla de registro del administrador
@app.route('/registro-total')
def registro_total():
    if 'logeado' in session and session['id_rol'] == 1:
        # Realiza una consulta para obtener todos los usuarios afiliados
        cur = mysql.connection.cursor()
        cur.execute('SELECT id, nombre_completo, cedula_identidad, edad, sexo, telefono, domicilio, partido FROM afiliaciones')
        usuarios = cur.fetchall()
        cur.close()

        return render_template("tabla_registro_total.html", usuarios=usuarios)
    else:
        return "Acceso denegado."

# Nueva ruta para el registro público de afiliación
@app.route('/registro-afiliacion-publico', methods=['GET', 'POST'])
def registro_afiliacion_publico():
    if request.method == 'POST':
        _nombre_completo = request.form['nombre_completo']
        _cedula_identidad = request.form['cedula_identidad']
        _edad = request.form['edad']
        _sexo = request.form['sexo']
        _telefono = request.form['telefono']
        _domicilio = request.form['domicilio']
        _partido = request.form['partido']

        cur = mysql.connection.cursor()

        # Verifica si la cédula ya existe en la base de datos
        cur.execute('SELECT * FROM afiliaciones WHERE cedula_identidad = %s', (_cedula_identidad,))
        existe_cedula = cur.fetchone()

        if existe_cedula:
            mensaje = "La cédula ya está registrada en nuestra base de datos."
            return render_template('registro_afiliacion_publico.html', mensaje=mensaje)
        else:
            cur.execute('INSERT INTO afiliaciones (nombre_completo, cedula_identidad, edad, sexo, telefono, domicilio, partido) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (_nombre_completo, _cedula_identidad, _edad, _sexo, _telefono, _domicilio, _partido))
            mysql.connection.commit()
            cur.close()

            mensaje = "Afiliación registrada con éxito."
            return render_template('registro_afiliacion_publico.html', mensaje=mensaje)

    return render_template('registro_afiliacion_publico.html')

# Ruta para el registro
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        _correo = request.form['txtCorreo']
        _password = request.form['txtPassword']

        # Verificar si el correo ya existe en la base de datos
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM usuarios WHERE correo = %s', (_correo,))
        existing_user = cur.fetchone()
        cur.close()

        if existing_user:
            # Si el correo ya existe, muestra un mensaje de error
            return render_template('registro.html', mensaje="Correo electrónico ya registrado. Prueba con otro correo.")

        # Si el correo no existe, procede con el registro
        hashed_password = bcrypt.hashpw(_password.encode('utf-8'), bcrypt.gensalt())
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO usuarios (correo, password) VALUES (%s, %s)', (_correo, hashed_password))
        mysql.connection.commit()
        cur.close()

        return render_template('registro.html', mensaje="Registro exitoso")

    return render_template('registro.html')

# Ruta para la página de registro general
@app.route('/registro.html')
def registro_general():
    return render_template('registro.html')

if __name__ == '__main__':
    app.secret_key = "gabriel_hds"
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)