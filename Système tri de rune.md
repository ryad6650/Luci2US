\## Stats de runes reconnues (11 types)



Index dans les tableaux: SPD, HP%, HP(flat), ATK%, ATK(flat), DEF%, DEF(flat), CD%, CR%, ACC%, RES%



ATTENTION : la convention de nommage est inversée entre Main et Sub.



&#x20; | Stat réelle | Champ Main | Champ Sub   | Index tableau  |

&#x20; |-------------|------------|-------------|----------------|

&#x20; | SPD         | MainSPD    | SubSPD      | 0              |

&#x20; | HP%         | MainHP2    | SubHP       | 1              |

&#x20; | HP flat     | MainHP     | SubHP2      | 2              |

&#x20; | ATK%        | MainATK2   | SubATK      | 3              |

&#x20; | ATK flat    | MainATK    | SubATK2     | 4              |

&#x20; | DEF%        | MainDEF2   | SubDEF      | 5              |

&#x20; | DEF flat    | MainDEF    | SubDEF2     | 6              |

&#x20; | CD%         | MainCD     | SubCD       | 7              |

&#x20; | CR%         | MainCR     | SubCR       | 8              |

&#x20; | ACC%        | MainACC    | SubACC      | 9              |

&#x20; | RES%        | MainRES    | SubRES      | 10             |



&#x20; Règle : pour Main, le suffixe "2" = pourcentage. Pour Sub, le suffixe "2" = flat.

&#x20; Tous les tableaux de poids/maxRoll/diviseurs utilisent l'index ci-dessus.



Suffixes dans le code:

\- \*\*Main\*\*: MainSPD, MainATK (flat), MainATK2 (%), MainHP, MainHP2 (%), MainDEF, MainDEF2 (%), MainCR, MainCD, MainACC, MainRES

\- \*\*Innate\*\*: InnateSPD, InnateATK, InnateATK2

\- \*\*Sub\*\*: SubSPD, SubATK, SubATK2 + seuils MinSPD, MinATK, MinATK2

\- \*\*Artefact\*\*: SPDInc, ATKInc, HPAdd, ATKAdd, DEFAdd, SPDAdd + S1Rec, S2Rec, S3Rec, S1Acc, S2Acc, S3Acc, S1CD, S2CD, S34CD, FirstCD, FireDealt, WaterDealt, WindDealt, LightDealt, DarkDealt, etc.



Attribution automatique des stats principales par slot

&#x20;                                                                                                                                                                                                                          

&#x20; Dans le système force :                                                                                                                                                                          

&#x20; - Slot 1 → Main = ATK flat

&#x20; - Slot 3 → Main = DEF flat

&#x20; - Slot 5 → Main = HP flat 



Dans le système force :

&#x20; - Legend (lv ≥ 12) : 4 subs

&#x20; - Hero (lv ≥ 9) : jusqu'à 3 subs

&#x20; - Rare (lv ≥ 6) : jusqu'à 2 subs

&#x20; - Magic (lv ≥ 3) : 1 sub

&#x20; - Normal (lv ≥ 0) : 0 sub



\## Formule 1: Score



```

Score = Ceiling( SUM(SubValue\[i] \* poids\[stat]) + InnateValue \* poids\[innate] )

```



Poids fixes (meme pour tous les grades):



| Index | Stat probable | Poids |

|-------|---------------|-------|

| 0     | SPD 		| 3.3333|

| 1     | HP% 		| 2.5 	|

| 2     | HP flat 	| 0.0187|

| 3 	| ATK% 		| 2.5 	|

| 4 	| ATK flat 	| 0.35 	|

| 5 	| DEF% 		| 2.5 	|

| 6 	| DEF flat 	| 0.35 	|

| 7 	| CD% 		| 2.8571|

| 8 	| CR% 		| 3.3333|

| 9 	| ACC% 		| 2.5 	|

| 10 	| RES% 		| 2.5 	|



