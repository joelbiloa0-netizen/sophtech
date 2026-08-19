"""
SophTech — Chatbot IA de culture générale informatique
=======================================================
Projet 3 — Portfolio Data Science & IA (MyLab AI)

Stack : Python + Streamlit + API Groq (modèle openai/gpt-oss-120b)
Rôle  : répondre aux questions de culture informatique / numérique / tech
        (matériel, logiciels, internet, cybersécurité, IA, histoire de la
        tech, métiers du numérique) avec un ton de vulgarisateur.
"""

import groq
import streamlit as st
from groq import Groq

# ---------------------------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SophTech",
    page_icon="💻",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Initialisation de l'état de session
# ---------------------------------------------------------------------------
# "messages" : historique du chat (liste de dicts {role, content},
#              rôles "user"/"assistant" UNIQUEMENT, le system prompt
#              n'y est jamais stocké).
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# "niveau" : niveau d'explication choisi (appliqué aux prochaines réponses).
if "niveau" not in st.session_state:
    st.session_state["niveau"] = "Débutant"

# ---------------------------------------------------------------------------
# Vérification de la clé API (présence dans les secrets Streamlit)
# ---------------------------------------------------------------------------
if "GROQ_API_KEY" not in st.secrets:
    st.error(
        "Clé API Groq manquante. Copie le fichier `.streamlit/secrets.toml.example` "
        "vers `.streamlit/secrets.toml` et renseigne ta clé `GROQ_API_KEY`."
    )
    st.stop()  # arrêt propre de l'app, pas de crash

# Client Groq (initialisé une seule fois, au niveau du module)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
# Questions suggérées affichées uniquement avant le premier message.
QUESTIONS_SUGGEREES = [
    "C'est quoi le cloud ?",
    "IA vs Machine Learning : quelle différence ?",
    "Comment fonctionne un CPU ?",
    "C'est quoi la cybersécurité ?",
]

# Texte du niveau d'explication injecté dans le system prompt.
PROMPTS_NIVEAU = {
    "Débutant": (
        "explique comme à quelqu'un qui découvre le sujet, évite tout jargon "
        "technique, utilise des analogies simples"
    ),
    "Intermédiaire": (
        "tu peux utiliser du vocabulaire technique courant, mais explique les "
        "termes moins connus"
    ),
    "Expert": "tu peux être précis et technique, la personne a des bases solides",
}


# ---------------------------------------------------------------------------
# Fonctions
# ---------------------------------------------------------------------------
def construire_system_prompt(niveau: str) -> str:
    """Construit le system prompt SophTech selon le niveau choisi."""
    return (
        "Tu es SophTech, un assistant expert en culture générale informatique et "
        "numérique (matériel, logiciels, internet, cybersécurité, intelligence "
        "artificielle, histoire de la tech, métiers du numérique). Tu expliques de "
        "façon claire et accessible, avec des exemples concrets, sans jargon "
        f"inutile. Adapte ton niveau d'explication : {PROMPTS_NIVEAU[niveau]}. "
        "Si la question posée n'a AUCUN rapport avec l'informatique ou le numérique, "
        "réponds poliment que ce n'est pas ton domaine et invite à reformuler autour "
        "de la tech."
    )


def traiter_question(question: str) -> None:
    """
    Ajoute la question à l'historique, appelle l'API Groq et ajoute la réponse.

    Utilisé à la fois par le chat_input et par les boutons de suggestions,
    afin que les deux chemins se comportent exactement de la même façon.
    Un message est TOUJOURS ajouté à l'historique (réussite ou erreur),
    ce qui garantit que les boutons de suggestions ne réapparaissent jamais.
    """
    # 1. Ajout de la question de l'utilisateur à l'historique
    st.session_state["messages"].append({"role": "user", "content": question})

    # 2. Construction du system prompt avec le niveau sélectionné
    #    (le changement de niveau s'applique uniquement aux prochaines réponses,
    #    l'historique déjà affiché n'est pas modifié).
    system_prompt = construire_system_prompt(st.session_state["niveau"])

    # 3. Appel API : system prompt en PREMIER message de la liste,
    #    suivi de l'historique complet (rôles user/assistant).
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "system", "content": system_prompt}]
            + st.session_state["messages"],
        )
        reponse = completion.choices[0].message.content
        st.session_state["messages"].append({"role": "assistant", "content": reponse})

    # Clé invalide / expirée : réponse d'erreur visible dans le chat
    # (st.error() seul disparaîtrait au rerun suivant, le message utilisateur
    # resterait alors sans réponse visible).
    except groq.AuthenticationError:
        st.session_state["messages"].append(
            {
                "role": "assistant",
                "content": "⚠️ Erreur d'authentification avec l'API Groq — "
                "vérifie ta clé dans les secrets.",
            }
        )

    # Autres erreurs (timeout, rate limit — fréquent sur le tier gratuit —
    # connexion, etc.) : même logique, texte différent pour distinguer la cause.
    except Exception:
        st.session_state["messages"].append(
            {
                "role": "assistant",
                "content": "Le service est momentanément indisponible, "
                "réessaie dans quelques instants.",
            }
        )

    # 4. Rerun : actualise le chat ET masque définitivement les suggestions
    #    (l'historique n'est plus vide).
    st.rerun()


# ---------------------------------------------------------------------------
# Barre latérale : niveau d'explication + nouvelle conversation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Paramètres")

    # Le widget conserve le choix dans st.session_state["niveau"] (via key).
    st.radio(
        "Niveau d'explication",
        options=["Débutant", "Intermédiaire", "Expert"],
        key="niveau",
        help="S'applique aux prochaines réponses, sans modifier l'historique.",
    )

    # Bouton "Nouvelle conversation" : vide l'historique et relance l'app.
    if st.button("🔄 Nouvelle conversation", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

    # Rappel de la configuration courante
    st.divider()
    st.caption(f"Modèle : openai/gpt-oss-120b\nNiveau : {st.session_state['niveau']}")

# ---------------------------------------------------------------------------
# En-tête de l'application
# ---------------------------------------------------------------------------
st.title("SophTech — Culture générale informatique")
st.caption(
    "Pose ta question : matériel, logiciels, internet, cybersécurité, "
    "intelligence artificielle, histoire de la tech, métiers du numérique…"
)

# ---------------------------------------------------------------------------
# Questions suggérées (UNIQUEMENT tant que l'historique est vide)
# ---------------------------------------------------------------------------
# Condition strictement identique au test d'affichage de l'historique :
# dès que le premier message (réponse comprise) est ajouté, ces boutons
# disparaissent pour toute la session.
if not st.session_state["messages"]:
    st.markdown("#### Une idée pour commencer ?")
    colonnes = st.columns(len(QUESTIONS_SUGGEREES))
    for colonne, question in zip(colonnes, QUESTIONS_SUGGEREES):
        if colonne.button(question, use_container_width=True):
            # Même chemin que le chat_input : question + réponse + rerun.
            traiter_question(question)

# ---------------------------------------------------------------------------
# Affichage de l'historique du chat
# ---------------------------------------------------------------------------
if st.session_state["messages"]:
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ---------------------------------------------------------------------------
# Zone de saisie (chat natif Streamlit, pas de formulaire classique)
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Pose ta question sur l'informatique et le numérique…"):
    traiter_question(prompt)

# ---------------------------------------------------------------------------
# Pied de page
# ---------------------------------------------------------------------------
st.divider()
st.caption("Projet réalisé dans le cadre de mon portfolio Data Science & IA")