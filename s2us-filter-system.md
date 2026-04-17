# Analyse du systeme de filtrage S2US (Script2us)

> Analyse effectuee le 2026-04-16
> Source: decompilation IL bytecode via .NET Reflection (dnfile + csc.exe) de Script2us.exe
> Verification: tokens resolus par Module.ResolveMethod/ResolveField, tableau statique extrait via FieldRva
> Outils: dnSpy installe dans C:\tools\dnSpy, decompileur custom en C# et Python

---

## 1. SMART FILTER - Logique complete (decompilee et verifiee)

Le "Smart Filter" est une **checkbox par filtre** visible dans l'editeur de filtres S2US.
En JSON, il correspond au champ `Level = -1`.

### Signature de la methode decompilee

```csharp
// Methode principale d'evaluation de filtre (noms obfusques, reconstitues par analyse)
bool EvaluateFilter(int runeLevel, int filterLevel, bool doSmartPowerup)
// Retourne: true = rune gardee, false = rune vendue
// Locals: [0]=targetLevel, [1]=loopCounter, [2]=state, [3]=flag,
//         [4]=checkpointsArray, [5]=powerupTarget, [6]=currentCheckpoint, [7]=temp
```

### Pseudo-code decompile depuis le bytecode IL (verifie par token resolution)

```
function EvaluateFilter(runeLevel, filterLevel, doSmartPowerup):
    CHECKPOINTS = [3, 6, 9, 12, 15]   // extrait de FieldRva field#6027
    targetLevel = runeLevel            // loc_0 = arg1 (IL_011D-011E)

    // --- EARLY EXIT ---
    if filterLevel >= runeLevel: return false    // IL_002B-002D
    if rune.IsUnknown AND doSmartPowerup: return false  // IL_0038-0045

    // --- BOUCLE 1: Trouver le prochain checkpoint (toujours) ---
    // IL_014F-016D
    if runeLevel not in CHECKPOINTS:
        for checkpoint in CHECKPOINTS:
            if runeLevel >= checkpoint AND filterLevel < checkpoint:
                targetLevel = checkpoint
                break

    // --- BOUCLE 2: Smart Filter (seulement si doSmartPowerup = true) ---
    // IL_01BA-01EA  (entree conditionelle: IL_016F-0170 ldarg.3 brfalse)
    if doSmartPowerup:
        for checkpoint in CHECKPOINTS:
            if runeLevel >= checkpoint AND filterLevel < checkpoint:
                if SmartPowerup_global == True:
                    // MODE PROGRESSIF: accepte le checkpoint si level >=
                    targetLevel = checkpoint
                    break
                else:
                    // MODE STRICT: uniquement si level == checkpoint exact
                    if runeLevel == checkpoint:
                        targetLevel = checkpoint
                        break

    // --- PLANCHER PAR RARETE (uniquement si SmartPowerup global est OFF) ---
    // IL_01FC-0281 - verifie via String.op_Equality sur get_Rarity
    if SmartPowerup_global == False:
        if rarity == "Rare"   AND runeLevel >= 6  AND targetLevel < 6:  targetLevel = 6
        if rarity == "Hero"   AND runeLevel >= 9  AND targetLevel < 9:  targetLevel = 9
        if rarity == "Legend"  AND runeLevel >= 12 AND targetLevel < 12: targetLevel = 12

    // --- POWER-UP LOOP ---
    // IL_0433-049F: si pas encore au targetLevel, power-up par +3 jusqu'a 15
    // Boucle: powerupTarget = targetLevel + 3, incremente par +3, stop a < 16
    // A chaque palier: re-evalue le filtre -> si echec: return false (SELL)
    // set_Level(filterLevel) appele pour mettre a jour le level du filtre (IL_03AB)
    // Thread.Sleep(1000) entre chaque power-up (IL_0332)

    return true/false  // selon resultat final de l'evaluation
```

### Preuves de la decompilation

| Element | Source IL | Preuve |
|---------|----------|--------|
| CHECKPOINTS = [3,6,9,12,15] | FieldRva field#6027 | Valeurs brutes extraites de la memoire statique |
| get_SmartPowerup | Token 0x06000919 | Resolu par Module.ResolveMethod -> nom exact |
| get_Rarity | Token resolu | Appele 3x suivi de String.op_Equality |
| Constantes 6, 9, 12 | Opcodes ldc.i4.6, ldc.i4.s 9, ldc.i4.s 12 | En clair dans le bytecode |
| set_Level(Int32) | IL_03AB | Resolu par token - modifie le level de la rune |
| Thread.Sleep(1000) | IL_0332 | 1 seconde entre chaque power-up |
| Boucle +3 < 16 | IL_0493-049D | ldc.i4.3 add, blt.s avec ldc.i4.s 16 |

