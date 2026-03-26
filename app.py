import streamlit as st
import pandas as pd
from geopy.distance import geodesic
from streamlit_js_eval import get_geolocation # IMPORTANTE: Requiere pip install streamlit-js-eval

# --- FUNCIÓN DE PROCESAMIENTO ---
@st.cache_data
def cargar_y_limpiar(url):
    try:
        df = pd.read_csv(url)
        # Limpieza de coordenadas para evitar errores de spliteo
        df = df.dropna(subset=['Coordenadas'])
        coords = df['Coordenadas'].astype(str).str.replace(' ', '').str.split(',', expand=True)
        df['lat'] = pd.to_numeric(coords[0], errors='coerce')
        df['lon'] = pd.to_numeric(coords[1], errors='coerce')
        # Eliminar filas donde la conversión a número falló
        df = df.dropna(subset=['lat', 'lon'])
        return df
    except Exception as e:
        st.error(f"Error al procesar los datos: {e}")
        return pd.DataFrame()

def calcular_distancia(lat1, lon1, lat2, lon2):
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers

def main():
    # --- CONFIGURACIÓN DE PÁGINA ---
    st.set_page_config(
        page_title="Seguridad Entre Ríos", 
        page_icon="🚓", 
        layout="wide",
        initial_sidebar_state="collapsed" # Ayuda en celulares a ver el mapa primero
    )

    # --- ESTILO CSS PARA OCULTAR EL LOGO DE GITHUB Y AJUSTES MÓVILES ---
    # Nota: Aunque usamos el config.toml, este CSS asegura que el pie de página esté limpio
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        </style>
        """, unsafe_allow_html=True)

    # --- CONFIGURACIÓN DE ENLACES ---
    SHEETS = {
        "🛣️ Seguridad Vial": "1CCv1AyT2gtIGhcORYucGvVn5xmvR6f40Is_ZvmeusZw",
        "🌾 Seguridad Rural": "1CfFCv2YnYkorJzaz_ZdMLDJR5Ffl-wyPMTPppT8ChP0",
        "🏙️ Comisarías Paraná": "13p6cTaSLK0N5CbruagTnMR0YdlGVFdIusBXYNFWY0CA"
    }

    # --- SIDEBAR (Menú lateral) ---
    st.sidebar.title("🚔 Navegación")
    pagina = st.sidebar.radio("Seleccioná el área:", list(SHEETS.keys()))
    
    # --- SECCIÓN: NOTICIAS LOCALES ---
    st.sidebar.divider()
    st.sidebar.subheader("📰 Noticias de Entre Ríos")
    st.sidebar.link_button("🌐 Ir a El Once Digital", "https://www.elonce.com/")
    
    # --- SECCIÓN: VIDEO INSTITUCIONAL ---
    st.sidebar.divider()
    url_video = "https://youtu.be/QcyJONgBcvM" 
    st.sidebar.video(url_video)
    st.sidebar.caption("Noticiero El Once")

    # --- SECCIÓN: MI UBICACIÓN DINÁMICA ---
    st.sidebar.divider()
    st.sidebar.subheader("📍 Mi Ubicación")
    
    loc = get_geolocation()

    if loc:
        mi_lat = loc['coords']['latitude']
        mi_lon = loc['coords']['longitude']
        st.sidebar.success("✅ Ubicación detectada")
    else:
        st.sidebar.warning("Esperando GPS... (Viale por defecto)")
        mi_lat = -31.8650
        mi_lon = -59.7730

    st.sidebar.write(f"**Lat:** {mi_lat:.4f} | **Lon:** {mi_lon:.4f}")
    ordenar_cerca = st.sidebar.toggle("Ordenar por cercanía", value=True)

    # Carga de datos
    url_actual = f"https://docs.google.com/spreadsheets/d/{SHEETS[pagina]}/export?format=csv"

    df = cargar_y_limpiar(url_actual)
    if df.empty:
        st.warning("No se pudieron cargar los datos de la planilla.")
        st.stop()

    # Definir nombres de columnas según la hoja
    if pagina == "🛣️ Seguridad Vial":
        col_titulo = "Nombre Puesto Caminero"
        icono = "🏢"
    elif pagina == "🌾 Seguridad Rural":
        col_titulo = "Nombre Brigada"
        icono = "🚜"
    else:
        col_titulo = "Nombre Comisaría"
        icono = "👮"

    # --- CUERPO PRINCIPAL ---
    st.title(f"Sistema de {pagina}")
    
    busqueda = st.text_input(f"🔍 Buscar en {pagina}...", placeholder="Ej: Comisaría, San Benito, Ruta 12...")

    df_mostrar = df.copy()
    
    if busqueda:
        mask = (df_mostrar[col_titulo].str.contains(busqueda, case=False, na=False)) | \
               (df_mostrar['Ciudad'].str.contains(busqueda, case=False, na=False)) | \
               (df_mostrar['Dirección'].str.contains(busqueda, case=False, na=False))
        df_mostrar = df_mostrar[mask]

    if ordenar_cerca:
        df_mostrar['distancia'] = df_mostrar.apply(
            lambda row: calcular_distancia(mi_lat, mi_lon, row['lat'], row['lon']), axis=1
        )
        df_mostrar = df_mostrar.sort_values('distancia')

    # --- MAPA ---
    st.subheader("🗺️ Mapa de Unidades")
    st.map(df_mostrar[['lat', 'lon']], size=20, zoom=9)
    st.caption("💡 Tip: Deslizá desde los bordes de la pantalla para bajar en el celular.")
    
    st.divider()

    # --- VISTA DE TARJETAS ---
    st.subheader(f"📍 Listado ({len(df_mostrar)})")

    # En móviles, columns(2) se apila automáticamente, lo cual es bueno
    cols = st.columns(2)
    for i, (index, row) in enumerate(df_mostrar.iterrows()):
        with cols[i % 2]:
            with st.container(border=True):
                dist_txt = f" - 📍 {row['distancia']:.1f} km" if ordenar_cerca else ""
                st.markdown(f"#### {icono} {row[col_titulo]}")
                if ordenar_cerca: st.info(dist_txt)
                
                st.markdown(f"**📍 Ciudad:** {row['Ciudad']}")
                st.markdown(f"**🏠 Dirección:** {row['Dirección']}")
                
                # Gestión de teléfonos con links cliqueables
                tels = []
                for col_tel in ['Teléfono Guardia', 'Teléfono']:
                    if col_tel in row and pd.notna(row[col_tel]):
                        val = str(row[col_tel]).split('.')[0].strip() # Limpiar decimales .0
                        if val.upper() != "NO POSEE" and len(val) > 3:
                            tels.append(f"📞 [{val}](tel:{val})")
                
                if tels:
                    st.markdown(" / ".join(tels))
                else:
                    st.markdown("📞 *Teléfono no disponible*")
                
                link_maps = f"https://www.google.com/maps?q={row['lat']},{row['lon']}"
                st.link_button("🌐 Ver en Google Maps", link_maps)

    st.divider()
    st.caption("© 2026 Seguridad Entre Ríos - Desarrollado para la comunidad")

if __name__=='__main__':
    main()