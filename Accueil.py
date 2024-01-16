import streamlit as st

CURRENT_THEME = "blue"
IS_DARK_THEME = True

st.title('Application SNCF')

st.image("image/sncf.png", width=100, use_column_width=False, clamp=True)

st.header("Comment inciter les utilisateurs à favoriser les moyens de transport ?")

st.subheader("Bienvenue")

st.write("Notre application dédiée à la SNCF simplifie la prise de décision en fournissant des données précises sur les gares les plus fréquentées, facilitant ainsi une gestion efficace des flux de passagers.")

st.write("Grâce à une analyse approfondie du flux ferroviaire, notre application identifie les points d'amélioration clés, permettant à la SNCF de prendre des décisions éclairées pour renforcer l'efficacité opérationnelle du réseau ferroviaire.")

st.write("Nous allons répondre à ses questions :")

st.write("1) Quelles sont les gares les plus fréquentées ?")

st.write("2) Quelles aménagements faudrait-il faire dans les gares ?")

st.write("3) Où faudrait-il améliorer le flux ferroviaire ?")

st.divider()

st.write("N'hésitez pas à explorer notre application pour trouver des pistes d'optimisation les infrastructures et améliorer l'expérience des voyageurs.")