Max theorique: \~300. Inclut innate.



\## Formule 2: Efficiency1 — METHODE PAR DEFAUT



\*\*C'est la methode utilisee par defaut dans l'app\*\* (EffMethod pointe vers Efficiency1).



```

Efficiency1 = Ceiling( (SUM(SubValue\[i] \* poids\_grade\[stat] \* 100)) / denominateur )

```



N'inclut PAS l'innate. Poids varient par grade.



\### Calcul du denominateur



Le denominateur n'est PAS le max potentiel total de la rune. Il est construit ainsi:

1\. Base = valeur du palier de niveau atteint (voir table ci-dessous)

2\. On ajoute le bonus de rarete pour chaque palier de level \*\*non encore atteint\*\*



Pour une rune +0 Legend 6\*: denominateur = 0 (base lv0) + 4 × 8 (bonus Legend) = \*\*32\*\*

Pour une rune +12 Legend 6\*: denominateur = 64 (base lv12) + 0 (aucun palier restant) = \*\*64\*\*



Cela signifie qu'a +0, l'Efficiency1 mesure la qualite des subs actuelles \*\*par rapport au potentiel des rolls restants\*\*, pas par rapport au max total. C'est pourquoi une rune +0 peut afficher une efficiency elevee.



\### Exemple verifie (confirme avec l'app reelle)



Rune 6\* Legend Swift Slot 1 +0, subs: SPD 6, HP% 6, DEF% 7, ATK% 5

\- Numerateur: (6×1.333 + 6×1 + 7×1 + 5×1) × 100 = 2599.8

\- Denominateur: 0 + 8+8+8+8 = 32

\- Efficiency1 = Ceiling(2599.8 / 32) = Ceiling(81.24) = \*\*82%\*\* ✓



\### Poids par grade (exemples: index 0=SPD, 2=HP flat, 4=ATK flat, 7=CD%):



| Grade | SPD 	| ATK%/DEF%/HP% | HP flat | ATK/DEF flat | CD%  | CR%  | ACC%  | RES% |

|-------|------	|---------------|---------|--------------|------|------|-------|------|

| 1\* 	| 2.0 	| 1.0 	        | 0.0167  | 0.20         | 1.0  | 2.0  | 1.0   | 1.0  |

| 2\* 	| 1.5 	| 1.0           | 0.0143  | 0.24 	 | 1.0  | 1.5  | 1.0   | 1.0  |

| 3\* 	| 1.667 | 1.0           | 0.0152  | 0.25 	 | 1.25 | 1.667| 1.25  | 1.25 |

| 4\* 	| 1.5 	| 1.0           | 0.0133  | 0.24 	 | 1.2  | 1.5  | 1.2   | 1.2  |

| 5\* 	| 1.4 	| 1.0           | 0.0117  | 0.187 	 | 1.4  | 1.4  | 1.0   | 1.0  |

| 6\* 	| 1.333 | 1.0           | 0.0107  | 0.16 	 | 1.143| 1.333| 1.0   | 1.0  |



\### Table des valeurs de base par grade et niveau:



| Grade | Lv0 | Lv3+ | Lv6+ | Lv9+ | Lv12+ |

|-------|-----|------|------|------|-------|

| 1\* 	| 0   | 4    | 8    | 12   | 16    |

| 2\* 	| 0   | 6    | 12   | 16   | 24    |

| 3\* 	| 0   | 10   | 20   | 30   | 40    |

| 4\* 	| 0   | 12   | 24   | 36   | 48    |

| 5\* 	| 0   | 14   | 28   | 42   | 56    |

| 6\* 	| 0   | 16   | 32   | 48   | 64    |



\### Bonus rarete (rolls non effectues):



Pour chaque palier de level non atteint, un bonus par grade est ajoute au denominateur:

\- Legend: +bonus a lv<12, lv<9, lv<6, lv<3 (4 bonus max)

