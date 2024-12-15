import streamlit as st
import pandas as pd
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import plotly.express as px



#Función para normalizar tanto los valores de mercado como las estadísticas.
def normalizar_valor(valor):
    if not valor or valor == '-':
        return None
    valor = valor.replace('€', '').strip()  #Eliminar el símbolo de €.
    if 'm' in valor:
        return float(valor.replace('m', ''))*1e6  #Convertir la 'm' a millones.
    elif 'k' in valor:
        return float(valor.replace('k', ''))*1e3  #Convertir la 'k' a miles.
    else:
        return int(valor)  #En otro caso convertimos el valor a entero.

#Genera la URL para los valores de mercado de un equipo y temporada específicos en Transfermarkt.
def get_team_season_marketvalues_url(team, code, season):
    return f'https://www.transfermarkt.co.uk/{team}/kader/verein/{code}/plus/0/galerie/0?saison_id={season}'

#Genera la URL para las estadísticas generales de un equipo y temporada específicos en Transfermarkt.
def get_team_season_stats_url(team, code, season):
    return f'https://www.transfermarkt.es/{team}/leistungsdaten/verein/{code}/plus/1?reldata=%26{season}'

#Función de scraping genérica para manejar varias temporadas o dos temporadas específicas.
def scrape_transfermarkt_data(team, code, seasons, display=None):
    
    #Definimos las listas donde almacenaremos los datos respectivos.
    marketvalue_data = []
    stats_data = []
    
    #Cabecera que incluyen un agente de usuario aleatorio para evitar bloqueos.
    headers = {'User-Agent': UserAgent().random}

    for season in seasons:
        
        #Scrapeo de VALORES DE MERCADO:
        
        #Genera la URL para la temporada que estamos scrapeando.
        marketvalue_url = get_team_season_marketvalues_url(team, code, season)
        #Realiza la solicitud HTTP.
        marketvalue_request = requests.get(marketvalue_url, headers=headers)
        
        #Control de errores.
        if marketvalue_request.status_code != 200:
            if display:
                 display(f'Error al descargar valores de mercado para la temporada {season}: {marketvalue_request.status_code}')
            continue  
        
        #Analizamos el contenido de la página con BeautifulSoup.
        marketvalue_soup = BeautifulSoup(marketvalue_request.content, 'html.parser')
        
        #Seleccionamos todas las filas de la tabla y las vamos iterando.
        rows = marketvalue_soup.find_all('tr', class_=['odd', 'even'])
        for row in rows:
            
            #Extrae el número de jugador.
            number = row.select('div.rn_nummer')
            number = normalizar_valor(number[0].text.strip()) if number else None
            
            #Extrae el nombre del jugador.
            player = row.select('td.hauptlink')
            player = player[0].text.strip() if player else None
            
            #Extrae la posición del jugador.
            position_cell = row.select('td')[1]  #Sacamos la segunda columna de la tabla (Nombre y Posición).
            position = None
            if position_cell:
                position_text = position_cell.text.strip()  #Sacamos el texto y eliminamos los espacios en blanco.
                position = position_text.split()[-1]  #Dividimos el texto por espacios ([Nombre, Posición]) y nos quedamos con la última palabra.
            
            #Extrae la edad del jugador.
            age = row.select('td.zentriert')
            age = normalizar_valor(age[1].text.strip()) if age else None
            
            #Extrae la nacionalidad del jugador.
            nationality = row.select('img.flaggenrahmen')
            nationality = nationality[0]['title'] if nationality else None
            
            #Extrae el valor de mercado del jugador.
            market_value = row.select('td.rechts.hauptlink')
            market_value = normalizar_valor(market_value[0].text.strip()) if market_value else None
            
            #Agrega la información al conjunto de datos.
            marketvalue_data.append({
                'Season': str(season),   #Queremos que las temporadas sean una variable categórica para manejarlas mejor más adelante.
                'Number': number,
                'Player': player,
                'Position': position,
                'Age': age,
                'Nationality': nationality,
                'Market Value': market_value
            })
        
        #Muestra el progreso por pantalla en la aplicación de Streamlit.  
        if display:
            display(f'Valores de mercado de la temporada {season} completados.')



        #Scrapeo de ESTADÍSTICAS:
        
        #Genera la URL para la temporada que estamos scrapeando.
        stats_url = get_team_season_stats_url(team, code, season)
        #Realiza la solicitud HTTP.
        stats_request = requests.get(stats_url, headers=headers)
        
        #Control de errores.
        if stats_request.status_code != 200:
            if display:
                 display(f'Error al descargar estadísticas para la temporada {season}: {stats_request.status_code}')
            continue  
        
        #Analizamos el contenido de la página con BeautifulSoup.
        stats_soup = BeautifulSoup(stats_request.content, 'html.parser')
        
        #Seleccionamos todas las filas de la tabla y las vamos iterando.
        rows = stats_soup.find_all('tr', class_=['odd', 'even'])
        for row in rows:
            
            zentriert = row.select('td.zentriert')
            
            #Verifica si la fila contiene 'No ha sido alineado esta temporada' o 'No ha estado en la plantilla esta temporada'.
            if any(cell.text.strip() in ['No ha sido alineado esta temporada', 'No ha estado en la plantilla esta temporada'] for cell in zentriert):
                continue
            
            #Extrae el nombre del jugador.
            player = row.select_one('td.hauptlink a[title]')
            player = player.text.strip() if player else None
            
            #Extrae las titularidades del jugador.
            lineups = zentriert[4].text.strip() 
            lineups = normalizar_valor(lineups) if lineups else None
            
            #Extrae los goles del jugador.
            goals = zentriert[5].text.strip()
            goals = normalizar_valor(goals) if goals else None
            
            #Extrae las asistencias del jugador.
            assists = zentriert[6].text.strip()
            assists = normalizar_valor(assists)if assists else None
            
            #Extrae las tarjetas amarillas del jugador.
            yellow_cards = zentriert[7].text.strip()
            yellow_cards = normalizar_valor(yellow_cards) if yellow_cards else None
            
            #Extrae las segundas tarjetas amarilla del jugador.
            second_card = zentriert[8].text.strip() 
            second_card = normalizar_valor(second_card) if second_card else None
            
            #Extrae las tarjetas rojas del jugador.
            red_cards = zentriert[9].text.strip()
            red_cards = normalizar_valor(red_cards) if red_cards else None
            
            #Agrega la información al conjunto de datos.
            stats_data.append({
                'Season': str(season),
                'Player': player,
                'Lineups': lineups,
                'Goals': goals,
                'Assists': assists,
                'Yellow Cards': yellow_cards,
                'Second Card' : second_card,
                'Red Cards': red_cards
            })
            
        #Muestra el progreso en pantalla de la aplicación en Streamlit.
        if display:
            display(f'Estadísticas de la temporada {season} completadas.')

    marketvalue_df = pd.DataFrame(marketvalue_data)
    stats_df = pd.DataFrame(stats_data)
    
    #Combina las dos tablas en una única, por Jugador y Temporada.
    combined_data = pd.merge(marketvalue_df, stats_df, on=['Player', 'Season'], how='inner')
    
    return combined_data



