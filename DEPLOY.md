# Déployer le site Fixbyte sur GitHub Pages

Guide pas à pas pour publier ce site statique sur **https://studio.fixbyte.be**.

Le dépôt doit rester **public** (Pages gratuit). Branche : **`master`**. Déploiement : **GitHub Actions** (workflow `Site`).

---

## 1. Créer le dépôt GitHub

1. Connectez-vous à GitHub.
2. **New repository**.
3. Nom suggéré : `fixbyte-templates` (ou autre, public).
4. Ne pas cocher “Add a README” si vous poussez ce dossier tel quel.
5. Créer le dépôt.

En local, à la racine de ce projet :

```bash
git init
git add .
git commit -m "Site Fixbyte Designs (restaurants, barbiers, agences, cafés)"
git branch -M master
git remote add origin https://github.com/VOTRE-COMPTE/VOTRE-DEPOT.git
git push -u origin master
```

Remplacez `VOTRE-COMPTE` et `VOTRE-DEPOT`.

---

## 2. Activer GitHub Pages (Actions)

1. Dépôt → **Settings** → **Pages**.
2. **Build and deployment**
   - Source : **GitHub Actions** (pas “Deploy from a branch”)
3. **Settings** → **Actions** → **General** → **Workflow permissions** → **Read and write** (pour que CI puisse committer les PNG).
4. Poussez sur `master` (ou lancez le workflow **Site** manuellement).
5. **Actions** → workflow **Site** → vérifiez que le job **Deploy GitHub Pages** est vert.

Une URL temporaire apparaît :

`https://VOTRE-COMPTE.github.io/VOTRE-DEPOT/`

Le workflow (`.github/workflows/pages.yml`) :

1. Capture les aperçus manquants (`fetch-previews.py --only-missing`) si `data/**` a changé
2. Commit les PNG + JSON mis à jour si besoin
3. Déploie le site sur Pages

---

## 3. Fichier CNAME

Ce projet contient déjà un fichier `CNAME` à la racine :

```
studio.fixbyte.be
```

Ne le renommez pas et ne l’écrasez pas. GitHub s’en sert pour lier le domaine personnalisé.

---

## 4. DNS chez le registrar

Chez votre registrar / DNS (Cloudflare, OVH, Namecheap, etc.), zone du domaine parent.

### Option recommandée : CNAME

| Type  | Nom      | Valeur                 | TTL  |
| ----- | -------- | ---------------------- | ---- |
| CNAME | `studio` | `VOTRE-COMPTE.github.io` | Auto |

`VOTRE-COMPTE` = votre nom d’utilisateur GitHub (ou le compte org).  
Pas de `https://`, pas de slash final.

Exemple : si le compte est `m0hss`, la valeur est `m0hss.github.io`.

### Option de secours : enregistrements A / AAAA

Si le registrar refuse un CNAME sur ce sous-domaine, pointez `studio` vers GitHub :

**A**

- `185.199.108.153`
- `185.199.109.153`
- `185.199.110.153`
- `185.199.111.153`

**AAAA**

- `2606:50c0:8000::153`
- `2606:50c0:8001::153`
- `2606:50c0:8002::153`
- `2606:50c0:8003::153`

Pour un sous-domaine, préférez le CNAME.

Propagation DNS : quelques minutes à 48 h (souvent < 30 min).

Vérification :

```bash
dig studio.fixbyte.be CNAME +short
# attendu : VOTRE-COMPTE.github.io.

dig studio.fixbyte.be A +short
# attendu : une des IP 185.199.108–111.153
```

---

## 5. Brancher le domaine dans GitHub Pages

1. **Settings** → **Pages**.
2. **Custom domain** : `studio.fixbyte.be`
3. **Save**.
4. GitHub vérifie le DNS (pastille verte “DNS check successful”).
5. Cochez **Enforce HTTPS** dès que le certificat est prêt (souvent 5–30 min après le check DNS).

Si le check échoue : attendez la propagation, vérifiez le CNAME, retirez un éventuel enregistrement CAA trop strict, puis ré-enregistrez le domaine.

---

## 6. Vérifier le site en ligne

Ouvrez :

