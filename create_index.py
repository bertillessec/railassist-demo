import json, requests, subprocess

key = subprocess.check_output('az search admin-key show --service-name railassist-search --resource-group rg-t-bmathieu-1283 --query primaryKey -o tsv', shell=True).decode().strip()
endpoint = 'https://railassist-search.search.windows.net'
headers = {'Content-Type':'application/json', 'api-key': key}

# Simple index without semantic config
index_def = {
    'name': 'rail-knowledge',
    'fields': [
        {'name':'id','type':'Edm.String','key':True,'filterable':True},
        {'name':'title','type':'Edm.String','searchable':True,'analyzer':'fr.microsoft'},
        {'name':'category','type':'Edm.String','filterable':True,'facetable':True},
        {'name':'content','type':'Edm.String','searchable':True,'analyzer':'fr.microsoft'},
        {'name':'language','type':'Edm.String','filterable':True},
    ]
}

r = requests.put(f'{endpoint}/indexes/rail-knowledge?api-version=2024-07-01', headers=headers, json=index_def)
print(f'Index creation: {r.status_code}')
if r.status_code >= 400:
    print(f'Error: {r.text}')
    # If index exists, try delete + recreate
    if 'already exists' in r.text.lower():
        print('Index exists, deleting...')
        requests.delete(f'{endpoint}/indexes/rail-knowledge?api-version=2024-07-01', headers=headers)
        r = requests.put(f'{endpoint}/indexes/rail-knowledge?api-version=2024-07-01', headers=headers, json=index_def)
        print(f'Retry: {r.status_code}')

if r.status_code < 300:
    docs = {'value': [
        {'@search.action':'upload','id':'reg-001','title':'Droits des voyageurs - Reglement EC 1371/2007','category':'reglementation','language':'fr','content':'Le reglement europeen EC 1371/2007 etablit les droits et obligations des voyageurs ferroviaires. En cas de retard a destination de 60 minutes ou plus, le voyageur a droit a une indemnisation de 25% du prix du billet pour un retard de 60 a 119 minutes, et de 50% pour un retard de 120 minutes ou plus. Pour les trains nationaux belges, la SNCB applique des seuils plus genereux: 25% des 15 minutes de retard, 50% des 30 minutes, et 100% des 60 minutes. La demande doit etre introduite dans les 3 mois suivant le voyage.'},
        {'@search.action':'upload','id':'reg-002','title':'Conditions generales de transport SNCB','category':'reglementation','language':'fr','content':'Tout voyageur doit etre en possession un titre de transport valable avant de monter dans le train. En absence de titre valable, une surtaxe de 75 EUR est appliquee. Les enfants de moins de 12 ans voyagent gratuitement accompagnes un adulte. Les velos sont admis moyennant un supplement de 4 EUR. Les animaux de petite taille sont admis gratuitement dans un contenant adapte.'},
        {'@search.action':'upload','id':'reg-003','title':'Abonnements et formules tarifaires','category':'tarification','language':'fr','content':'La SNCB propose: Standard Abonnement (reduction 75%), Campus pour etudiants, Key Card (10 trajets prix reduit), Railflex (tout le reseau), Go Pass jeunes moins de 26 ans (10 trajets a 6,60 EUR). Weekend Ticket: illimite sam-dim pour 7,50 EUR. Carte Senior: 50% reduction pour les plus de 65 ans.'},
        {'@search.action':'upload','id':'reg-004','title':'Procedure de reclamation','category':'service_client','language':'fr','content':'Reclamation via formulaire en ligne belgiantrain.be, guichet Customer Service en gare, ou courrier postal Service Clientele SNCB Rue de France 56 1060 Bruxelles. Delai traitement 30 jours ouvrables. Joindre titre de transport original. Remboursement par virement ou bon de voyage.'},
        {'@search.action':'upload','id':'sec-001','title':'Regles de securite en gare et a bord','category':'securite','language':'fr','content':'Interdit de traverser les voies hors passages prevus. Respecter ligne jaune sur quais. Signal alarme uniquement en danger imminent (amende 500 EUR si abus). Defibrillateur dans chaque rame. Colis suspect: appeler 0800 30 230.'},
        {'@search.action':'upload','id':'sec-002','title':'Accessibilite PMR','category':'accessibilite','language':'fr','content':'Service B-Special a reserver 24h a avance au 02/528.28.28. Rampes amovibles en gare. Places PMR en voiture 1. Chiens assistance admis gratuitement. Bandes podotactiles et annonces sonores dans toutes les gares.'},
        {'@search.action':'upload','id':'ops-001','title':'Ponctualite et performance','category':'operations','language':'fr','content':'Objectif ponctualite 90%. Taux 2025: 87,3%. Causes retard: infrastructure 35%, materiel roulant 25%, facteurs externes 20%, gestion 15%. Plan 2024-2028: 200 km voies/an, 445 nouvelles voitures M7.'},
        {'@search.action':'upload','id':'ops-002','title':'Bagages et objets interdits','category':'operations','language':'fr','content':'2 bagages main gratuits (max 30 kg). Interdits: armes, explosifs, produits chimiques, objets pointus non proteges, hoverboards. Trottinettes pliees admises. Objets trouves: 02/525.25.25, conserves 50 jours.'},
        {'@search.action':'upload','id':'net-001','title':'Reseau ferroviaire belge','category':'reseau','language':'fr','content':'3607 km de lignes, 550 gares. L1 Bruxelles-Anvers (40000 voyageurs/jour), L25/L36 Bruxelles-Liege (grande vitesse), L50A Bruxelles-Gand-Bruges-Ostende, L96 Bruxelles-Namur-Luxembourg. Gares principales: Bruxelles-Midi, Anvers-Central, Liege-Guillemins.'},
        {'@search.action':'upload','id':'net-002','title':'Connexions internationales','category':'reseau','language':'fr','content':'Depuis Bruxelles-Midi: Thalys/Eurostar Paris 1h22, Londres 1h51, Amsterdam 1h47, Cologne 1h47. ICE Francfort 2h58. Luxembourg via L161 3h. Nightjet vers Vienne et Innsbruck. Reservation obligatoire trains grande vitesse.'}
    ]}
    r = requests.post(f'{endpoint}/indexes/rail-knowledge/docs/index?api-version=2024-07-01', headers=headers, json=docs)
    print(f'Upload: {r.status_code}')
    result = r.json()
    ok = sum(1 for v in result.get('value', []) if v.get('status'))
    print(f'Uploaded: {ok} documents')

    # Quick test search
    r = requests.post(f'{endpoint}/indexes/rail-knowledge/docs/search?api-version=2024-07-01', headers=headers, json={'search':'compensation retard','top':2})
    print(f'Test search: {r.status_code}')
    for doc in r.json().get('value', []):
        print(f'  -> {doc["title"]} (score: {doc["@search.score"]:.2f})')

print('Done!')
