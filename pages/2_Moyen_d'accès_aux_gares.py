import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px


def main():
    menu_options = ["Carte", "Graphiques"]
    choix_menu = st.sidebar.selectbox("Fréquentation des gares :", menu_options)
    st.title("Quelles aménagements faudrait-il faire dans les gares ?")

    if choix_menu == "Carte":
        df1 = pd.read_csv("data/liste-des-gares.csv", sep=';')
        df2 = pd.read_csv("data/repartition-des-moyens-dacces.csv", sep=';')

        df1[['Latitude', 'Longitude']] = df1['Geo Point'].str.split(', ', expand=True)
        df1['Latitude'] = df1['Latitude'].astype(float)
        df1['Longitude'] = df1['Longitude'].astype(float)

        columns_to_keep = ['CODE_UIC','LIBELLE','COMMUNE','DEPARTEMEN','Latitude','Longitude']
        df1 = df1[columns_to_keep]
        df1['CODE_UIC'] = df1['CODE_UIC'].apply(lambda x: str(x)[-6:])

        columns_to_keep = ['UIC','Gare enquêtée','Gpe intermodalités usagers','Répartition']
        df2 = df2[columns_to_keep]
        df2['UIC'] = df2['UIC'].astype(str)
        df2['UIC'] = df2['UIC'].apply(lambda x: str(x)[:6])

        df = pd.merge(df2, df1, left_on='UIC', right_on='CODE_UIC', how='inner')
        center=[df1.Latitude.mean(), df1.Longitude.mean()]
        df = df.dropna(subset=['Répartition'])
        df = df.drop_duplicates(subset=['UIC','Gpe intermodalités usagers'])
        nombre_total = sum(df['Répartition'])

        map = folium.Map(location=center, zoom_start=6, control_scale=True)

        moyen = st.selectbox('Moyen de transport',['Voiture / Moto','Bus / Car / Navette','Métro / RER / Tramway','Vélo','Marche'])
        data1=df
        if moyen == 'Voiture / Moto':
            allowed_values = ['2 roues motorisées', 'Autres voitures (location, autopartage)', 'Taxis', 'Voiture conducteur', 'Voiture passager']
            data1 = data1[data1['Gpe intermodalités usagers'].isin(allowed_values)]
        elif moyen == 'Bus / Car / Navette':
            data1 = data1[data1['Gpe intermodalités usagers'] == 'Bus/Car/Navette']
        elif moyen == 'Métro / RER / Tramway':
            data1 = data1[(data1['Gpe intermodalités usagers'] == 'Métro / RER') | 
            (data1['Gpe intermodalités usagers'] == 'Tramway')]
        elif moyen == 'Vélo':
            data1 = data1[data1['Gpe intermodalités usagers'] == 'Vélo']
        elif moyen == 'Marche':
            data1 = data1[data1['Gpe intermodalités usagers'] == 'Marche']
        else:
            data1=df

        categ = st.radio('Taux de Répartition',('Tous','Faible','Moyen','Elevée'))

        col1, col2 = st.columns(2)

        data2=data1
        data2['Répartition'] = data2['Répartition'].astype(int)
        data2['Catégorie'] = pd.qcut(data2['Répartition'], 3, labels=False)
        data2["Catégorie"] = data2["Catégorie"].astype(str)
        purpose_colour = {'0':'lightblue', '1':'blue', '2':'darkblue'}

        data3=data2
        if categ == 'Faible':
            data3=data3[(data3['Catégorie']== '0')]
        elif categ == 'Moyen':
            data3=data3[(data3['Catégorie']== '1')]
        elif categ == 'Elevée':
            data3=data3[(data3['Catégorie']== '2')]
        else:
            data3=data2
            
        col1.metric("Nombre de Gares", data3['UIC'].nunique())
        rounded_value = round(sum(data3['Répartition'])/nombre_total*100, 2)
        formatted_value = "{:.2f}%".format(rounded_value)
        col2.metric("Taux de Répartition Globale", formatted_value)

        for i,row in data3.iterrows():
            content = f'Département: {str(row["DEPARTEMEN"])}<br>' f'Gare: {str(row["Gare enquêtée"])}<br>' f'Répartition: {str(row["Répartition"])}'f'%'
            iframe = folium.IFrame(content, width=400, height=100)
            popup = folium.Popup(iframe, min_width=400, max_width=400)
            
            try:
                icon_color = purpose_colour[row['Catégorie']]
            except:
                icon_color = 'gray'
            
            folium.Marker(location=[row['Latitude'],row['Longitude']],
                        popup = popup, 
                        icon=folium.Icon(color=icon_color, icon='')).add_to(map)

        st_data = st_folium(map, width=800)


    elif choix_menu == "Graphiques":
        moyens_acces = pd.read_csv('data/repartition-des-moyens-dacces.csv', sep=';')
        fig_moyens_acces = px.pie(moyens_acces, names='Gpe intermodalités usagers', title='Répartition des Moyens d\'Accès aux Gares')
        
        st.plotly_chart(fig_moyens_acces)

        distances_acces = pd.read_csv('data/repartition-des-distances-dacces.csv', sep=';')
        distances_acces = distances_acces.sort_values(by='Distance parcourue', ascending=False)

        fig_distances_acces = px.bar(
            distances_acces,
            x='Répartition',
            y='Distance parcourue',
            orientation='h',
            title='Répartition des Distances d\'Accès à la Gare',
            labels={'Répartition': 'Répartition', 'Distance parcourue': 'Distance parcourue'},
            color_discrete_sequence=['#2E8B57']
        )

        fig_distances_acces = fig_distances_acces.update_xaxes(categoryorder='total descending')
        st.plotly_chart(fig_distances_acces)

        ### Répartition des Retards ###
        
        regularite_tgv = pd.read_csv('data/regularite-mensuelle-tgv-aqst.csv', sep=';')
        regularite_tgv['Date'] = pd.to_datetime(regularite_tgv['Date'], format='%Y-%m')
        regularite_tgv['Mois'] = regularite_tgv['Date'].dt.strftime('%Y-%m')
        regularite_tgv['Pourcentage Retard'] = (regularite_tgv['Nombre trains en retard > 15min'] / regularite_tgv['Nombre de circulations prévues']) * 100

        available_years = regularite_tgv['Date'].dt.year.unique()
        selected_year = st.sidebar.selectbox('Choisir une année', available_years)

        filtered_data = regularite_tgv[regularite_tgv['Date'].dt.year == selected_year]
        selected_causes = st.sidebar.multiselect('Choisir la cause du retard', regularite_tgv.columns[22:29])
        selected_causes = [cause for cause in selected_causes if cause not in ['Mois', 'Pourcentage Retard']]

        if selected_causes:
            filtered_data = filtered_data[['Mois', 'Pourcentage Retard'] + selected_causes]
        else:
            filtered_data = filtered_data[['Mois', 'Pourcentage Retard']]

        fig_retards_par_cause = px.bar(filtered_data, x='Mois', y=selected_causes,
                               title=f'Répartition des Retards par Cause pour {selected_year}',
                               labels={'value': 'Pourcentage de Retard', 'variable': 'Cause'},
                               color_discrete_map={'variable': 'darkblue'})

        fig_retards_par_cause.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

        st.plotly_chart(fig_retards_par_cause)


if __name__ == "__main__":
    main()
