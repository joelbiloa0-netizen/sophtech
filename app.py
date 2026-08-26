"""
SophTech — Chatbot IA de culture générale informatique
=======================================================
Projet 3 — Portfolio Data Science & IA (MyLab AI)

Stack : Python + Streamlit + API Groq (modèle openai/gpt-oss-120b)
Rôle  : répondre aux questions de culture informatique / numérique / tech
        (matériel, logiciels, internet, cybersécurité, IA, histoire de la
        tech, métiers du numérique) avec un ton de vulgarisateur.
"""

import json

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

# Tool function calling (standard OpenAI-compatible, PAS browser_search) :
# permet au modèle de demander une recherche web quand c'est pertinent.
OUTIL_RECHERCHE_WEB = [
    {
        "type": "function",
        "function": {
            "name": "rechercher_web",
            "description": (
                "Recherche des informations récentes sur le web. À utiliser "
                "UNIQUEMENT pour des questions sur l'actualité, des événements "
                "récents, des versions logicielles récentes, ou des faits précis "
                "(dates, noms, chiffres) dont tu n'es pas sûr à 100%."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "requete": {
                        "type": "string",
                        "description": "la requête de recherche à utiliser",
                    }
                },
                "required": ["requete"],
            },
        },
    }
]


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
        f"inutile. Adapte ton niveau d'explication : {PROMPTS_NIVEAU[niveau]}.\n\n"
        "Règles de format : réponds de façon concise, 2 à 5 phrases dans la majorité "
        "des cas. N'utilise des tableaux, listes à puces ou sections numérotées QUE "
        "si on te le demande explicitement ou si la question l'exige clairement. Pas "
        "de longue introduction ni de récapitulatif en fin de réponse.\n\n"
        "Règle d'honnêteté : tes connaissances s'arrêtent autour de mi-2024. Si on "
        "te pose une question sur un événement récent, une actualité, une version "
        "logicielle récente, ou un fait précis (date, nom, chiffre) dont tu n'es pas "
        "certain, dis-le clairement et brièvement plutôt que d'inventer une réponse "
        "qui a l'air précise. Ne construis jamais de tableau récapitulatif de faits "
        "si tu n'es pas sûr à 100% de chaque ligne.\n\n"
        "Si la question posée n'a AUCUN rapport avec l'informatique ou le numérique, "
        "réponds poliment que ce n'est pas ton domaine et invite à reformuler autour "
        "de la tech.\n\n"
        "Tu as accès à un outil de recherche web (rechercher_web). "
        "Certaines questions semblent simples mais deviennent vite obsolètes : la "
        "dernière version d'un logiciel ou langage, le prix actuel d'un produit, "
        "qui occupe un poste ou un rôle en ce moment, un classement ou une "
        "statistique à jour, une actualité récente. Pour ce type de question, utilise "
        "TOUJOURS rechercher_web — même si tu as l'impression de connaître la réponse, "
        "car tes connaissances ont une date de coupure et ont pu devenir fausses "
        "depuis. Ne réponds directement, sans chercher, que pour des faits stables : "
        "définitions, concepts, principes de fonctionnement, histoire ancienne. "
        "Quand tu utilises des résultats de recherche, base ta réponse dessus et cite "
        "brièvement 1 à 2 sources (juste le nom du site)."
    )


def rechercher_web(requete: str) -> str:
    """Cherche sur le web via Firecrawl et retourne un résumé texte des résultats."""
    try:
        from firecrawl.v2 import FirecrawlClient
        firecrawl = FirecrawlClient(api_key=st.secrets["FIRECRAWL_API_KEY"])
        resultats = firecrawl.search(query=requete, limit=5)
        if not resultats.web:
            return "Aucun résultat trouvé pour cette recherche."
        texte = ""
        for r in resultats.web:
            texte += f"- {r.title} ({r.url}): {r.description}\n"
        return texte
    except Exception:
        return "La recherche web n'est pas disponible pour le moment."


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

    # 3. Appel API : system prompt en PREMIER message de la liste, suivi de
    #    l'historique complet (rôles user/assistant). Le tool rechercher_web
    #    est proposé au modèle (function calling standard), qui décide seul
    #    de l'utiliser ou non.
    try:
        messages_api = [{"role": "system", "content": system_prompt}] + st.session_state[
            "messages"
        ]

        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages_api,
            max_completion_tokens=600,
            reasoning_effort="low",
            tools=OUTIL_RECHERCHE_WEB,
            tool_choice="auto",
        )
        message_reponse = completion.choices[0].message

        if message_reponse.tool_calls:
            # Le modèle demande une recherche web : exécution de chaque appel,
            # puis deuxième requête avec le tool call et les résultats renvoyés.
            messages_api.append(message_reponse)
            for tool_call in message_reponse.tool_calls:
                arguments = json.loads(tool_call.function.arguments)
                resultat = rechercher_web(arguments["requete"])
                messages_api.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": resultat,
                    }
                )

            # Deuxième appel SANS tools : la réponse finale ne peut plus redemander
            # une recherche, la boucle s'arrête forcément ici.
            completion_finale = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages_api,
                max_completion_tokens=600,
                reasoning_effort="low",
            )
            reponse = completion_finale.choices[0].message.content
        else:
            reponse = message_reponse.content

        # Seul le TEXTE final est ajouté à l'historique, jamais les détails du
        # tool call — exactement comme avant.
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