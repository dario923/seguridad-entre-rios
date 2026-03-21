import streamlit as st
import pandas as pd
from geopy.distance import geodesic

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
    # Podés cambiar este link por cualquier video de YouTube de la Policía
    url_video = "https://youtu.be/QcyJONgBcvM" 
    st.sidebar.video(url_video)
    st.sidebar.caption("Noticiero el once digital")

    # --- SECCIÓN: MI UBICACIÓN ---
    st.sidebar.divider()
    st.sidebar.subheader("📍 Mi Ubicación")
    
    # Coordenadas actuales (Viale por defecto)
    mi_lat = st.sidebar.number_input("Latitud:", value=-31.8647, format="%.6f")
    mi_lon = st.sidebar.number_input("Longitud:", value=-59.9128, format="%.6f")
    
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

    # Mapa principal (muestra las unidades filtradas)
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
                
                link_maps = f"https://www.google.com/maps?q={row['lat']},{row['lon']}"
                st.link_button("🌐 Abrir en Google Maps", link_maps)

if __name__=='__main__':
    main()