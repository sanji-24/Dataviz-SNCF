import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px


def main():
    menu_options = ["Carte", "Graphiques"]
    choix_menu = st.sidebar.selectbox("Fréquentation des gares :", menu_options)
    st.title("Quelles sont les gares les plus fréquentées ?")

    if choix_menu == "Carte":
        df1 = pd.read_csv("data/liste-des-gares.csv", sep=';')
        df2 = pd.read_csv("data/frequentation-gares.csv", sep=';')

        df1[['Latitude', 'Longitude']] = df1['Geo Point'].str.split(', ', expand=True)
        df1['Latitude'] = df1['Latitude'].astype(float)
        df1['Longitude'] = df1['Longitude'].astype(float)

        columns_to_keep = ['CODE_UIC','LIBELLE','COMMUNE','DEPARTEMEN','Latitude','Longitude']
        df1 = df1[columns_to_keep]

        columns_to_keep = ['Nom de la gare','Code UIC','Code postal','Segmentation DRG','Total Voyageurs 2022','Total Voyageurs 2021','Total Voyageurs 2020','Total Voyageurs 2019','Total Voyageurs 2018','Total Voyageurs 2017','Total Voyageurs 2016','Total Voyageurs 2015']
        df2 = df2[columns_to_keep]

        df = pd.merge(df2, df1, left_on='Code UIC', right_on='CODE_UIC', how='inner')
        center=[df1.Latitude.mean(), df1.Longitude.mean()]
        df['Nombre de gares'] = 1

        map = folium.Map(location=center, zoom_start=6, control_scale=True)

        on = st.toggle('Vision Détails Gares')
        
        annee = st.slider('Année', 2015, 2022)
        data1=df
        data1['Total Voyageurs'] = data1[f'Total Voyageurs {annee}']

        categ = st.radio('Nombre de Voyageurs',('Tous','Peu','Moyen','Beaucoup'))
        purpose_colour = {'0':'lightblue', '1':'blue', '2':'darkblue'}

        segmentation = st.selectbox('Type de gare',['Tous types de gares','Gares de voyageurs d’intérêt national','Gares de voyageurs d’intérêt régional','Gares de voyageurs d’intérêt local'])
        data2=data1
        if segmentation == 'Gares de voyageurs d’intérêt national':
            data2 = data2[data2['Segmentation DRG'] == 'A']
        elif segmentation == 'Gares de voyageurs d’intérêt régional':
            data2 = data2[data2['Segmentation DRG'] == 'B']
        elif segmentation == 'Gares de voyageurs d’intérêt local':
            data2 = data2[data2['Segmentation DRG'] == 'C']
        else:
            data2=data1

        col1, col2 = st.columns(2)

        if on:
            data3=data2
            data3['Total Voyageurs'] = data3['Total Voyageurs'].astype(int)
            data3['Catégorie'] = pd.qcut(data3['Total Voyageurs'], 3, labels=False)
            data3["Catégorie"] = data3["Catégorie"].astype(str)

            data4=data3
            if categ == 'Peu':
                data4=data4[(data4['Catégorie']== '0')]
            elif categ == 'Moyen':
                data4=data4[(data4['Catégorie']== '1')]
            elif categ == 'Beaucoup':
                data4=data4[(data4['Catégorie']== '2')]
            else:
                data4=data3
            
            col1.metric("Nombre de Gares", len(data4))
            col2.metric("Nombre de Voyageurs", sum(data4['Total Voyageurs']))

            for i,row in data4.iterrows():
                content = f'Département: {str(row["DEPARTEMEN"])}<br>' f'Gare: {str(row["Nom de la gare"])}<br>' f'Total Voyageurs: {str(row["Total Voyageurs"])}'
                iframe = folium.IFrame(content, width=400, height=100)
                popup = folium.Popup(iframe, min_width=400, max_width=400)
            
                try:
                    icon_color = purpose_colour[row['Catégorie']]
                except:
                    icon_color = 'gray'
            
                folium.Marker(location=[row['Latitude'],row['Longitude']],
                            popup = popup, 
                            icon=folium.Icon(color=icon_color, icon='')).add_to(map)

        else:
            data3=data2
            data3=data3.groupby('DEPARTEMEN').agg({
            'Longitude': 'mean',
            'Latitude': 'mean',
            'Total Voyageurs': 'sum',
            'Nombre de gares': 'sum'
            }).reset_index()

            data3['Total Voyageurs'] = data3['Total Voyageurs'].astype(int)
            data3['Catégorie'] = pd.qcut(data3['Total Voyageurs'], 3, labels=False)
            data3["Catégorie"] = data3["Catégorie"].astype(str)

            data4=data3
            if categ == 'Small':
                data4=data4[(data4['Catégorie']== '0')]
            elif categ == 'Medium':
                data4=data4[(data4['Catégorie']== '1')]
            elif categ == 'Large':
                data4=data4[(data4['Catégorie']== '2')]
            else:
                data4=data3
            
            col1.metric("Nombre de Gares", sum(data4['Nombre de gares']))
            col2.metric("Nombre de Voyageurs", sum(data4['Total Voyageurs']))

            for i,row in data4.iterrows():
                content = f'Département: {str(row["DEPARTEMEN"])}<br>' f'Total Voyageurs: {str(row["Total Voyageurs"])}<br>' f'Nombre de Gares: {str(row["Nombre de gares"])}'
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
        liste_des_gares = pd.read_csv('data/liste-des-gares.csv', sep=';')
        frequentation_gares = pd.read_csv('data/frequentation-gares.csv', sep=';')
        frequentation_gares = frequentation_gares.rename(columns={'Code UIC': 'CODE_UIC', 'Nom de la gare': 'Gare'})

        def map_segmentation_drg(segment):
            if segment == 'A':
                return 'Gares d\'intérêt national'
            elif segment == 'B':
                return 'Gares d\'intérêt régional'
            else: 
                return 'Gares d\'intérêt local'
            

        frequentation_gares['Segmentation DRG Nouveau'] = frequentation_gares['Segmentation DRG'].map(map_segmentation_drg)
        frequentation_gares['Taux de Croissance'] = (frequentation_gares['Total Voyageurs 2022'] - frequentation_gares['Total Voyageurs 2021']) / frequentation_gares['Total Voyageurs 2021'] * 100

        fig = px.bar(
            frequentation_gares,
            x='Segmentation DRG Nouveau',
            y='Taux de Croissance',
            title='Taux de Croissance des Voyageurs par Segmentation DRG',
            labels={'Segmentation DRG Nouveau': 'Segmentation DRG', 'Taux de Croissance': 'Taux de Croissance (%)'},
            color_discrete_sequence=['#2E8B57'],
        )
        fig.update_layout(xaxis_title='Segmentation DRG', yaxis_title='Taux de Croissance')

        st.plotly_chart(fig)

        frequentation_gares['Segmentation DRG Nouveau'] = frequentation_gares['Segmentation DRG'].map(map_segmentation_drg)
        average_frequentation = frequentation_gares.groupby('Segmentation DRG Nouveau')['Total Voyageurs 2022'].mean().reset_index()
        average_frequentation = average_frequentation.sort_values(by='Total Voyageurs 2022', ascending=False)

        fig = px.bar(
            average_frequentation,
            x='Segmentation DRG Nouveau',
            y='Total Voyageurs 2022',
            title='Fréquentation Moyenne par Segmentation DRG',
            labels={'Total Voyageurs 2022': 'Fréquentation Moyenne'},
            color_discrete_sequence=['#2E8B57'],
        )

        st.plotly_chart(fig)
        
        ### PARTIE POUR LES FLUX ###

        liste_des_gares = pd.read_csv('data/liste-des-gares.csv', sep=';')
        frequentation_gares = pd.read_csv('data/frequentation-gares.csv', sep=';')
        frequentation_gares = frequentation_gares.rename(columns={'Code UIC': 'CODE_UIC', 'Nom de la gare': 'Gare'})
        frequentation_gares['Taux de Croissance'] = (frequentation_gares['Total Voyageurs 2022'] - frequentation_gares['Total Voyageurs 2021']) / frequentation_gares['Total Voyageurs 2021'] * 100

        merged_data = pd.merge(frequentation_gares, liste_des_gares[['CODE_UIC', 'DEPARTEMEN']], on='CODE_UIC', how='left')
        gares_augmentation_significative = merged_data[merged_data['Taux de Croissance'] > 10]
        departements_uniques = liste_des_gares['DEPARTEMEN'].unique()
        departements_uniques.sort()
        selected_departement = st.sidebar.selectbox("Sélectionnez un département :", departements_uniques)

        gares_departement = gares_augmentation_significative[gares_augmentation_significative['DEPARTEMEN'] == selected_departement]
        gares_departement = gares_departement.sort_values(by='Taux de Croissance', ascending=False)

        result_df = gares_departement.groupby('Gare').first().reset_index()

        st.header("Augmentation significative du nombre de voyageurs dans le département : {}".format(selected_departement)) 
        st.subheader("Liste des gares (taux de croissance > 10%):")
        st.write(result_df[['Gare', 'Taux de Croissance']])

        fig = px.bar(result_df, x='Gare', y='Taux de Croissance', title='Taux de Croissance des Voyageurs par Gare')
        fig.update_layout(xaxis_title='Gare', yaxis_title='Taux de Croissance (%)')

        st.plotly_chart(fig)

        ### Identification des heures de pointe et heures creuses ###
        
        horaires_gares = pd.read_csv('data/horaires-des-gares.csv', sep=';')
        frequentation_gares = pd.read_csv('data/frequentation-gares.csv', sep=';')
        liste_des_gares = pd.read_csv('data/liste-des-gares.csv', sep=';')

        frequentation_gares = frequentation_gares.rename(columns={'Code UIC': 'UIC', 'Nom de la gare': 'Gare'})
        liste_des_gares = liste_des_gares.rename(columns={'CODE_UIC': 'UIC', 'DEPARTEMEN': 'Departement'})

        merged_data = pd.merge(horaires_gares, frequentation_gares[['UIC', 'Gare', 'Total Voyageurs 2022']], on='Gare', how='left')
        merged_data = pd.merge(merged_data, liste_des_gares[['UIC', 'Departement']], on='UIC', how='left')

        merged_data['Heure'] = merged_data['Horaire en jour normal'].str.extract('(\d{2}:\d{2})')
        merged_data['Heure'] = pd.to_datetime(merged_data['Heure'], format='%H:%M', errors='coerce').dt.hour

        filtered_data = merged_data[merged_data['Departement'] == selected_departement]

        fig_heatmap = px.imshow(
            filtered_data.pivot_table(index='Jour de la semaine', columns='Heure', values='Total Voyageurs 2022', aggfunc='mean'),
            labels=dict(x="Heure de la journée", y="Jour de la semaine", color="Total Voyageurs 2022"),
            title=f'Identification des heures de pointe et heures creuses - Département {selected_departement}',
            color_continuous_scale='Viridis',
        )

        fig_heatmap.update_xaxes(tickvals=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
                                ticktext=['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'])

        st.plotly_chart(fig_heatmap)


if __name__ == "__main__":
    main()
