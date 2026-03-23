import streamlit as st
import pandas as pd
from geopy.distance import geodesic
from streamlit_js_eval import get_geolocation # IMPORTANTE: Requiere pip install streamlit-js-eval

# --- FUNCIÓN DE PROCESAMIENTO ---
@st.cache_data
def cargar_y_limpiar(url):
    df = pd.read_csv(url)
    df = df.dropna(subset=['Coordenadas'])
    coords = df['Coordenadas'].str.replace(' ', '').str.split(',', expand=True)
    df['lat'] = coords[0].astype(float)
    df['lon'] = coords[1].astype(float)
    return df

def calcular_distancia(lat1, lon1, lat2, lon2):
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers

def main():
    st.set_page_config(page_title="Seguridad Entre Ríos", page_icon="🚓", layout="wide")

    # --- CONFIGURACIÓN DE ENLACES ---
    SHEETS = {
        "🛣️ Seguridad Vial": "1CCv1AyT2gtIGhcORYucGvVn5xmvR6f40Is_ZvmeusZw",
        "🌾 Seguridad Rural": "1CfFCv2YnYkorJzaz_ZdMLDJR5Ffl-wyPMTPppT8ChP0",
        "🏙️ Comisarías Paraná": "13p6cTaSLK0N5CbruagTnMR0YdlGVFdIusBXYNFWY0CA"
    }

    # --- SIDEBAR (Menú lateral) ---
    st.sidebar.title("🚔 Navegación")
    pagina = st.sidebar.radio("Seleccioná el área:", list(SHEETS.keys()))

    # --- SECCIÓN: VIDEO INSTITUCIONAL ---
    st.sidebar.divider()
    url_video = "https://youtu.be/QcyJONgBcvM" 
    st.sidebar.video(url_video)
    st.sidebar.caption("Noticiero el once digital")

    # --- SECCIÓN: MI UBICACIÓN DINÁMICA (JAVASCRIPT) ---
    st.sidebar.divider()
    st.sidebar.subheader("📍 Mi Ubicación")
    
    # Intentamos obtener la ubicación real del dispositivo
    loc = get_geolocation()

    if loc:
        # Si el navegador/celular da permiso, usamos las coordenadas reales
        mi_lat = loc['coords']['latitude']
        mi_lon = loc['coords']['longitude']
        st.sidebar.success("✅ Ubicación detectada")
    else:
        # Si falla o está cargando, usamos Viale como backup
        st.sidebar.warning("Esperando GPS... (Usando Viale por defecto)")
        mi_lat = -31.8650
        mi_lon = -59.7730

    # Mostramos las coordenadas actuales en la barra lateral
    st.sidebar.write(f"**Lat:** {mi_lat:.6f}")
    st.sidebar.write(f"**Lon:** {mi_lon:.6f}")
    
    ordenar_cerca = st.sidebar.toggle("Ordenar por cercanía", value=True)

    # Carga de datos
    url_actual = f"https://docs.google.com/spreadsheets/d/{SHEETS[pagina]}/export?format=csv"

    try:
        df = cargar_y_limpiar(url_actual)
        if pagina == "🛣️ Seguridad Vial":
            col_titulo = "Nombre Puesto Caminero"
            icono = "🏢"
        elif pagina == "🌾 Seguridad Rural":
            col_titulo = "Nombre Brigada"
            icono = "🚜"
        else:
            col_titulo = "Nombre Comisaría"
            icono = "👮"
    except Exception as e:
        st.error(f"Error al conectar con {pagina}: {e}")
        st.stop()

    # --- CUERPO PRINCIPAL ---
    st.title(f"Sistema de {pagina}")
    
    busqueda = st.text_input(f"🔍 Buscar en {pagina}...", placeholder="Ej: Comisaría 5ta, San Benito...")

    df_mostrar = df.copy()
    
    # Filtrado por texto
    if busqueda:
        mask = (df_mostrar[col_titulo].str.contains(busqueda, case=False, na=False)) | \
               (df_mostrar['Ciudad'].str.contains(busqueda, case=False, na=False)) | \
               (df_mostrar['Dirección'].str.contains(busqueda, case=False, na=False))
        df_mostrar = df_mostrar[mask]

    # Cálculo de distancias y ordenamiento
    if ordenar_cerca:
        df_mostrar['distancia'] = df_mostrar.apply(
            lambda row: calcular_distancia(mi_lat, mi_lon, row['lat'], row['lon']), axis=1
        )
        df_mostrar = df_mostrar.sort_values('distancia')

    # Mapa principal
    st.subheader("🗺️ Mapa de Unidades")
    st.map(df_mostrar[['lat', 'lon']])

    st.divider()

    # --- VISTA DE TARJETAS ---
    st.subheader(f"📍 Listado de Unidades ({len(df_mostrar)})")

    cols = st.columns(2)
    for i, (index, row) in enumerate(df_mostrar.iterrows()):
        with cols[i % 2]:
            with st.container(border=True):
                dist_txt = f" - 📍 a {row['distancia']:.2f} km" if ordenar_cerca else ""
                st.markdown(f"### {icono} {row[col_titulo]}{dist_txt}")
                st.markdown(f"**📍 Ciudad:** {row['Ciudad']}")
                st.markdown(f"**🏠 Dirección:** {row['Dirección']}")
                
                # Teléfonos
                tels = []
                if 'Teléfono Guardia' in row and pd.notna(row['Teléfono Guardia']):
                    t1 = str(row['Teléfono Guardia']).replace('.0','')
                    tels.append(f"📞 **Guardia:** [{t1}](tel:{t1})")
                if 'Teléfono' in row and pd.notna(row['Teléfono']) and str(row['Teléfono']) != "NO POSEE":
                    t2 = str(row['Teléfono']).replace('.0','')
                    tels.append(f"☎️ **Oficina:** [{t2}](tel:{t2})")
                
                if tels:
                    for t in tels: st.markdown(t)
                else:
                    st.markdown("📞 **Teléfono:** No disponible")
                
                # Botón con link corregido para Google Maps
                link_maps = f"https://www.google.com/maps?q={row['lat']},{row['lon']}"
                st.link_button("🌐 Abrir en Google Maps", link_maps)

if __name__=='__main__':
    main()