- [https://studio.fixbyte.be](https://studio.fixbyte.be) — accueil
- [https://studio.fixbyte.be/restaurant.html](https://studio.fixbyte.be/restaurant.html) — page Restaurants
- [https://studio.fixbyte.be/barbiers.html](https://studio.fixbyte.be/barbiers.html) — page Barbiers
- [https://studio.fixbyte.be/agences.html](https://studio.fixbyte.be/agences.html) — page Agences
- [https://studio.fixbyte.be/entreprises.html](https://studio.fixbyte.be/entreprises.html) — page Entreprises
- [https://studio.fixbyte.be/cafes.html](https://studio.fixbyte.be/cafes.html) — page Cafés & boulangeries
- [https://studio.fixbyte.be/ecommerce.html](https://studio.fixbyte.be/ecommerce.html) — page E-commerce

Contrôles :

- Le logo Fixbyte s’affiche.
- La nav bascule entre Restaurants, Barbiers, Agences, Entreprises, Cafés et E-commerce.
- Les cartes montrent une image de preview et ouvrent l’URL dans un nouvel onglet.
- Le cadenas HTTPS est actif.

---

## 7. Ajouter ou modifier une œuvre (flux CI)

Les URLs ne sont pas dans le HTML. Éditez un fichier `data/*.json` :

- `data/restaurants.json`
- `data/barbiers.json`
- `data/agences.json`
- `data/entreprises.json`
- `data/cafes.json`
- `data/ecommerce.json`

Ajoutez l’URL (le champ `image` peut être omis — CI le remplit) :

```json
[
  {
    "url": "https://votre-design-framer.com/projet"
  }
]
```

Puis :

```bash
git add data/restaurants.json
git commit -m "Ajoute un design restaurant"
git push
```

Le workflow **Site** :

1. Détecte le changement sous `data/**`
2. Lance `fetch-previews.py --only-missing` (Chrome headless)
3. Commit les PNG + JSON mis à jour (`chore: refresh design previews [skip ci]`)
4. Déploie Pages

Recapture manuelle (tous les manquants) : **Actions** → **Site** → **Run workflow**.

### Contrôles de skip (message de commit)

| Tag | Effet |
| --- | --- |
| `[skip previews]` | Déploie le site **sans** lancer Chrome / screenshots |
| `[skip ci]` | Ne lance **rien** (ni previews, ni deploy) |

Exemples :

```bash
git commit -m "tweaks hero [skip previews]"
git push

git commit -m "wip docs [skip ci]"
git push
```

Push HTML/CSS/JS sans toucher `data/**` : le job previews est sauté automatiquement ; le deploy tourne quand même.

### Option locale (debug)

```bash
./fetch-previews.py data/restaurants.json --only-missing
# ou un site seul :
./fetch-previews.py https://votre-design-framer.com/projet
```

Les cartes lisent `url` + `image` dans le JSON (fichiers dans `assets/previews/`).

---

## 8. Prévisualiser en local

Ne pas ouvrir les HTML en `file://` (le JSON et les aperçus locaux peuvent échouer).

```bash
python3 -m http.server 8080
# ou : ./serve.sh
```

Puis : [http://localhost:8080](http://localhost:8080)

---

## 9. Dépannage

| Problème | Piste |
| --- | --- |
| Workflow Site ne déploie pas | Settings → Pages → Source = **GitHub Actions**. Vérifier Actions → Site. |
| Job previews échoue | Logs Chrome / URL inaccessible. Relancer le workflow ou capturer en local. |
| DNS check failed | CNAME vers `USER.github.io` (pas l’URL du projet). Attendre la propagation. `dig` pour confirmer. |
| HTTPS reste gris | Attendre le certificat Let’s Encrypt. Ne pas cocher Enforce HTTPS trop tôt. Réenregistrer le custom domain. |
| 404 sur une page HTML | Artifact Pages doit contenir les fichiers à la racine du site. Vérifier le job deploy. |
| Page blanche / pas de cartes | Console : fetch JSON bloqué. En local, utiliser `http.server`. En prod, vérifier `data/*.json` poussés. |
| Preview manquante sur une PR | Le workflow **Validate data** échoue tant que l’image n’existe pas (merge sur `master` laisse CI la générer, ou générez en local avant la PR). |
| Ancien site encore visible | Cache CDN Pages : attendre 1–2 min, hard refresh. |
| Custom domain écrasé | Ne pas supprimer `CNAME`. Un push sans ce fichier détache le domaine. |

---

## Fichiers utiles

| Fichier | Rôle |
| --- | --- |
| `index.html` | Accueil (`/`) — pas dans la nav |
| `restaurant.html` | Page Restaurants |
| `barbiers.html` | Page Barbiers |
| `agences.html` | Page Agences |
| `entreprises.html` | Page Entreprises |
| `instituts.html` | Redirect → `agences.html` |
| `cafes.html` | Page Cafés & boulangeries |
| `ecommerce.html` | Page E-commerce |
| `data/*.json` | URLs + chemins d’images des designs |
| `CNAME` | `studio.fixbyte.be` |
| `css/style.css` | Styles |
| `js/cards.js` | Rendu des cartes depuis le JSON |
| `fetch-previews.py` | Capture des aperçus (local + CI) |
| `scripts/validate-data.py` | Validation JSON / images (CI PR) |
| `.github/workflows/pages.yml` | Previews + deploy Pages |
| `.github/workflows/validate.yml` | Guardrails PR sur `data/**` |
