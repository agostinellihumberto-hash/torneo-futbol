import streamlit as st
import random
import pandas as pd

st.set_page_config(page_title="Gestor de Torneos de Fútbol", layout="wide")

st.title("🏆 Gestor Profesional de Torneo de Fútbol")
st.markdown("Configurá tu formato de torneo, cargá tus planteles y simulá resultados en tiempo real.")

# Inicialización de estados de sesión
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

LETRAS = ["A", "B", "C", "D"]

# --- FUNCIONES DE CÁLCULO Y FIXTURE ---
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

# --- PANTALLA DE CONFIGURACIÓN DE TORNEO ---
if not st.session_state.configurado:
    st.header("1. Configuración Inicial del Torneo")
    
    tipo_torneo = st.radio("¿Qué tipo de torneo querés armar?", 
                           ["Todos contra todos (1 grupo único)", "2 Grupos", "3 Grupos", "4 Grupos"])
    
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

    if st.button("🔥 Crear Fixture y Comenzar Torneo"):
        st.session_state.equipos = list(form_equipos.keys())
        st.session_state.grupo_equipo = list(form_equipos.values())
        st.session_state.cant_grupos = c_grupos
        st.session_state.jugadores = {eq: [] for eq in st.session_state.equipos}
        armar_fixture_total()
        st.session_state.configurado = True
        st.success("¡Torneo creado con éxito!")
        st.rerun()

# --- PANTALLA PRINCIPAL DEL TORNEO ACTIVO ---
else:
    # Barra lateral con información general y reseteo
    with st.sidebar:
        st.header("🏆 Estado del Torneo")
        st.write(f"Formatos: {st.session_state.cant_grupos} grupo(s)")
        st.write(f"Equipos registrados: {len(st.session_state.equipos)}")
        
        st.markdown("---")
        if st.button("❌ Reiniciar Todo el Torneo"):
            st.session_state.configurado = False
            st.session_state.equipos = []
            st.session_state.grupo_equipo = []
            st.session_state.partidos = []
            st.session_state.jugadores = {}
            st.rerun()
            
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Fixture y Resultados", "📊 Tablas de Posiciones", "🏃 Gestión de Jugadores", "🎲 Simulador Rápido"])

    # --- TAB 1: FIXTURE Y RESULTADOS ---
    with tab1:
        st.header("Resultados del Torneo")
        
        # Filtro opcional por grupo
        g_filtro = 0
        if st.session_state.cant_grupos > 1:
            g_seleccionado = st.selectbox("Filtrar por Grupo", [f"Grupo {LETRAS[i]}" for i in range(st.session_state.cant_grupos)])
            g_filtro = LETRAS.index(g_seleccionado.split(" ")[1])
            
        partidos_filtrados = [p for p in st.session_state.partidos if p['grupo'] == g_filtro]
        
        fechas = sorted(list(set(p['fecha'] for p in partidos_filtrados)))
        for f in fechas:
            st.markdown(f"### 🗓️ Fecha {f}")
            p_fecha = [p for p in partidos_filtrados if p['fecha'] == f]
            
            for idx, p in enumerate(p_fecha):
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
    with tab2:
        st.header("Tabla de Posiciones")
        
        for g in range(st.session_state.cant_grupos):
            if st.session_state.cant_grupos > 1:
                st.subheader(f"Grupo {LETRAS[g]}")
                
            equipos_grupo = [eq for idx, eq in enumerate(st.session_state.equipos) if st.session_state.grupo_equipo[idx] == g]
            stats = {eq: {'PTS': 0, 'PJ': 0, 'PG': 0, 'PE': 0, 'PP': 0, 'GF': 0, 'GC': 0, 'DG': 0} for eq in equipos_grupo}
            
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
            st.dataframe(df, use_container_width=True)

    # --- TAB 3: PLANTEL DE JUGADORES ---
    with tab3:
        st.header("Gestión de Planteles de Jugadores")
        eq_seleccionado = st.selectbox("Elegí un equipo para ver o agregar jugadores", st.session_state.equipos)
        
        # Agregar jugador
        nuevo_j = st.text_input("Nombre del nuevo jugador")
        if st.button("🏃 Registrar Jugador"):
            if nuevo_j.strip() != "":
                if nuevo_j.strip() not in st.session_state.jugadores[eq_seleccionado]:
                    st.session_state.jugadores[eq_seleccionado].append(nuevo_j.strip())
                    st.success(f"¡{nuevo_j.strip()} agregado a {eq_seleccionado}!")
                    st.rerun()
                else:
                    st.warning("Este jugador ya está en la plantilla.")
                    
        # Mostrar plantilla
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
    with tab4:
        st.header("Simulador Automático de Resultados")
        st.write("¿Querés jugar los partidos pendientes de forma rápida usando la computadora?")
        if st.button("🎲 Simular partidos restantes aleatoriamente"):
            simulados = 0
            for p in st.session_state.partidos:
                if p['goles_l'] < 0 or p['goles_v'] < 0:
                    p['goles_l'] = random.randint(0, 4)
                    p['goles_v'] = random.randint(0, 4)
                    simulados += 1
            if simulados > 0:
                st.success(f"¡Se han completado {simulados} partidos con simulaciones aleatorias!")
                st.rerun()
            else:
                st.info("No hay partidos pendientes para simular, ¡el torneo ya está completo!")
