import streamlit as st
import random
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Gestión de Torneo de Fútbol", layout="wide")

st.title("🏆 Gestión de Torneo de Fútbol")
st.markdown("Bienvenido a la aplicación web de gestión de torneos. ¡Configurá tus equipos y simulá partidos!")

# Inicializar variables de estado de sesión si no existen
if 'equipos' not in st.session_state:
    st.session_state.equipos = []
if 'grupo_equipo' not in st.session_state:
    st.session_state.grupo_equipo = []
if 'partidos' not in st.session_state:
    st.session_state.partidos = []
if 'jugadores' not in st.session_state:
    st.session_state.jugadores = {}

# --- Panel Lateral: Configuración ---
with st.sidebar:
    st.header("⚙️ Configuración del Torneo")
    
    # Opción rápida de demostración
    if st.button("Cargar Demo Rápida (5 Equipos)"):
        st.session_state.equipos = ['Boca', 'River', 'Racing', 'Independiente', 'San Lorenzo']
        st.session_state.grupo_equipo = [0] * 5
        st.session_state.partidos = []
        # Método del círculo para fixture rápido
        n = len(st.session_state.equipos)
        for f in range(n - 1):
            for k in range(n // 2):
                a = (f + k) % (n - 1)
                b = (f + n - 1 - k) % (n - 1)
                if k == 0:
                    b = n - 1
                st.session_state.partidos.append({
                    'fecha': f + 1,
                    'local': st.session_state.equipos[a],
                    'visita': st.session_state.equipos[b],
                    'goles_l': -1,
                    'goles_v': -1
                })
        st.success("¡Demo cargada con éxito!")

# --- Cuerpo Principal ---
if not st.session_state.equipos:
    st.info("Hacé clic en el botón del panel izquierdo para cargar un torneo de demostración rápido.")
else:
    tab1, tab2, tab3 = st.tabs(["📅 Fixture y Resultados", "📊 Posiciones", "🎲 Simulación Automática"])
    
    with tab1:
        st.subheader("Fixture del Torneo")
        for p in st.session_state.partidos:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 3])
            with col1:
                st.write(p['local'])
            with col2:
                goles_l = st.number_input(f"Goles {p['local']}", min_value=-1, max_value=20, value=p['goles_l'], key=f"l_{p['local']}_{p['visita']}")
                p['goles_l'] = goles_l
            with col3:
                goles_v = st.number_input(f"Goles {p['visita']}", min_value=-1, max_value=20, value=p['goles_v'], key=f"v_{p['local']}_{p['visita']}")
                p['goles_v'] = goles_v
            with col4:
                st.write(p['visita'])
            st.write("---")
            
    with tab2:
        st.subheader("Tabla de Posiciones")
        # Cálculo de estadísticas en vivo
        stats = {eq: {'PTS': 0, 'PJ': 0, 'PG': 0, 'PE': 0, 'PP': 0, 'GF': 0, 'GC': 0, 'DG': 0} for eq in st.session_state.equipos}
        
        for p in st.session_state.partidos:
            if p['goles_l'] >= 0 and p['goles_v'] >= 0:
                gl = p['goles_l']
                gv = p['goles_v']
                loc = p['local']
                vis = p['visita']
                
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
        
    with tab3:
        st.subheader("Simulador Automático de Resultados")
        if st.button("🎲 Simular partidos pendientes aleatoriamente"):
            simulados = 0
            for p in st.session_state.partidos:
                if p['goles_l'] < 0 or p['goles_v'] < 0:
                    p['goles_l'] = random.randint(0, 4)
                    p['goles_v'] = random.randint(0, 4)
                    simulados += 1
            if simulados > 0:
                st.success(f"¡Se han simulado {simulados} partidos automáticamente!")
                st.rerun()
            else:
                st.info("No quedan partidos pendientes por simular.")
