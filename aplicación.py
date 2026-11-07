import streamlit as st
import random
import pandas as pd

st.set_page_config(page_title="Gestor Profesional de Fútbol", layout="wide")

st.title("🏆 Gestor Profesional de Torneo de Fútbol")
st.markdown("Configurá tu formato de torneo, cargá tus planteles, simulá resultados y disputá la fase eliminatoria (mata mata).")

# --- CONSTANTES ---
LETRAS = ["A", "B", "C", "D"]
ETAPAS = [["Semifinales", 4], ["Cuartos de final", 8], ["Octavos de final", 16]]

# --- ESTADO DE SESIÓN ---
if 'configurado' not in st.session_state:
    st.session_state.configurado = False
if 'equipos' not in st.session_state:
    st.session_state.equipos = []
if 'grupo_equipo' not in st.session_state:
    st.session_state.grupo_equipo = []
if 'partidos' not in st.session_state:
    st.session_state.partidos = []
if 'jugadores' not in st.session_state:
    st.session_state.jugadores = {}
if 'cant_grupos' not in st.session_state:
    st.session_state.cant_grupos = 1
if 'por_grupo' not in st.session_state:
    st.session_state.por_grupo = 0
if 'extras' not in st.session_state:
    st.session_state.extras = 0
if 'mata_mata_partidos' not in st.session_state:
    st.session_state.mata_mata_partidos = {}  # Ronda: lista de partidos