### APP STREAMLIT ###

#Definimos la página principal de nuestra aplicación de Streamlit.
def main_app():
    
    #Título de la aplicación.
    st.title('Transfermarkt Scraper')

    #Selector del modo que queremos emplear para el estudio: Rango de temporadas o Comparar dos temporadas.
    mode = st.radio('Selecciona el método de estúdio:',
                    options=['Examinar un Rango de Temporadas', 'Examinar dos Temporadas'],
                    index=0)

    #Lista de equipos con sus códigos predefinidos.
    predefined_teams = {'Real Madrid': '418',
                        'FC Barcelona': '131',
                        'Atlético de Madrid': '13',
                        'Manchester City': '281',
                        'Liverpool': '31',
                        'Chelsea': '631',
                        'Bayern Múnich': '27',
                        'Paris Saint-Germain': '583',
                        'Juventus': '506',
                        'AC Milan': '5',
                        'Inter de Milán': '46',
                        'Ponferradina': '4032'}

    #Podemos seleccionar un equipo de los que hemos predefinido o buscar uno en Transfermarkt y escribirlo con su codigo manualmente.
    st.subheader('Selecciona un equipo o escribe uno:')
    predefined_team = st.selectbox('Equipos predefinidos:',
                                   options=['Seleccionar manualmente...'] + list(predefined_teams.keys()),
                                   index=0)

    if predefined_team == 'Seleccionar manualmente...':
        team = st.text_input('Nombre del equipo (en la URL de Transfermarkt):')
        code = st.text_input('Código del equipo (en la URL de Transfermarkt):')
    else:
        team = predefined_team
        code = predefined_teams[predefined_team]

    #Dependiendo del modo de estudio extraemos unos gráficos u otros. 
    if mode == 'Examinar un Rango de Temporadas':
        
        st.markdown('### Búsqueda por Rango de Temporadas')
        
        #Podemos elejir un rango de años entre los últimos 20 años (para años anteriores no hay practicamente datos).
        start_season = st.number_input('Temporada de inicio:', min_value=2005, max_value=2025, value=2020)
        end_season = st.number_input('Temporada de fin:', min_value=2005, max_value=2025, value=2024)

        
        if st.button('Scrapear Datos'):
            #Aparece una rueda de carga con el texto mientras se cargan los datos.
            with st.spinner('Preparando el scraping...'):
                
                #Se crea una caja vacia donde iremos lanzando texto con el progreso del scraping.
                progress_placeholder = st.empty()

                #Función que despliega los mensajes que tenia el parametro display durante el scrapeo.
                def display(message):
                    progress_placeholder.text(message)

                #Pasamos de las dos temporadas que limitan el rango a una lista con todos los años dentro de ese rango.
                seasons = list(range(start_season, end_season + 1))
                #Llamada a la función principal de scraping para sacar el DataFrame final con los parámetros indicados en la app de Streamlit.
                combined_data = scrape_transfermarkt_data(team, code, seasons, display)
                #Mantiene la almacenado el DataFrame mientras la sesión esté activa.
                st.session_state["combined_data"] = combined_data

                st.success("Datos obtenidos correctamente!")
                st.write(combined_data)
                
                
                #**Gráfico 1.1: Evolución del Valor de Mercado Promedio por Temporada**
                st.subheader("Evolución del Valor de Mercado Promedio por Temporada")
                
                marketvalue_season = combined_data.groupby("Season")["Market Value"].mean().reset_index()
                
                #Gráfico de lineas.
                graf11 = px.line(marketvalue_season,
                                x="Season",
                                y="Market Value",
                                labels={"Season": "Temporada", "Market Value": "Valor de Mercado Promedio (€)"},
                                markers=True)
                
                #Controlamos el formato del eje X.
                graf11.update_layout(xaxis=dict(tickmode="array", 
                                                tickvals=marketvalue_season["Season"],
                                                ticktext=marketvalue_season["Season"],  
                                                title="Temporada"))
                
                st.plotly_chart(graf11)


                #**Gráfico 1.2: Distribución de Goles y Asistencias por Jugador**
                st.subheader("Distribución de Goles y Asistencias por Jugador")
                
                #Agrupamos para cada Temporada la suma de los Goles y Asistencias de cada Jugador.
                goles_asistencias = combined_data.groupby(["Player", "Season"])[["Goals", "Assists"]].sum().reset_index()
                #Dentro de esta agrupación creamos la variable 'Total' con la suma de los Goles y Asistencias.
                goles_asistencias["Total"] = goles_asistencias["Goals"] + goles_asistencias["Assists"]
                
                #Seleccionar los 30 jugadores con más Goles y Asistencias.
                top_jugadores = (goles_asistencias.groupby("Player")["Total"].sum().reset_index().sort_values(by="Total", ascending=False).head(30)["Player"])
                
                #Filtrar el DataFrame para incluir solo los jugadores seleccionados
                goles_asistencias_filtered = goles_asistencias[goles_asistencias["Player"].isin(top_jugadores)]
            
                #Ordenar los datos por Season (convertir a numérico temporalmente para ordenarlas temporadas correctamente).
                goles_asistencias_filtered["Season"] = goles_asistencias_filtered["Season"].astype(int)
                goles_asistencias_filtered = goles_asistencias_filtered.sort_values(by=["Season", "Player"])
                goles_asistencias_filtered["Season"] = goles_asistencias_filtered["Season"].astype(str)
                
                #Variable con la descripción detallada que quiero que aparezca al pasar el raton sobre cada barra.
                goles_asistencias_filtered["Desglose"] = ("Goles: " + goles_asistencias_filtered["Goals"].astype(str) +
                                                          ", Asistencias: " + goles_asistencias_filtered["Assists"].astype(str))
                
                #Gráfico de barras.
                graf12 = px.bar(goles_asistencias_filtered,
                               x="Player",
                               y=["Goals", "Assists"],
                               color="Season",  # Colorear por Temporada.
                               labels={"Player": "Jugador", "Season": "Temporada"},
                               barmode="stack",  #Temporadas una encima de otra.
                               hover_name="Desglose",
                               hover_data={"value": False})

                #Editamos el formato de la leyenda y los ejes.
                graf12.update_layout(legend=dict(title="Temporada",
                                                 traceorder="reversed"),
                                     xaxis=dict(title="Jugador"),
                                     yaxis=dict(title="Cantidad"))

                st.plotly_chart(graf12)


                #**Gráfico 1.3: Jugador con Mayor Valor de Mercado por Temporada**
                st.subheader("Jugador con Mayor Valor de Mercado por Temporada")
                
                #Seleccionamos los jugadores con mayor Valor de Mercado para cada Temporada.
                top_marketvalue_players = combined_data.loc[combined_data.groupby("Season")["Market Value"].idxmax()]
                
                #Gráfico de barras.
                graf13 = px.bar(top_marketvalue_players,
                                             x="Season",
                                             y="Market Value",
                                             color="Player",
                                             labels={"Season": "Temporada", "Market Value": "Valor de Mercado (€)", "Player": "Jugador"},
                                             text="Player")
                
                #Quitamos la leyenda y editamos el eje X.
                graf13.update_layout(showlegend=False, 
                                     xaxis=dict(tickmode="array",  
                                                tickvals=top_marketvalue_players["Season"],
                                                ticktext=top_marketvalue_players["Season"],  
                                                title="Temporada"))
                
                st.plotly_chart(graf13)


    #Pasamos al estudio en el que comparamos dos temporadas específicas.
    elif mode == "Examinar dos Temporadas":
        
        st.markdown("### Búsqueda de dos Temporadas Específicas")
        
        season_1 = st.number_input("Primera temporada:", min_value=2005, max_value=2025, value=2010)
        season_2 = st.number_input("Segunda temporada:", min_value=2005, max_value=2025, value=2020)

        if st.button("Scrapear Datos"):
            with st.spinner("Preparando el scraping..."):
                progress_placeholder = st.empty()

                def display(message):
                    progress_placeholder.text(message)

                #Introducimos las dos temporadas a comparar en formato lista como parametro seasons en la funcion principal de scrapeo.
                combined_data = scrape_transfermarkt_data(team, code, [season_1, season_2], display)
                st.session_state["comparison_data"] = combined_data

                st.success(f"Datos obtenidos para las temporadas {season_1} y {season_2}!")
                st.write(combined_data)
                
                
                #**Gráfico 2.1: Jugador con Mayor Impacto (Goles + Asistencias) por Temporada**
                st.subheader("Jugador con Mayor Impacto (Goles + Asistencias)")

                #Para este caso imputamos todos los None a 0 para que los cálculos salgan correctamente.
                combined_data = combined_data.fillna(0)
                
                #Creamos una columna "Total" que combina goles y asistencias
                combined_data["Total"] = combined_data["Goals"] + combined_data["Assists"]

                #Inicializamos un DataFrame vacío para almacenar los jugadores con mayor impacto por temporada.
                top_players_list = []

                #Iteramos las dos temporadas que tenemos.
                for season in combined_data["Season"].unique():
                    
                    #Filtra los datos para la temporada actual
                    season_data = combined_data[combined_data["Season"] == season]
                    #Encuentra el índice del jugador con mayor impacto (Total).
                    top_player_index = season_data["Total"].idxmax()
                    #Agrega el jugador al DataFrame de resultados.
                    top_players_list.append(season_data.loc[top_player_index])
                    
                #Convertimos la lista de jugadores a un DataFrame.
                top_players_by_season = pd.DataFrame(top_players_list)

                #Creamos el gráfico de barras.
                graf21 = px.bar(top_players_by_season,
                                        x="Season",
                                        y="Total",
                                        color="Player",
                                        labels={"Total": "Goles + Asistencias", "Season": "Temporada", "Player": "Jugador"},
                                        text="Player")
                
                #Aumentamos el tamaño del texto que aparece en las barras.
                graf21.update_traces(textfont=dict(size=18), 
                                             textposition="inside")

                #Ajustamos parametros como la leyenda y los ejes.
                graf21.update_layout(showlegend=False,
                                             xaxis=dict(title="Temporada",
                                                        tickmode="array",
                                                        tickvals=top_players_by_season["Season"],
                                                        ticktext=top_players_by_season["Season"]),
                                             yaxis=dict(title="Goles + Asistencias"))
                
                st.plotly_chart(graf21)
                
                
                
                #**Gráfico 2.2: Resumen de tarjetas por temporada**
                st.subheader("Resumen de Tarjetas por Temporada")

                #Creamos una nueva columna para las tarjetas rojas totales.
                combined_data["Red Cards"] = combined_data["Red Cards"].fillna(0) + combined_data["Second Card"].fillna(0)
                combined_data["Yellow Cards"] = combined_data["Yellow Cards"].fillna(0)

                #Se suman las tarjetas amarillas y rojas por temporada.
                tarjetas_totales = combined_data.groupby("Season")[["Yellow Cards", "Red Cards"]].sum().reset_index()

                #Pasamos el DataFrame tarjetas_totales a un formato 'long' (hacia abajo) para que se especifique el tipo de tarjeta y la cantidad como variables.
                tarjetas_totales_long = tarjetas_totales.melt(id_vars="Season", 
                                                              value_vars=["Yellow Cards", "Red Cards"], 
                                                              var_name="Tipo de Tarjeta", 
                                                              value_name="Cantidad")

                #Gráfico de barras con los colores de las tarjetas.
                graf22 = px.bar(tarjetas_totales_long,
                                             x="Season",
                                             y="Cantidad",
                                             color="Tipo de Tarjeta",
                                             labels={"Season": "Temporada", "Cantidad": "Total de Tarjetas", "Tipo de Tarjeta": "Tipo"},
                                             barmode="group",
                                             color_discrete_map={"Yellow Cards": "yellow", "Red Cards": "red"})

                
                graf22.update_layout(legend_title="Tipo de Tarjeta",
                                                  xaxis=dict(title="Temporada"),
                                                  yaxis=dict(title="Cantidad de Tarjetas"))

                st.plotly_chart(graf22)


                #Además calculamos y mostramos en pantalla el jugador con más tarjetas para cada temporada.
                jugador_mas_tarjetas = combined_data.groupby(["Season", "Player"])[["Yellow Cards", "Red Cards"]].sum()

                jugador_mas_tarjetas["Total"] = jugador_mas_tarjetas["Yellow Cards"] + jugador_mas_tarjetas["Red Cards"]
                jugador_mas_tarjetas = jugador_mas_tarjetas.reset_index()

                jugadores_top = jugador_mas_tarjetas.loc[jugador_mas_tarjetas.groupby("Season")["Total"].idxmax()]

                #Mostramos el texto debajo del gráfico.
                st.markdown("### Jugadores con Más Tarjetas por Temporada:")
                for index, row in jugadores_top.iterrows():
                    st.markdown(f"- **Temporada {row['Season']}:** {row['Player']} con {int(row['Total'])} tarjetas ({int(row['Yellow Cards'])} amarillas, {int(row['Red Cards'])} rojas)")
                
                
                # **Gráfico 2.3: Jugador con Mayor Valor de Mercado por Temporada**
                st.subheader("Jugador con Mayor Valor de Mercado por Temporada")

                #Realizamos el mismo proceso que antes pero en este caso para la busqueda del jugador con máyor valor de mercado.
                top_marketvalue_by_season = []

                for season in combined_data["Season"].unique():
                    
                    season_data = combined_data[combined_data["Season"] == season]
                    top_player_index = season_data["Market Value"].idxmax()
                    top_marketvalue_by_season.append(season_data.loc[top_player_index])

                top_marketvalue_by_season = pd.DataFrame(top_marketvalue_by_season)

                graf23 = px.bar(top_marketvalue_by_season,
                                             x="Season",
                                             y="Market Value",
                                             color="Player",
                                             labels={"Season": "Temporada", "Market Value": "Valor de Mercado (€)", "Player": "Jugador"},
                                             text="Player")
                
                graf23.update_traces(textfont=dict(size=18),  
                                     textposition="inside")

                graf23.update_layout(showlegend=False,
                                     xaxis=dict(title="Temporada",
                                                tickmode="array",
                                                tickvals=top_marketvalue_by_season["Season"],
                                                ticktext=top_marketvalue_by_season["Season"]),
                                     yaxis=dict(title="Valor de Mercado (€)"))

                st.plotly_chart(graf23)
                
#Ejecuta la aplicación
if __name__ == "__main__":
    main_app()

