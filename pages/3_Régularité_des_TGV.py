import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px


def main():
    menu_options = ["Carte", "Graphiques"]
    choix_menu = st.sidebar.selectbox("Fréquentation des gares :", menu_options)
    st.title("Où faudrait-il améliorer le flux ferroviaire ?")

    if choix_menu == "Carte":
        df1 = pd.read_csv("data/liste-des-gares.csv", sep=';')
        df2 = pd.read_csv("data/regularite-mensuelle-intercites.csv", sep=';')

        df1[['Latitude', 'Longitude']] = df1['Geo Point'].str.split(', ', expand=True)
        df1['Latitude'] = df1['Latitude'].astype(float)
        df1['Longitude'] = df1['Longitude'].astype(float)

        columns_to_keep = ['CODE_UIC','LIBELLE','COMMUNE','DEPARTEMEN','Latitude','Longitude']
        df1 = df1[columns_to_keep]
        df1['Gare'] = df1['LIBELLE'].str.upper()

        df2['Année'] = df2['Date'].apply(lambda x: int(x[:4]))
        df2["Nombre de trains en retard"] = df2["Nombre de trains en retard à l'arrivée"]
        df2=df2.groupby(['Départ','Arrivée','Année']).agg({
        'Nombre de trains programmés': 'sum',
        'Nombre de trains ayant circulé': 'sum',
        'Nombre de trains annulés': 'sum',
        "Nombre de trains en retard": 'sum',
        'Taux de régularité': 'mean'
        }).reset_index()
        df2 = df2.sort_values(by='Année', ascending=False)
        df2 = df2.groupby(['Départ', 'Arrivée']).head(1)
        df2 = df2.dropna(subset=['Année'])
        df2['Taux de régularité'] = round(df2['Taux de régularité'], 2)

        df = pd.merge(df2, df1, left_on='Départ', right_on='Gare', how='inner')
        center=[df1.Latitude.mean(), df1.Longitude.mean()]
        df = df.drop_duplicates(subset=['Départ','Arrivée','Année'])

        map = folium.Map(location=center, zoom_start=6, control_scale=True)

        train1 = st.selectbox('Nombre de trains',['Tous','Programmés','Annulés','En Retard'])
        data1=df
        train2=train1.lower()
        if train1 == "Tous":
            data1=df
            categ = st.radio('Taux de régularité',('Tous','Mauvais','Moyen','Bon'))
            variable = 'Taux de régularité'
        else:
            data1['Nombre de trains'] = data1[f'Nombre de trains {train2}']
            categ = st.radio(f'Nombre de trains {train2}',('Tous','Peu','Moyen','Beaucoup'))
            variable = f'Nombre de trains {train2}'

        col1, col2, col3, col4, col5 = st.columns(5)

        data2=data1
        data2[variable] = data2[variable].astype(int)
        data2['Catégorie'] = pd.qcut(data2[variable], 3, labels=False)
        data2["Catégorie"] = data2["Catégorie"].astype(str)
        purpose_colour = {'0':'lightblue', '1':'blue', '2':'darkblue'}

        data3=data2
        if categ == 'Bon' or categ == 'Peu':
            data3=data3[(data3['Catégorie']== '0')]
        elif categ == 'Moyen' or categ == 'Moyen':
            data3=data3[(data3['Catégorie']== '1')]
        elif categ == 'Mauvais' or categ == 'Beaucoup':
            data3=data3[(data3['Catégorie']== '2')]
        else:
            data3=data2
            
        col1.metric('Lignes de TGV', len(data3))
        col2.metric("Trains programmés", int(sum(data3['Nombre de trains programmés'])))
        col3.metric("Trains annulés", int(sum(data3['Nombre de trains annulés'])))
        col4.metric("Trains en retard", int(sum(data3['Nombre de trains en retard'])))
        rounded_value = round((data3['Taux de régularité'].mean()), 2)
        formatted_value = "{:.2f}%".format(rounded_value)
        col5.metric("Régularité globale", formatted_value)

        for i,row in data3.iterrows():
            content = f'Département: {str(row["DEPARTEMEN"])}<br>' f'Gare: {str(row["LIBELLE"])}<br>' f'Trains programmés: {str(row["Nombre de trains programmés"])}<br>' f'Trains annulés: {str(row["Nombre de trains annulés"])}<br>' f'Trains en retard: {str(row["Nombre de trains en retard"])}<br>' f'Régularité: {str(row["Taux de régularité"])}' f'%'
            iframe = folium.IFrame(content, width=400, height=150)
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

        ### Les gares à améliorer ###

        st.header("Les gares à améliorer")
        intercites_data = pd.read_csv('data/regularite-mensuelle-intercites.csv', sep=';')
        tgv_data = pd.read_csv('data/regularite-mensuelle-tgv-aqst.csv', sep=';')

        gares_intercites = set(intercites_data['Départ']).union(set(intercites_data['Arrivée']))
        gares_tgv = set(tgv_data['Gare de départ']).union(set(tgv_data['Gare d\'arrivée']))
        gares_communes = gares_intercites.intersection(gares_tgv)

        intercites_data['Amelioration'] = intercites_data['Nombre de trains en retard à l\'arrivée'] + intercites_data['Nombre de trains annulés']
        tgv_data['Amelioration'] = tgv_data['Nombre de trains en retard à l\'arrivée'] + tgv_data['Nombre de trains annulés']

        gares_amelioration_intercites = intercites_data.groupby(['Départ', 'Arrivée'])['Amelioration'].sum().reset_index()
        gares_amelioration_tgv = tgv_data.groupby(['Gare de départ', 'Gare d\'arrivée'])['Amelioration'].sum().reset_index()

        gares_amelioration_intercites = gares_amelioration_intercites[gares_amelioration_intercites['Amelioration'] > 0]
        gares_amelioration_tgv = gares_amelioration_tgv[gares_amelioration_tgv['Amelioration'] > 0]

        gares_amelioration_intercites['Amelioration'] = gares_amelioration_intercites['Amelioration'].astype(str).str.replace(',', '')
        gares_amelioration_tgv['Amelioration'] = gares_amelioration_tgv['Amelioration'].astype(str).str.replace(',', '')

        st.header("Gares à améliorer pour réduire les retards et annulations")
        st.write("Gares à améliorer pour le service Intercités :")
        st.write(gares_amelioration_intercites[['Départ', 'Arrivée', 'Amelioration']])

        st.write("Gares à améliorer pour le service TGV :")
        st.write(gares_amelioration_tgv[['Gare de départ', 'Gare d\'arrivée', 'Amelioration']])


        ### Les gares avec le plus de problèmes de régularité ###

        st.header("Les gares avec le plus de problèmes de régularité")
        regularite_tgv = pd.read_csv('data/regularite-mensuelle-tgv-aqst.csv', sep=';')
        regularite_tgv['Année'] = regularite_tgv['Date'].str[:4]
        selected_service = st.sidebar.selectbox("Sélectionnez un service :", regularite_tgv['Service'].unique())
        filtered_data = regularite_tgv[regularite_tgv['Service'] == selected_service]

        filtered_data['Catégorie Retard'] = pd.cut(filtered_data['Retard moyen trains en retard > 15 (si liaison concurrencée par vol)'],
                                                bins=[-float('inf'), 15, 30, 60, float('inf')],
                                                labels=['<15 min', '15-30 min', '30-60 min', '>60 min'])

        filtered_data['Catégorie Annulation'] = filtered_data['Nombre de trains annulés'].apply(lambda x: 'Non annulé' if x == 0 else 'Annulé')
        selected_year = st.sidebar.selectbox("Sélectionnez une année :", filtered_data['Année'].unique())
        filtered_data = filtered_data[filtered_data['Année'] == selected_year]

        selected_category = st.sidebar.radio("Sélectionnez une catégorie :", ['Retard', 'Annulation'])

        if selected_category == 'Retard':
            selected_minute_range = st.sidebar.selectbox("Sélectionnez une plage de minutes :", ['<15 min', '15-30 min', '30-60 min', '>60 min'])
            filtered_data = filtered_data[filtered_data['Catégorie Retard'] == selected_minute_range]

        elif selected_category == 'Annulation':
            selected_annulation_category = st.sidebar.selectbox("Sélectionnez une catégorie d'annulation :", ['Non annulé', 'Annulé'])
            filtered_data = filtered_data[filtered_data['Catégorie Annulation'] == selected_annulation_category]

        if selected_category == 'Retard':
            filtered_data = filtered_data.sort_values(by='Retard moyen trains en retard > 15 (si liaison concurrencée par vol)', ascending=False)
        else:
            filtered_data = filtered_data.sort_values(by='Nombre de trains annulés', ascending=False)

        top_10_gares = filtered_data.head(10)

        fig = px.bar(top_10_gares,
                    x='Gare de départ',
                    y='Nombre de trains annulés' if selected_category == 'Annulation' else 'Retard moyen trains en retard > 15 (si liaison concurrencée par vol)',
                    title=f'Top 10 des gares avec le plus de problèmes de {selected_category} en {selected_service} pour l\'année {selected_year}',
                    labels={'Retard moyen trains en retard > 15 (si liaison concurrencée par vol)': 'Retard moyen (minutes)'},
                    color='Gare d\'arrivée')

        fig.update_layout(height=500, width=750)
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.5, xanchor="right", x=1))
        st.plotly_chart(fig)


if __name__ == "__main__":
    main()