\- Hero: +bonus a lv<9, lv<6, lv<3 (3 bonus max)

\- Rare: +bonus a lv<6, lv<3 (2 bonus max)

\- Magic: +bonus a lv<3 (1 bonus max)



Bonus = grade\_number (1\*=2, 2\*=3, 3\*=5, 4\*=6, 5\*=7, 6\*=8)



\## Formule 3: Efficiency2



```

Efficiency2 = Ceiling( grade\_coef \* (100 + SUM(SubValue\[i] \* 100 / maxRoll\[stat]) + innate\_bonus) / 2.8 )

```



Inclut l'innate. Style "efficacite SW classique".



\### maxRoll par stat (max roll 6\* Legend):



| Stat 	   | maxRoll |

|----------|---------|

| SPD 	   | 30      |

| HP% 	   | 40      |

| HP flat  | 3750    |

| ATK%     | 40      |

| ATK flat | 200     |

| DEF%     | 40      |

| DEF flat | 200     |

| CD%      | 35      |

| CR%      | 30      |

| ACC%     | 40      |

| RES%     | 40      |



\### Coefficient par grade:



| Grade | Coef   |

|-------|--------|

| 1\*    | 0.7959 |

| 2\*    | 0.8044 |

| 3\*    | 0.8554 |

| 4\*    | 0.898  |

| 5\*    | 0.9745 |

| 6\*    | 1.0    |



\---



\## Formule 4: Efficacite Gemstone/Artefact 



```

Efficiency = Ceiling( SUM(SubValue\[i] / (maxValue\[stat] \* rarity\_rolls)) \* 100 / rarity\_divisor )

```



\### Par rarete:



| Rarete | Diviseur | Rolls |

|--------|----------|-------|

| Normal | 4.0      | 1     |

| Magic  | 2.5 	    | 2     |

| Rare   | 2.0      | 3     |

| Hero   | 1.75     | 4     |

| Legend | 1.6      | 5     |



\### maxValue artefact (tableau `\\u0003`, 33 entrees):



Principalement: 6, 6, 6, ... 5, 5, 5, ... 12, 4, 4, 6, 5, 0.3, 4, 4, 40, 4, 4, 8

