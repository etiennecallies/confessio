import os
from enum import Enum

import httpx


class DiscordChanel(Enum):
    NEW_REPORTS = "NEW_REPORTS"
    NEW_IMAGES = "NEW_IMAGES"
    INFRA_ALERTS = "INFRA_ALERTS"
    CRAWLING_ALERTS = "CRAWLING_ALERTS"
    CONTACT_FORM = "CONTACT_FORM"


def send_discord_alert(message: str, channel: DiscordChanel):
    discord_webhook_url = os.getenv(f"DISCORD_{channel.name}_URL")

    if not discord_webhook_url:
        print(f"Impossible d'envoyer l'alerte Discord : la variable d'environnement "
              f"DISCORD_{channel.name}_URL n'est pas définie.")
        return

    data = {
        "content": message
    }
    response = httpx.post(discord_webhook_url, json=data)

    if response.status_code != 204:
        print(f"Erreur lors de l'envoi de l'alerte Discord : "
              f"{response.status_code} - {response.text}")
    else:
        print("Alerte Discord envoyée avec succès.")


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    send_discord_alert("Test d'alerte Discord depuis Confessio.", DiscordChanel.CRAWLING_ALERTS)
