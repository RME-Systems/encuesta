from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'clave'
DATABASE_NAME = 'bd_encuestas.db'


def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        correo TEXT NOT NULL UNIQUE,
        rol TEXT NOT NULL DEFAULT 'usuario'
    );
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS encuestas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        descripcion TEXT,
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS preguntas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_encuesta INTEGER NOT NULL,
        texto_pregunta TEXT NOT NULL,
        tipo TEXT NOT NULL, -- 'texto' o 'escala' (1-5)
        FOREIGN KEY (id_encuesta) REFERENCES encuestas (id) ON DELETE CASCADE
    );
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS respuestas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_pregunta INTEGER NOT NULL,
        id_usuario INTEGER NOT NULL,
        respuesta_texto TEXT,
        valor INTEGER, -- Para tipo 'escala'
        FOREIGN KEY (id_pregunta) REFERENCES preguntas (id) ON DELETE CASCADE,
        FOREIGN KEY (id_usuario) REFERENCES usuarios (id) ON DELETE CASCADE
    );
    ''')


    conn.commit()
    conn.close()


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return redirect(url_for('ver_encuestas'))

@app.route('/encuestas')
def ver_encuestas():
    conn = get_db_connection()
    encuestas = conn.execute('SELECT * FROM encuestas').fetchall()
    conn.close()
    return render_template('encuestas.html', encuestas=encuestas)

@app.route('/encuestas/nueva', methods=['GET', 'POST'])
def nueva_encuesta():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO encuestas (titulo, descripcion) VALUES (?, ?)', (titulo, descripcion))
        conn.commit()
        conn.close()
        flash('Encuesta creada correctamente', 'success')
        return redirect(url_for('ver_encuestas'))
        
    return render_template('form_encuesta.html')

@app.route('/encuestas/editar/<int:id>', methods=['GET', 'POST'])
def editar_encuesta(id):
    conn = get_db_connection()
    encuesta = conn.execute('SELECT * FROM encuestas WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        
        conn.execute('UPDATE encuestas SET titulo = ?, descripcion = ? WHERE id = ?', (titulo, descripcion, id))
        conn.commit()
        conn.close()
        flash('Encuesta actualizada', 'success')
        return redirect(url_for('ver_encuestas'))

    return render_template('form_encuesta.html', encuesta=encuesta)

@app.route('/encuestas/eliminar/<int:id>')
def eliminar_encuesta(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM encuestas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Encuesta eliminada', 'danger')
    return redirect(url_for('ver_encuestas'))


@app.route('/encuestas/<int:id_encuesta>/preguntas')
def ver_preguntas(id_encuesta):
    conn = get_db_connection()
    encuesta = conn.execute('SELECT * FROM encuestas WHERE id = ?', (id_encuesta,)).fetchone()
    preguntas = conn.execute('SELECT * FROM preguntas WHERE id_encuesta = ?', (id_encuesta,)).fetchall()
    conn.close()
    return render_template('preguntas.html', preguntas=preguntas, encuesta=encuesta)

@app.route('/encuestas/<int:id_encuesta>/preguntas/nueva', methods=['GET', 'POST'])
def nueva_pregunta(id_encuesta):
    if request.method == 'POST':
        texto = request.form['texto_pregunta']
        tipo = request.form['tipo']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO preguntas (id_encuesta, texto_pregunta, tipo) VALUES (?, ?, ?)',
                     (id_encuesta, texto, tipo))
        conn.commit()
        conn.close()
        flash('Pregunta agregada', 'success')
        return redirect(url_for('ver_preguntas', id_encuesta=id_encuesta))
        
    return render_template('form_pregunta.html', id_encuesta=id_encuesta)

@app.route('/preguntas/eliminar/<int:id>')
def eliminar_pregunta(id):
    conn = get_db_connection()
    id_encuesta = conn.execute('SELECT id_encuesta FROM preguntas WHERE id = ?', (id,)).fetchone()['id_encuesta']
    conn.execute('DELETE FROM preguntas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Pregunta eliminada', 'danger')
    return redirect(url_for('ver_preguntas', id_encuesta=id_encuesta))


@app.route('/usuarios')
def ver_usuarios():
    conn = get_db_connection()
    usuarios = conn.execute('SELECT * FROM usuarios').fetchall()
    conn.close()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/usuarios/nuevo', methods=['GET', 'POST'])
def nuevo_usuario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        rol = request.form['rol']
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO usuarios (nombre, correo, rol) VALUES (?, ?, ?)', (nombre, correo, rol))
            conn.commit()
            flash('Usuario creado', 'success')
        except sqlite3.IntegrityError:
            flash('El correo ya existe', 'danger')
        finally:
            conn.close()
        return redirect(url_for('ver_usuarios'))
        
    return render_template('form_usuario.html')

@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    conn = get_db_connection()
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        rol = request.form['rol']
        
        try:
            conn.execute('UPDATE usuarios SET nombre = ?, correo = ?, rol = ? WHERE id = ?', (nombre, correo, rol, id))
            conn.commit()
            flash('Usuario actualizado', 'success')
        except sqlite3.IntegrityError:
            flash('El correo ya existe', 'danger')
        finally:
            conn.close()
        return redirect(url_for('ver_usuarios'))

    return render_template('form_usuario.html', usuario=usuario)

@app.route('/usuarios/eliminar/<int:id>')
def eliminar_usuario(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM usuarios WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Usuario eliminado', 'danger')
    return redirect(url_for('ver_usuarios'))


@app.route('/responder/<int:id_encuesta>', methods=['GET', 'POST'])
def responder_encuesta(id_encuesta):
    conn = get_db_connection()
    
    if request.method == 'POST':
        id_usuario = request.form['id_usuario']
        
        for key, value in request.form.items():
            if key.startswith('pregunta_'):
                id_pregunta = key.split('_')[1]
                tipo_pregunta = request.form[f'tipo_{id_pregunta}']
                
                respuesta_texto = None
                valor = None
                
                if tipo_pregunta == 'texto':
                    respuesta_texto = value
                elif tipo_pregunta == 'escala':
                    valor = int(value)
                
                conn.execute('''
                    INSERT INTO respuestas (id_pregunta, id_usuario, respuesta_texto, valor) 
                    VALUES (?, ?, ?, ?)
                ''', (id_pregunta, id_usuario, respuesta_texto, valor))
        
        conn.commit()
        conn.close()
        flash('¡Gracias por responder la encuesta!', 'success')
        return redirect(url_for('ver_encuestas'))

    encuesta = conn.execute('SELECT * FROM encuestas WHERE id = ?', (id_encuesta,)).fetchone()
    preguntas = conn.execute('SELECT * FROM preguntas WHERE id_encuesta = ?', (id_encuesta,)).fetchall()
    usuarios = conn.execute('SELECT * FROM usuarios WHERE rol = "usuario"').fetchall()
    conn.close()
    
    return render_template('responder_encuesta.html', encuesta=encuesta, preguntas=preguntas, usuarios=usuarios)


@app.route('/encuestas/<int:id_encuesta>/resultados')
def ver_resultados(id_encuesta):
    conn = get_db_connection()
    encuesta = conn.execute('SELECT * FROM encuestas WHERE id = ?', (id_encuesta,)).fetchone()
    
    preguntas = conn.execute('SELECT * FROM preguntas WHERE id_encuesta = ?', (id_encuesta,)).fetchall()
    
    resultados = []
    
    for p in preguntas:
        resultado = {'texto_pregunta': p['texto_pregunta'], 'tipo': p['tipo']}
        
        if p['tipo'] == 'escala':
            avg_data = conn.execute(
                'SELECT AVG(valor) as promedio, COUNT(id) as total FROM respuestas WHERE id_pregunta = ?', 
                (p['id'],)
            ).fetchone()
            resultado['promedio'] = round(avg_data['promedio'], 2) if avg_data['promedio'] else "N/A"
            resultado['total'] = avg_data['total']
            
            distribucion = conn.execute('''
                SELECT valor, COUNT(id) as cantidad FROM respuestas 
                WHERE id_pregunta = ? AND valor IS NOT NULL 
                GROUP BY valor ORDER BY valor
            ''', (p['id'],)).fetchall()
            
            resultado['chart_labels'] = [d['valor'] for d in distribucion]
            resultado['chart_data'] = [d['cantidad'] for d in distribucion]

        elif p['tipo'] == 'texto':
            respuestas_texto = conn.execute(
                'SELECT respuesta_texto FROM respuestas WHERE id_pregunta = ? AND respuesta_texto IS NOT NULL',
                (p['id'],)
            ).fetchall()
            resultado['respuestas'] = [r['respuesta_texto'] for r in respuestas_texto]
        
        resultados.append(resultado)
        
    conn.close()
    return render_template('resultados.html', encuesta=encuesta, resultados=resultados)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)