(correspondant aux 33 types de substats d'artefacts)





\## Tables de rolls de substats



\### Methode — Valeurs max de roll (gemme) par grade:



| Stat 		    | Grade 1 | Grade 2 | Grade 3 |

|-------------------|---------|---------|---------|

| SPD  		    | 6       | 8 	| 10      |

| ATK%/DEF%/CR%     | 9       | 11      | 13      |

| ACC% 		    | 6       | 8       | 10      |

| RES% 		    | 5       | 7       | 9       |

| CD%/HP% 	    | 8       | 9       | 11      |

| ATK flat/DEF flat | 23      | 30      | 40      |

| HP flat 	    | 310     | 420     | 580     |



\### Methode — Valeurs min de roll (meule):



| Stat 		    | Grade 1 | Grade 2 | Grade 3 |

|-------------------|---------|---------|---------|

| SPD 		    | 3       | 4       | 5 	  |

| ATK%/DEF%/CR%     | 6       | 7       | 10 	  |

| ACC%/RES%/CD%/HP% | 0       | 0 	| 0 	  |

| ATK flat/DEF flat | 18      | 22 	| 30 	  |

| HP flat 	    | 250     | 450 	| 550 	  |



\### Methode grindstone — Multiplicateurs:



Pour stats %: 7x ou 8x (ancient) le multiplicateur

Pour SPD/RES: 5x ou 6x (ancient)

Pour flat ATK/DEF: 15x ou 20x (ancient)

Pour HP flat: 300x ou 375x (ancient)                                                                                                                    

&#x20;                                                                                                                                                                                                                          

&#x20; ---                                                                                                                                                                                                                      

&#x20; Logique Gemme vs Meule                                                                                                                                                                                      

&#x20;                                                                                                                                                                                                                          

&#x20; 1. Quand utiliser une Gemme (Enchanted Gem)                                                                                                                                                                              

&#x20;                                                                                                                                                                                                                          

&#x20; Le code applique une gemme sur une sous-stat si :                                                                                                                                                                        

&#x20; - La sous-stat a une valeur > 0                                                                                                                                                                                          

&#x20; - La rune n'a pas encore de gemme appliquée, OU c'est la même position qui est déjà gemmée                                                                                                                               

&#x20;                                                                                                                                                                                                                          

&#x20; Effet : Remplace complètement la sous-stat (type + valeur) par la gemme. Le grind est remis à false sur cette position.



&#x20; 2. Quand utiliser une Meule (Grindstone)



&#x20; Le code applique une meule si :

&#x20; - La sous-stat a une valeur > 0

&#x20; - La position n'est pas marquée comme gemmée (Grind\[j] == false)



&#x20; Effet : Ajoute un bonus fixe à la valeur existante.



&#x20; 3. Stratégie optimale identifiée dans le code



&#x20; Le code explore toutes les combinaisons possibles de gemmes sur chaque position de sous-stat, puis calcule l'efficience de chaque variante pour garder la meilleure. La logique clé :



&#x20; Gemmer la même stat par elle-même est autorisé (ex: ATK% → gemme ATK%). C'est optimal quand :

&#x20; - La stat d'origine a un roll bas (ex: ATK% 5)

&#x20; - La gemme donne une valeur de base plus haute (ex: ATK% \~7-10)

&#x20; - On peut ensuite grinder par-dessus (ATK% est grindable)

&#x20; - Résultat : valeur gemmée + grind legend = bien plus que le roll initial



&#x20; Gemmer vers une stat non-grindable (CR%, CD%, ACC%, RES%) est moins optimal car :

&#x20; - La valeur de la gemme est le plafond final (pas de grind possible)

&#x20; - Exemple : gemmer vers CD% donne \~7 max, alors que garder ATK% gemmé + grind = \~17



&#x20; 4. Le flag Conversion



&#x20; Dans les paramètres, un flag Conversion active/désactive la prise en compte des gemmes dans l'évaluation. Quand activé, le filtre simule toutes les gemmes possibles pour trouver la meilleure configuration.



&#x20; 5. Filtrage des Gemstones/Grindstones 



&#x20; Le filtre sépare les pierres par :

&#x20; - Type : Grindstone ou EnchantedGem

&#x20; - Rareté : Normal / Magic / Rare / Hero / Legend

&#x20; - Set : Violent, Swift, Will, etc.

&#x20; - Seuils minimum par stat (MinHP, MinATK, MinSPD, etc.)



&#x20; ---

&#x20; Résumé : ce qui est optimal



&#x20; ┌──────────────────────────────────────────┬─────────────────────────────────────────────────┐

&#x20; │                Situation                 				 │                          Action optimale                           │

&#x20; ├──────────────────────────────────────────┼─────────────────────────────────────────────────┤

&#x20; │ Sous-stat grindable avec roll bas        				 │ Gemmer la même stat (meilleure base) puis grinder                  │

&#x20; ├──────────────────────────────────────────┼─────────────────────────────────────────────────┤

&#x20; │ Sous-stat non-grindable inutile         				 │ Gemmer vers une stat grindable (ATK%, HP%, DEF%, SPD) puis grinder │

&#x20; ├──────────────────────────────────────────┼─────────────────────────────────────────────────┤

&#x20; │ Sous-stat grindable avec bon roll        				 │ Grinder directement (pas besoin de gemmer)                         │

&#x20; ├──────────────────────────────────────────┼─────────────────────────────────────────────────┤

&#x20; │ Sous-stat non-grindable utile (CR%, CD%) 				 │ Garder telle quelle si le roll est bon                             │

&#x20; └──────────────────────────────────────────┴─────────────────────────────────────────────────┘



Le bot ne fait pas de calcul probabiliste avancé — il teste toutes les variantes et garde la plus efficiente, mais ne prend pas en compte le coût des gemmes/meules ni leur disponibilité.





&#x20;## Logique de filtrage Keep/Sell                                                                                                                                                                                         

&#x20;                                                                                                                                                                                                                          

&#x20; Le filtre itère chaque règle dans `Filter` et vérifie dans l'ordre :                                                                                                                                                     

&#x20;                                                           

&#x20; 1. \*\*Enabled\*\* — la règle est active

&#x20; 2. \*\*Set\*\* — le set de la rune correspond (Violent, Swift, Will, etc. — 23 sets)

&#x20; 3. \*\*Level Range\*\* — 5 ranges : 1→(0-2), 2→(3-5), 3→(6-8), 4→(9-11), 5→(12-15)

&#x20; 4. \*\*Rarity\*\* — Normal / Magic / Rare / Hero / Legend

&#x20; 5. \*\*Grade\*\* — 1★ à 6★

&#x20; 6. \*\*Slot\*\* — slot 1 à 6

&#x20; 7. \*\*Ancient\*\* — si Ancient=Checked, la rune doit être ancient. Si NotAncient=Checked, elle ne doit pas l'être

&#x20; 8. \*\*Main stat\*\* — stat principale (ATK, HP, DEF, SPD, CR, CD, ACC, RES, avec distinction flat/%)

&#x20; 9. \*\*Innate\*\* — stat innée spécifique requise

&#x20; 10. \*\*Sous-stats obligatoires\*\* (CheckState.Checked) — chaque sous-stat marquée obligatoire doit être présente avec une valeur >= seuil minimum (MinSPD, MinATK, etc.), sinon rejet

&#x20; 11. \*\*Sous-stats optionnelles\*\* (CheckState.Indeterminate) — au moins `Optional` d'entre elles doivent être présentes avec valeur >= seuil

&#x20; 12. \*\*Powerup\*\* — pour chaque sous-stat obligatoire/optionnelle, on estime le nombre de rolls :

&#x20;     `rolls\_estimés = Ceiling(SubValue / diviseur) - 1`

&#x20;     Les rolls des stats obligatoires doivent atteindre `PowerupMandatory`, puis ceux des optionnelles doivent atteindre `PowerupOptional`

&#x20; 13. \*\*Efficacité minimale\*\* — selon `EffMethod` :

&#x20;     - Si Efficiency1 : `rune.Efficiency1 >= seuil`

&#x20;     - Si Efficiency2 : `rune.Efficiency2 >= seuil`

&#x20;     - Dans tous les cas : `rune.Score >= seuil` (baseline toujours vérifiée)

&#x20; 14. Si toutes les conditions passent → \*\*GET\*\* (gardée), sinon on passe à la règle suivante. Si aucune règle ne matche → \*\*SELL\*\*



&#x20; La meilleure correspondance est gardée (celle avec l'efficacité la plus haute parmi les règles qui matchent).





\### Diviseurs Powerup (valeur de référence par roll)



&#x20; | Stat        | 6★  | 5★ |

&#x20; |-------------|-----|-----|

&#x20; | SPD         | 6   | 5   |

&#x20; | HP%         | 8   | 7   |

&#x20; | HP flat     | 375 | 300 |

&#x20; | ATK%        | 8   | 7   |

&#x20; | ATK flat    | 20  | 15  |

&#x20; | DEF%        | 8   | 7   |

&#x20; | DEF flat    | 20  | 15  |

&#x20; | CD%         | 7   | 5   |

&#x20; | CR%         | 6   | 5   |

&#x20; | ACC%        | 8   | 7   |

&#x20; | RES%        | 8   | 7   |



La meilleure correspondance est gardee (celle avec l'efficacite la plus haute).

