# Déployer le site Fixbyte sur GitHub Pages

Guide pas à pas pour publier ce site statique sur **https://designs.fixbyte.dev**.

Le dépôt doit rester **public** (Pages gratuit). Branche utilisée : `main`, dossier racine `/`.

---

## 1. Créer le dépôt GitHub

1. Connectez-vous à GitHub.
2. **New repository**.
3. Nom suggéré : `fixbyte-designs` (ou autre, public).
4. Ne pas cocher “Add a README” si vous poussez ce dossier tel quel.
5. Créer le dépôt.

En local, à la racine de ce projet :

```bash
git init
git add .
git commit -m "Site Fixbyte Designs (restaurants, barbiers, instituts, cafés)"
git branch -M main
git remote add origin https://github.com/VOTRE-COMPTE/VOTRE-DEPOT.git
git push -u origin main
```

Remplacez `VOTRE-COMPTE` et `VOTRE-DEPOT`.

---

## 2. Activer GitHub Pages

1. Dépôt → **Settings** → **Pages**.
2. **Build and deployment**
   - Source : **Deploy from a branch**
   - Branch : **main**
   - Folder : **/ (root)**
3. **Save**.

Attendez 1 à 2 minutes. Une URL temporaire apparaît :

`https://VOTRE-COMPTE.github.io/VOTRE-DEPOT/`

---

## 3. Fichier CNAME

Ce projet contient déjà un fichier `CNAME` à la racine :

```
designs.fixbyte.dev
```

Ne le renommez pas et ne l’écrasez pas. GitHub s’en sert pour lier le domaine personnalisé.

---

## 4. DNS chez le registrar de `fixbyte.dev`

Chez votre registrar / DNS (Cloudflare, OVH, Namecheap, etc.), zone **fixbyte.dev**.

### Option recommandée : CNAME

| Type  | Nom      | Valeur                 | TTL  |
| ----- | -------- | ---------------------- | ---- |
| CNAME | `designs` | `VOTRE-COMPTE.github.io` | Auto |

`VOTRE-COMPTE` = votre nom d’utilisateur GitHub (ou le compte org).  
Pas de `https://`, pas de slash final.

Exemple : si le compte est `fixbyte`, la valeur est `fixbyte.github.io`.

### Option de secours : enregistrements A / AAAA

Si le registrar refuse un CNAME sur ce sous-domaine, pointez `designs` (ou `@` seulement si vous utilisiez l’apex, ce n’est **pas** le cas ici) vers GitHub :

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
dig designs.fixbyte.dev CNAME +short
# attendu : VOTRE-COMPTE.github.io.

dig designs.fixbyte.dev A +short
# attendu : une des IP 185.199.108–111.153
```

---

## 5. Brancher le domaine dans GitHub Pages

1. **Settings** → **Pages**.
2. **Custom domain** : `designs.fixbyte.dev`
3. **Save**.
4. GitHub vérifie le DNS (pastille verte “DNS check successful”).
5. Cochez **Enforce HTTPS** dès que le certificat est prêt (souvent 5–30 min après le check DNS).

Si le check échoue : attendez la propagation, vérifiez le CNAME, retirez un éventuel enregistrement CAA trop strict, puis ré-enregistrez le domaine.

---

## 6. Vérifier le site en ligne

Ouvrez :

- [https://designs.fixbyte.dev](https://designs.fixbyte.dev) — accueil
- [https://designs.fixbyte.dev/restaurant.html](https://designs.fixbyte.dev/restaurant.html) — page Restaurants
- [https://designs.fixbyte.dev/barbiers.html](https://designs.fixbyte.dev/barbiers.html) — page Barbiers
- [https://designs.fixbyte.dev/instituts.html](https://designs.fixbyte.dev/instituts.html) — page Instituts
- [https://designs.fixbyte.dev/cafes.html](https://designs.fixbyte.dev/cafes.html) — page Cafés & boulangeries

Contrôles :

- Le logo Fixbyte s’affiche.
- La nav bascule entre Restaurants, Barbiers, Instituts et Cafés.
- Les cartes mention montrent une image OG (ou un fallback) et ouvrent l’URL dans un nouvel onglet.
- Le bloc **Tarifs** est visible en bas (prix encore vides).
- Le cadenas HTTPS est actif.

---

## 7. Ajouter ou modifier une œuvre

Les URLs ne sont pas dans le HTML. Éditez :

- `data/restaurants.json`
- `data/barbiers.json`
- `data/instituts.json`
- `data/cafes.json`

Format :

```json
[
  {
    "url": "https://votre-design-framer.com/projet",
    "image": "assets/previews/votre-design.png"
  }
]
```

Capture (ou recapture) l’aperçu :

```bash
./fetch-previews.py data/restaurants.json
# ou un site seul :
./fetch-previews.py https://votre-design-framer.com/projet
```

Puis :

```bash
git add data/restaurants.json data/barbiers.json data/instituts.json data/cafes.json assets/previews
git commit -m "Ajoute un design restaurant"
git push
```

GitHub Pages se met à jour en ~1 minute.

Les cartes lisent `url` + `image` dans le JSON (fichiers locaux dans `assets/previews/`). Aucun appel Microlink.

---

## 8. Prévisualiser en local

Ne pas ouvrir les HTML en `file://` (le JSON et les aperçus locaux peuvent échouer).

```bash
python3 -m http.server 8080
```

Puis : [http://localhost:8080](http://localhost:8080)

---

## 9. Dépannage

| Problème | Piste |
| --- | --- |
| DNS check failed | CNAME vers `USER.github.io` (pas l’URL du projet). Attendre la propagation. `dig` pour confirmer. |
| HTTPS reste gris | Attendre le certificat Let’s Encrypt. Ne pas cocher Enforce HTTPS trop tôt. Réenregistrer le custom domain. |
| 404 sur `/restaurant.html`, `/barbiers.html`, `/instituts.html` ou `/cafes.html` | Source Pages = `main` / `/ (root)`. Les fichiers doivent être à la racine du dépôt, pas dans un sous-dossier. |
| Page blanche / pas de cartes | Console : fetch JSON bloqué. En local, utiliser `http.server`. En prod, vérifier `data/*.json` poussés. |
| Images OG vides / quota Microlink | Quota journalier atteint. Le script retombe sur screenshot puis `assets/placeholder.svg`. Réessayer le lendemain, ou mettre un plan Microlink. |
| Ancien site encore visible | Cache CDN Pages : attendre 1–2 min, hard refresh. |
| Custom domain écrasé | Ne pas supprimer `CNAME`. Un push sans ce fichier détache le domaine. |

---

## Fichiers utiles

| Fichier | Rôle |
| --- | --- |
| `index.html` | Accueil (`/`) — pas dans la nav |
| `restaurant.html` | Page Restaurants |
| `barbiers.html` | Page Barbiers |
| `instituts.html` | Page Instituts |
| `cafes.html` | Page Cafés & boulangeries |
| `data/restaurants.json` | URLs des designs restaurants |
| `data/barbiers.json` | URLs des designs barbiers |
| `data/instituts.json` | URLs des designs instituts |
| `data/cafes.json` | URLs des designs cafés & boulangeries |
| `CNAME` | `designs.fixbyte.dev` |
| `css/style.css` | Styles |
| `js/cards.js` | Cartes mention Microlink |