# --- FUNCIONES AUXILIARES ---
def armar_fixture_grupo(g, indices):
    participantes = list(indices)
    if len(participantes) % 2 == 1:
        participantes.append(-1)
    n = len(participantes)
    rotacion = list(range(n))

    grupo_partidos = []
    for f in range(n - 1):
        for k in range(n // 2):
            a = participantes[rotacion[k]]
            b = participantes[rotacion[n - 1 - k]]
            if k == 0 and f % 2 == 1:
                a, b = b, a
            if a != -1 and b != -1:
                grupo_partidos.append({
                    'fecha': f + 1,
                    'grupo': g,
                    'local': st.session_state.equipos[a],
                    'visita': st.session_state.equipos[b],
                    'goles_l': -1,
                    'goles_v': -1
                })
        ultimo = rotacion.pop()
        rotacion.insert(1, ultimo)
    return grupo_partidos

def armar_fixture_total():
    st.session_state.partidos = []
    for g in range(st.session_state.cant_grupos):
        indices = [i for i, grp in enumerate(st.session_state.grupo_equipo) if grp == g]
        st.session_state.partidos.extend(armar_fixture_grupo(g, indices))

def calcular_tabla_grupo(g):
    equipos_grupo = [eq for idx, eq in enumerate(st.session_state.equipos) if st.session_state.grupo_equipo[idx] == g]
    stats = {eq: {'EQ_IDX': st.session_state.equipos.index(eq), 'PTS': 0, 'PJ': 0, 'PG': 0, 'PE': 0, 'PP': 0, 'GF': 0, 'GC': 0, 'DG': 0} for eq in equipos_grupo}
    
    for p in st.session_state.partidos:
        if p['grupo'] == g and p['goles_l'] >= 0 and p['goles_v'] >= 0:
            loc, vis = p['local'], p['visita']
            gl, gv = p['goles_l'], p['goles_v']
            
            stats[loc]['PJ'] += 1
            stats[vis]['PJ'] += 1
            stats[loc]['GF'] += gl
            stats[loc]['GC'] += gv
            stats[vis]['GF'] += gv
            stats[vis]['GC'] += gl

            if gl > gv:
                stats[loc]['PTS'] += 3
                stats[loc]['PG'] += 1
                stats[vis]['PP'] += 1
            elif gl < gv:
                stats[vis]['PTS'] += 3
                stats[vis]['PG'] += 1
                stats[loc]['PP'] += 1
            else:
                stats[loc]['PTS'] += 1
                stats[vis]['PTS'] += 1
                stats[loc]['PE'] += 1
                stats[vis]['PE'] += 1

    for eq in stats:
        stats[eq]['DG'] = stats[eq]['GF'] - stats[eq]['GC']

    df = pd.DataFrame.from_dict(stats, orient='index').sort_values(by=['PTS', 'DG', 'GF'], ascending=False)
    return df

# --- LÓGICA DE FASE ELIMINATORIA ---
def obtener_clasificados():
    tablas = []
    for g in range(st.session_state.cant_grupos):
        tablas.append(calcular_tabla_grupo(g))

    clasificados = []
    # Clasificados por puesto directo
    for puesto in range(1, st.session_state.por_grupo + 1):
        for g in range(st.session_state.cant_grupos):
            row = tablas[g].iloc[puesto - 1]
            clasificados.append({
                'etiqueta': f"{puesto}° Grupo {LETRAS[g]}",
                'grupo': g,
                'equipo': row.name
            })

    # Mejores del puesto siguiente (mejores terceros, etc)
    candidatos = []
    for g in range(st.session_state.cant_grupos):
        row_candidato = tablas[g].iloc[st.session_state.por_grupo]
        candidatos.append({
            'equipo': row_candidato.name,
            'PTS': row_candidato['PTS'],
            'DG': row_candidato['DG'],
            'GF': row_candidato['GF'],
            'grupo': g
        })
    
    candidatos = sorted(candidatos, key=lambda x: (x['PTS'], x['DG'], x['GF']), reverse=True)
    
    for e in range(st.session_state.extras):
        clasificados.append({
            'etiqueta': f"Mejor {st.session_state.por_grupo + 1}° ({e + 1})",
            'grupo': candidatos[e]['grupo'],
            'equipo': candidatos[e]['equipo']
        })
    return clasificados

def armar_cruces(clasificados):
    total = len(clasificados)
    mitad = total // 2
    cruces = []
    for i in range(mitad):
        cruces.append([clasificados[i], clasificados[total - 1 - i]])

    # Intentar evitar emparejamiento del mismo grupo en primera ronda
    for i in range(mitad):
        if cruces[i][0]['grupo'] == cruces[i][1]['grupo'] and cruces[i][0]['grupo'] != -1:
            siguiente = (i + 1) % mitad
            cruces[i][1], cruces[siguiente][1] = cruces[siguiente][1], cruces[i][1]
    return cruces

# --- PANTALLA DE CONFIGURACIÓN DE TORNEO ---
if not st.session_state.configurado:
    st.header("1. Configuración Inicial del Torneo")

    tipo_torneo = st.radio("¿Qué tipo de torneo querés armar?",
                           ["Todos contra todos (1 grupo único - Gana el que sume más puntos)", "2 Grupos", "3 Grupos", "4 Grupos"])

    c_grupos = 1
    if "2 Grupos" in tipo_torneo: c_grupos = 2
    elif "3 Grupos" in tipo_torneo: c_grupos = 3
    elif "4 Grupos" in tipo_torneo: c_grupos = 4

    tam_grupos = []
    cols_g = st.columns(c_grupos)
    for g in range(c_grupos):
        with cols_g[g]:
            etiqueta = f"Equipos en Grupo {LETRAS[g]}" if c_grupos > 1 else "Cantidad de Equipos"
            tam = st.number_input(etiqueta, min_value=2, max_value=20, value=4, key=f"tam_g_{g}")
            tam_grupos.append(tam)

    # Selección de Clasificados para Mata-Mata
    por_grupo = 0
    extras = 0
    if c_grupos > 1:
        st.subheader("Configuración de Clasificados para Mata-Mata")
        total_equipos = sum(tam_grupos)
        min_tam = min(tam_grupos)

        st.info(f"Total de equipos en juego: {total_equipos}. Definamos la cantidad de clasificados a fase eliminatoria.")
        
        # Buscamos combinaciones de llaves válidas (4, 8 o 16 para mata-mata)
        opciones_validas = []
        for obj in [4, 8, 16]:
            if obj < total_equipos:
                p = obj // c_grupos
                ex = obj % c_grupos
                if p < min_tam and (ex == 0 or p + 1 < min_tam):
                    opciones_validas.append((obj, p, ex))
        
        if not opciones_validas:
            st.error("⚠️ No es posible armar una fase final exacta (Semifinales, Cuartos o Octavos) con este tamaño de grupos. Modificá las cantidades.")
        else:
            # Mostrar recomendación
            rec = opciones_validas[0]
            st.markdown(f"Recomendación: **Fase Final de {rec[0]} equipos** (Clasifican {rec[1]} por grupo y los {rec[2]} mejores siguientes del torneo)")
            
            opcion_elegida = st.selectbox("Seleccionar tamaño de Cuadro Eliminatorio", 
                                          [f"{item[0]} equipos (Pasan {item[1]} por grupo + {item[2]} mejores de repesca)" for item in opciones_validas])
            
            # Extraer los datos elegidos
            size_obj = int(opcion_elegida.split(" ")[0])
            por_grupo = size_obj // c_grupos
            extras = size_obj % c_grupos

    st.subheader("Nombres de los Equipos")
    form_equipos = {}
    for g in range(c_grupos):
        if c_grupos > 1:
            st.markdown(f"**Grupo {LETRAS[g]}**")
        cols_e = st.columns(tam_grupos[g])
        for i in range(tam_grupos[g]):
            with cols_e[i]:
                nombre_eq = st.text_input(f"Equipo {i+1}", value=f"Equipo {LETRAS[g] if c_grupos > 1 else ''}{i+1}", key=f"eq_name_{g}_{i}")
                form_equipos[nombre_eq] = g

    if c_grupos > 1 and not opciones_validas:
        st.warning("Por favor ajustá el tamaño de los grupos para habilitar el mata-mata.")
    else:
        if st.button("🔥 Crear Fixture y Comenzar Torneo"):
            st.session_state.equipos = list(form_equipos.keys())
            st.session_state.grupo_equipo = list(form_equipos.values())
            st.session_state.cant_grupos = c_grupos
            st.session_state.por_grupo = por_grupo
            st.session_state.extras = extras
            st.session_state.jugadores = {eq: [] for eq in st.session_state.equipos}
            st.session_state.mata_mata_partidos = {}
            armar_fixture_total()
            st.session_state.configurado = True
            st.success("¡Torneo creado con éxito!")
            st.rerun()

# --- PANTALLA PRINCIPAL DEL TORNEO ACTIVO ---
else:
    with st.sidebar:
        st.header("🏆 Estado del Torneo")
        st.write(f"Formato: {st.session_state.cant_grupos} grupo(s)")
        st.write(f"Equipos registrados: {len(st.session_state.equipos)}")
        if st.session_state.cant_grupos > 1:
            st.write(f"Clasifican a la Fase Final: {st.session_state.por_grupo * st.session_state.cant_grupos + st.session_state.extras} equipos")

        st.markdown("---")
        if st.button("❌ Reiniciar Todo el Torneo"):
            st.session_state.configurado = False
            st.session_state.equipos = []
            st.session_state.grupo_equipo = []
            st.session_state.partidos = []
            st.session_state.jugadores = {}
            st.session_state.mata_mata_partidos = {}
            st.rerun()

    # Definición de pestañas
    pestañas = ["📅 Fixture y Grupos", "📊 Tablas de Posiciones", "🏃 Gestión de Jugadores", "🎲 Simulador Rápido"]
    if st.session_state.cant_grupos > 1:
        pestañas.append("🏅 Fase Eliminatoria (Mata Mata)")
        
    tabs = st.tabs(pestañas)

    # --- TAB 1: FIXTURE Y RESULTADOS ---
    with tabs[0]:
        st.header("Resultados de la Fase de Grupos")
        g_filtro = 0
        if st.session_state.cant_grupos > 1:
            g_seleccionado = st.selectbox("Filtrar por Grupo", [f"Grupo {LETRAS[i]}" for i in range(st.session_state.cant_grupos)])
            g_filtro = LETRAS.index(g_seleccionado.split(" ")[1])

        partidos_filtrados = [p for p in st.session_state.partidos if p['grupo'] == g_filtro]
        fechas = sorted(list(set(p['fecha'] for p in partidos_filtrados)))
        
        for f in fechas:
            st.markdown(f"### 🗓️ Fecha {f}")
            p_fecha = [p for p in partidos_filtrados if p['fecha'] == f]

            for p in p_fecha:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 3])
                with col1:
                    st.write(f"**{p['local']}**")
                with col2:
                    g_l = st.number_input("Goles L", min_value=-1, max_value=20, value=int(p['goles_l']), key=f"gl_{p['local']}_{p['visita']}_{f}", label_visibility="collapsed")
                    p['goles_l'] = g_l
                with col3:
                    g_v = st.number_input("Goles V", min_value=-1, max_value=20, value=int(p['goles_v']), key=f"gv_{p['local']}_{p['visita']}_{f}", label_visibility="collapsed")
                    p['goles_v'] = g_v
                with col4:
                    st.write(f"**{p['visita']}**")
            st.write("---")

    # --- TAB 2: TABLA DE POSICIONES ---
    with tabs[1]:
        st.header("Tablas de Posiciones en Tiempo Real")
        for g in range(st.session_state.cant_grupos):
            if st.session_state.cant_grupos > 1:
                st.subheader(f"Grupo {LETRAS[g]}")
            df = calcular_tabla_grupo(g)
            st.dataframe(df.drop(columns=['EQ_IDX']), use_container_width=True)
            
            # Declaración del campeón para Grupo Único
            if st.session_state.cant_grupos == 1:
                partidos_pendientes = any(p['goles_l'] == -1 for p in st.session_state.partidos)
                if not partidos_pendientes:
                    st.balloons()
                    st.success(f"🏆 ¡Felicidades a **{df.index[0]}**, el CAMPEÓN de la liga tras finalizar todos los partidos!")

    # --- TAB 3: PLANTEL DE JUGADORES ---
    with tabs[2]:
        st.header("Gestión de Planteles de Jugadores")
        eq_seleccionado = st.selectbox("Elegí un equipo para ver o agregar jugadores", st.session_state.equipos)

        nuevo_j = st.text_input("Nombre del nuevo jugador")
        if st.button("🏃 Registrar Jugador"):
            if nuevo_j.strip() != "":
                if nuevo_j.strip() not in st.session_state.jugadores[eq_seleccionado]:
                    st.session_state.jugadores[eq_seleccionado].append(nuevo_j.strip())
                    st.success(f"¡{nuevo_j.strip()} agregado a {eq_seleccionado}!")
                    st.rerun()
                else:
                    st.warning("Este jugador ya está en la plantilla.")

        st.subheader(f"Plantilla de {eq_seleccionado}")
        plantel = st.session_state.jugadores[eq_seleccionado]
        if not plantel:
            st.info("No hay jugadores inscriptos en este equipo todavía.")
        else:
            for i, j in enumerate(plantel):
                col_j, col_b = st.columns([5, 1])
                with col_j:
                    st.write(f"{i+1}. {j}")
                with col_b:
                    if st.button("🗑️ Eliminar", key=f"del_{eq_seleccionado}_{i}"):
                        plantel.pop(i)
                        st.rerun()

    # --- TAB 4: SIMULADOR RÁPIDO ---
    with tabs[3]:
        st.header("Simulador Automático de Resultados")
        st.write("Simulá todos los partidos restantes de la fase de grupos automáticamente.")
        if st.button("🎲 Simular partidos pendientes de grupos"):
            simulados = 0
            for p in st.session_state.partidos:
                if p['goles_l'] < 0 or p['goles_v'] < 0:
                    p['goles_l'] = random.randint(0, 4)
                    p['goles_v'] = random.randint(0, 4)
                    simulados += 1
            if simulados > 0:
                st.success(f"¡Se han completado {simulados} partidos de grupos aleatoriamente!")
                st.rerun()
            else:
                st.info("No hay partidos de grupo pendientes por simular.")

    # --- TAB 5: MATA MATA (SOLO MULTI-GRUPO) ---
    if st.session_state.cant_grupos > 1:
        with tabs[4]:
            st.header("🏅 Cuadro Eliminatorio (Mata Mata)")
            
            # Validar si faltan jugarse partidos de grupos
            grupo_pendiente = any(p['goles_l'] == -1 for p in st.session_state.partidos)
            if grupo_pendiente:
                st.warning("⚠️ Tenés que registrar todos los resultados de la fase de grupos para habilitar de forma definitiva la fase de eliminación.")
            
            # Generar clasificados pro-forma o definitivos
            clasificados = obtener_clasificados()
            ronda_inicial_size = len(clasificados)
            ronda_inicial_nombre = "Semifinales" if ronda_inicial_size == 4 else ("Cuartos de final" if ronda_inicial_size == 8 else "Octavos de final")

            # Inicializar mata-mata si no existe o se debe regenerar
            if not st.session_state.mata_mata_partidos:
                cruces_iniciales = armar_cruces(clasificados)
                st.session_state.mata_mata_partidos[ronda_inicial_nombre] = []
                for i, c in enumerate(cruces_iniciales):
                    st.session_state.mata_mata_partidos[ronda_inicial_nombre].append({
                        'local': c[0]['equipo'],
                        'visita': c[1]['equipo'],
                        'goles_l': -1,
                        'goles_v': -1,
                        'etiqueta_l': c[0]['etiqueta'],
                        'etiqueta_v': c[1]['etiqueta']
                    })

            # Función para pasar de ronda
            def avanzar_ronda(ronda_actual, partidos_actuales):
                rondas_map = {"Octavos de final": "Cuartos de final", "Cuartos de final": "Semifinales", "Semifinales": "Final"}
                proxima_ronda = rondas_map[ronda_actual]
                
                # Validar que todos los de la ronda actual tengan ganadores
                ganadores = []
                for idx, p in enumerate(partidos_actuales):
                    if p['goles_l'] == -1 or p['goles_v'] == -1:
                        st.error("Faltan definir resultados de esta ronda para avanzar.")
                        return
                    if p['goles_l'] == p['goles_v']:
                        # Forzar desempate por penales ficticio
                        ganador = p['local'] if random.choice([True, False]) else p['visita']
                    else:
                        ganador = p['local'] if p['goles_l'] > p['goles_v'] else p['visita']
                    ganadores.append(ganador)
                
                # Crear cruces de la proxima ronda
                proximos_partidos = []
                for i in range(0, len(ganadores), 2):
                    proximos_partidos.append({
                        'local': ganadores[i],
                        'visita': ganadores[i+1],
                        'goles_l': -1,
                        'goles_v': -1,
                        'etiqueta_l': f"Ganador {i+1}",
                        'etiqueta_v': f"Ganador {i+2}"
                    })
                st.session_state.mata_mata_partidos[proxima_ronda] = proximos_partidos
                st.success(f"¡Se han armado los cruces de {proxima_ronda}!")
                st.rerun()

            # Mostrar cada ronda disputada hasta el momento
            orden_rondas = ["Octavos de final", "Cuartos de final", "Semifinales", "Final"]
            rondas_activas = [r for r in orden_rondas if r in st.session_state.mata_mata_partidos]
            
            for ronda in rondas_activas:
                st.subheader(f"⚔️ {ronda}")
                partidos_ronda = st.session_state.mata_mata_partidos[ronda]
                for idx, p in enumerate(partidos_ronda):
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 3])
                    with col1:
                        st.markdown(f"**{p['local']}** <small>({p['etiqueta_l']})</small>", unsafe_allow_html=True)
                    with col2:
                        gl = st.number_input("G", min_value=-1, max_value=20, value=int(p['goles_l']), key=f"mata_l_{ronda}_{idx}", label_visibility="collapsed")
                        p['goles_l'] = gl
                    with col3:
                        gv = st.number_input("G", min_value=-1, max_value=20, value=int(p['goles_v']), key=f"mata_v_{ronda}_{idx}", label_visibility="collapsed")
                        p['goles_v'] = gv
                    with col4:
                        st.markdown(f"**{p['visita']}** <small>({p['etiqueta_v']})</small>", unsafe_allow_html=True)
                
                # Botón de avanzar o de campeón si es final
                es_ultima_disponible = (ronda == rondas_activas[-1])
                if es_ultima_disponible:
                    if ronda != "Final":
                        if st.button(f"➡️ Generar siguientes llaves desde {ronda}"):
                            avanzar_ronda(ronda, partidos_ronda)
                    else:
                        # Declarar campeón de copa
                        final = partidos_ronda[0]
                        if final['goles_l'] >= 0 and final['goles_v'] >= 0:
                            if final['goles_l'] != final['goles_v']:
                                campeon = final['local'] if final['goles_l'] > final['goles_v'] else final['visita']
                                st.balloons()
                                st.success(f"🏆 ¡Felicidades a **{campeon}**, el CAMPEÓN absoluto del torneo tras ganar el mata-mata!")
                            else:
                                st.info("⚠️ Definición por penales requerida: Cargá un ganador diferente o editá los goles para coronar al campeón.")
                st.write("---")