### Comportement pratique

**Smart Filter ON (Level=-1, SmartPowerup=True) - MODE RECOMMANDE:**

Le bot power-up les runes **etape par etape** (+3, +6, +9, +12, +15)
et evalue le filtre a **CHAQUE checkpoint** (avec 1 seconde entre chaque power-up).
Si la rune echoue a un checkpoint -> **STOP et SELL** = economie de mana.

Exemple concret avec une rune Legend et filtre SPD requis:
- +3: SPD n'a pas roll? -> VEND immediatement (economise mana du +6/+9/+12)
- +6: SPD a roll 1x, mais trop bas? -> VEND
- +9: SPD a roll 2x, le filtre passe -> continue
- +12: SPD a roll 3x, tous les criteres valides -> GARDE

**Smart Filter OFF (Level=N fixe):**

Le bot power-up **DIRECTEMENT** au niveau specifie, puis evalue UNE SEULE FOIS.
Tout-ou-rien. Plus de mana depensee, mais evaluation plus simple.

Valeurs du champ Level dans le JSON:
| Level | Signification |
|-------|--------------|
| -1 | Smart Filter ON (evaluation progressive) |
| 0 | Evaluer a +0 (pas de power-up) |
| 1 | Evaluer a +3 |
| 2 | Evaluer a +6 |
| 3 | Evaluer a +9 |
| 4 | Evaluer a +12 |
| 5 | Evaluer a +15 |

### SmartPowerup (flag global)

Flag booleen dans `RuneFilter` (pas dans chaque filtre individuel).

- `SmartPowerup: true` -> active le mode >= (laxiste) dans la boucle de checkpoints.
  Si la rune a atteint ou depasse un checkpoint, l'evaluer a ce checkpoint.
- `SmartPowerup: false` -> mode strict (level exact == checkpoint requis)
  + active le plancher par rarete (Rare=+6, Hero=+9, Legend=+12)

### Proprietes supplementaires decouvertes (via Reflection)

Deux champs par filtre que le JSON standard n'expose pas toujours:
- `PowerupMandatory: Int32` - nombre de subs obligatoires requis PENDANT le power-up
- `PowerupOptional: Int32` - nombre de subs optionnels requis PENDANT le power-up

Ces champs permettent des criteres differents pendant le power-up progressif
vs l'evaluation finale (ex: exiger moins de subs a +3 qu'a +12).

---

## 2. Structure d'un filtre individuel

Chaque filtre est un objet JSON dans `RuneFilter.Filter[]`.

### Champs de filtrage des sous-stats

| Champ | Valeur | Signification |
|-------|--------|---------------|
| `Sub[stat]` = 0 | int | Ignorer ce sub-stat |
| `Sub[stat]` = 1 | int | **Requis** (obligatoire, doit etre present) |
| `Sub[stat]` = 2 | int | **Optionnel** (compte vers le seuil `Optional`) |
| `Min[stat]` | int | Valeur minimale du sub-stat apres rolls |
| `Optional` | int | Nombre de subs optionnels requis parmi ceux marques "2" |
| `PowerupMandatory` | int | Subs obligatoires pendant power-up progressif |
| `PowerupOptional` | int | Subs optionnels pendant power-up progressif |

Stats disponibles: SPD, HP (%), HP2 (flat), ATK (%), ATK2 (flat), DEF (%), DEF2 (flat), CR, CD, ACC, RES

### Champs d'efficience

| Champ | Signification |
|-------|---------------|
| `Efficiency` | Seuil minimum d'efficience (%) |
| `EffMethod` | `"S2US"` ou `"SWOP"` - methode de calcul |
| `Grind` | 0=off, 1=on - simuler les meules dans le calcul |
| `Gem` | 0=off, 1=?, 2=full - simuler les gemmes dans le calcul |

### Champs de selection (set/slot/qualite)

- **Sets**: Violent, Swift, Despair, Will, Rage, Blade, Intangible, etc. (0=ignore, 1=inclus)
- **Slots**: Slot1-Slot6 (0=ignore, 1=inclus)
- **Qualite**: Rare, Hero, Legend (0=ignore, 1=inclus)
- **Etoiles**: FiveStars, SixStars
- **Type**: Ancient, Normal, NotAncient
- **Main stat**: MainSPD, MainHP, MainATK, MainDEF, MainCR, MainCD, MainACC, MainRES
- **Innate**: Innate (global) + InnateXxx pour chaque stat specifique
- **Mark**: Marquage automatique de la rune gardee

