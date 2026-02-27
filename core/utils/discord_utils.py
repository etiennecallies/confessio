import json
import os
from enum import Enum

import httpx


class DiscordChanel(Enum):
    NEW_REPORTS = "nouveaux-retours"
    NEW_IMAGES = "nouvelles-images"
    INFRA_ALERTS = "infra-alerts"
    CRAWLING_ALERTS = "crawling-alerts"
    CONTACT_FORM = "formulaire-de-contact"


def send_discord_alert(message: str, channel: DiscordChanel):
    discord_webhooks_json = os.getenv("DISCORD_WEBHOOKS_JSON")

    try:
        discord_webhooks_dict = json.loads(discord_webhooks_json)
        webhook_url = discord_webhooks_dict[channel.value]
    except (TypeError, json.JSONDecodeError, KeyError) as e:
        print(f"Erreur lors du chargement des webhooks Discord : {e}")
        return

    data = {
        "content": message
    }
    response = httpx.post(webhook_url, json=data)

    if response.status_code != 204:
        print(f"Erreur lors de l'envoi de l'alerte Discord : "
              f"{response.status_code} - {response.text}")
    else:
        print("Alerte Discord envoyée avec succès.")


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    send_discord_alert("Test d'alerte Discord depuis Confessio.", DiscordChanel.CRAWLING_ALERTS)
