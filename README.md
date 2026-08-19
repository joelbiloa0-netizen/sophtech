# SophTech — Chatbot IA de culture générale informatique

SophTech est un chatbot conversationnel spécialisé en culture générale informatique et numérique : matériel, logiciels, internet, cybersécurité, intelligence artificielle, histoire de la tech et métiers du numérique. Il adopte un ton de vulgarisateur : des explications claires, des exemples concrets, sans manuel technique.

Ce projet est le 3e du portfolio Data Science & IA (MyLab AI).

## Fonctionnalités

- Chat conversationnel complet (Streamlit `chat_message` / `chat_input`)
- 3 niveaux d'explication : Débutant, Intermédiaire, Expert — le choix s'applique uniquement aux prochaines réponses, sans modifier l'historique
- 4 questions suggérées affichées avant le premier message de la session
- Bouton "Nouvelle conversation" pour repartir de zéro
- Gestion d'erreurs gracieuse : clé API manquante ou invalide, timeout, rate limit (le message utilisateur reçoit toujours une réponse visible dans le chat)

## Stack technique

- Python + Streamlit
- API Groq (package officiel `groq`)
- Modèle : `openai/gpt-oss-120b` (gratuit sur Groq, inférence rapide)
- Clé API lue depuis `st.secrets["GROQ_API_KEY"]` — jamais de clé en dur dans le code

## Prérequis

- Python 3.10 ou supérieur
- Un compte Groq et une clé API gratuite ([console.groq.com/keys](https://console.groq.com/keys))

## Installation

1. Créer et activer l'environnement virtuel :

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. Installer les dépendances :

   ```powershell
   pip install -r requirements.txt
   ```

3. Configurer la clé API :

   ```powershell
   Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
   ```

   Puis remplacer `votre_cle_api_groq_ici` par la vraie clé dans `.streamlit/secrets.toml`.

## Lancement local

```powershell
streamlit run app.py
```

L'application s'ouvre sur http://localhost:8501.

## Déploiement cloud (Streamlit Community Cloud)

1. Pousser le projet sur un dépôt GitHub (public ou privé accessible au service), en incluant `.streamlit/secrets.toml.example` et en excluant `.streamlit/secrets.toml` (déjà géré par le `.gitignore`).
2. Dans le dashboard [Streamlit Community Cloud](https://share.streamlit.io), cliquer sur "New app", sélectionner le dépôt, la branche (principale) et le fichier principal `app.py`.
3. Dans les paramètres de l'app, ouvrir l'onglet "Secrets" et ajouter :

   ```toml
   GROQ_API_KEY = "votre_cle_api_groq"
   ```

4. L'app se déploie automatiquement ; chaque push sur la branche principale déclenche une mise à jour.

## Structure du projet

```
sophtech/
├── app.py                          # application principale (chat, niveaux, suggestions, appels API)
├── requirements.txt                # dépendances : streamlit, groq
├── .gitignore                      # exclut secrets.toml, .venv, __pycache__…
├── .streamlit/
│   ├── secrets.toml                # clé API réelle (jamais commité)
│   └── secrets.toml.example        # modèle versionné avec un placeholder
└── README.md
```

## Bonne pratique sécurité

La vraie clé API ne doit jamais être commitée : elle vit uniquement dans `.streamlit/secrets.toml` (ignoré par Git) ou dans les secrets du déploiement cloud. Seul `.streamlit/secrets.toml.example` est versionné.

## Remarques

Le tier gratuit de Groq peut renvoyer des rate limits en cas d'usage intensif. L'application gère ce cas en affichant une réponse d'erreur côté assistant : "Le service est momentanément indisponible, réessaie dans quelques instants."