---

## 3. RuneFilter (parametres globaux)

```json
"RuneFilter": {
    "SmartPowerup": true,     // Active le mode progressif (voir section 1)
    "RareLevel": 2,           // Power-up Rare a +6 avant evaluation (0=+0, 1=+3, 2=+6...)
    "HeroLevel": 4,           // Power-up Hero a +12
    "LegendLevel": 4,         // Power-up Legend a +12
    "AutoGrind": false,       // Application auto de meules sur runes gardees
    "AutoGem": false,         // Application auto de gemmes sur runes gardees
    "Actives": 0,             // Nombre de filtres actifs
    "Check": true,            // Filtrage actif
    "Filter": [...],          // Liste des filtres
    "Early": false,           // Presets communautaires
    "Mid1": false,
    "Mid2": false,
    "End": false,
    "Fleq6_Early": false,
    "Fleq6_Mid1": false,
    "Fleq6_Mid2": false,
    "Fleq6_Late": false,
    "Fleq6": false
}
```

---

## 4. RuneManager (gestion globale)

```json
"RuneManager": {
    "Powerup": false,        // Power-up toutes les runes
    "PowerupSell": true,     // Vendre apres power-up si non matchee
    "Keep15": false,          // Garder les runes +15
    "KeepMarked": false,      // Garder les runes marquees
    "KeepContent": false,     // Garder les runes equipees
    "OnlySS": false,          // Seulement 6 etoiles
    "Skip": 0                 // Nombre de runes a skip
}
```

---

## 5. Classe Rune (decompilee via Reflection)

```
Rune:
    Unknown: Int32
    IsUnknown: Boolean
    Description: String
    Filter: String              // nom du filtre qui a matche
    Ancient: Boolean
    Level: Int32                // niveau actuel (+0 a +15)
    Type: String                // set (Violent, Swift, etc.)
    Rarity: String              // Rare, Hero, Legend
    Grade: String               // etoiles
    Slot: String                // S1-S6
    Main: String                // stat principale
    Innate: String              // stat innee
    InnateValue: Int32
    Sub: String[]               // tableau de sous-stats
    SubValue: Int32[]           // valeurs des sous-stats
    Gem: Boolean[]              // quels subs ont ete gemmes
    Grind: Boolean[]            // quels subs ont ete grindes
    EffMethod: String           // methode d'efficience
    Score: Int32
    Efficiency1: Decimal        // efficience methode 1
    Efficiency2: Decimal        // efficience methode 2
    Mark: Int32
```

---

## 6. Exemple de log S2US

```
[Violent] [Hero] [+0] [6*] [S2] [SPD] [HP+372] [RES+8%] [CD+7%] [DEF+8%]
  [100% S2US 61% SWOP] got by SPD (CDx2 + HP | ATK | DEF)
```

- Rune Violent Hero 6* Slot 2 main SPD
- Subs: HP flat, RES%, CD%, DEF%
- Efficience: 100% S2US, 61% SWOP
- Gardee par le filtre "SPD (CDx2 + HP | ATK | DEF)"

```
[Guard] [Hero] [+0] [6*] [S2] [DEF] [RES+5%] [ATK+7%] [ACC+8%] [HP+258]
  [74% S2US 57% SWOP] sold
```
- Rune vendue: aucun filtre n'a matche

---

## 7. Presets communautaires

Les fichiers .S2US contiennent des packs pre-configures:

| Fichier | Nb filtres | Usage |
|---------|-----------|-------|
| Fleq6_V2.3_LATEGAME.S2US | 170 | Late/end game |
| Fixed FleqMidgame2 Intan1.S2US | 322 | Mid game complet |
| Fleq6_late_end_and_intangible-midgame.S2US | - | Mix late + intangible midgame |

---

## 8. Informations techniques

- **Executable**: .NET Framework (Mono/.NET assembly), WinForms, ~75 Mo, 514 types, 15200 methodes
- **Obfuscation**: Noms de classes/methodes vides, constantes de string hashees (int -> string via methode interne)
- **OCR**: Tesseract 5.0 (eng.traineddata)
- **Packaging**: Costura.Fody (DLLs embarquees compressees)
- **Serialisation**: Newtonsoft.Json
- **Emulateur**: BlueStacks 5 (1280x720, 240 DPI)
- **Noms de filtres**: encodes en base64 dans le JSON
- **Discord S2US**: https://discord.gg/WHw2gAR
- **Site**: https://script2us.com/
- **dnSpy**: installe dans C:\tools\dnSpy pour decompilation manuelle supplementaire
