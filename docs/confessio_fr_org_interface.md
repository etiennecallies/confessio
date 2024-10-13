### Côté Confessio org (Nathan)
→ Prévoir l’authentification (HTTP)

→ endpoints pour récupérer les églises et paroisses

- [srvc-data] GET /dioceses
    - *payload à définir*
- [srvc-data] GET /diocese/{id}
    - *payload à définir*
- [srvc-data] GET /parish
    - *payload à définir*

→ endpoints pour récupérer les jobs et update leur statut

- [scriptorium] GET / job/parsing
    - renvoie null ou le payload du prochain job sur la queue (en statut “queued”)
    - payload de réponse
        
        ```python
        {
        	"job_id": str,
        	"parish_id": str,
        	"url": str,
        	"html": str
        }
        ```
        
- [scriptorium] UPDATE / job/{id}
    - payload
    
    ```python
    {
    	"status": enum["started", "finished", "failed"]
    }
    ```
    

→ endpoints pour ajouter les jobs et update leur statut

- [srvc-data] POST /schedules
    - payload
    
    ```python
    {
    	# Source
    	"job_id": uuid,
    	
    	# What?
    	"type": enum["confession", "mass", "adoration", ...],
    	"description": Optional[str],
    	"status": enum["unpublished", "published"],
    
    	# When?
    	"start": datetime without timezone,
    	"end": Optional[datetime without timezone],
    	
    	# Where?
    	"parish_id": uuid,
    	"church_id": Optional[uuid],
    	"appends_in_external_church": bool,
    }
    ```
    
- [srvc-data] POST /schedules-rules
    - *payload à définir*

### Côté [confessio.fr](http://confessio.fr) (Etienne)

→ récupère les paroisses et églises

→ dépile les job parsing

→ pousse les schedules 

→ plus tard, exposer

- [srvc-data] GET /next-schedules
    - input : une schedule_rule
    - output : une list de schedules
    - règles : *à préciser*