## 4.1 Introduction

Ce chapitre présente l'évaluation expérimentale de KIMVIWARE, une plateforme générique de test de microservices, afin de fournir des réponses empiriques aux questions de recherche posées dans le Chapitre 1. Au lieu de se limiter à la validation d'hypothèses, cette section structure l'analyse des résultats autour de la résolution directe de ces questions, démontrant ainsi la contribution pratique et académique de notre travail.

Les quatre questions de recherche qui guident cette évaluation sont :
1.  **RQ1:** Comment les algorithmes génétiques peuvent-ils être appliqués efficacement pour optimiser la génération et la sélection des cas de test tout en réduisant la redondance ?
2.  **RQ2:** Quelles stratégies hybrides peuvent être conçues pour atténuer le problème de l'explosion des chemins dans l'exécution symbolique pour les logiciels à grande échelle ?
3.  **RQ3:** Comment une architecture basée sur les microservices peut-elle soutenir l'évolutivité, la modularité et l'extensibilité dans les plateformes de test de logiciels automatisées ?
4.  **RQ4:** Dans quelle mesure une plateforme générique peut-elle réduire l'écart entre la recherche universitaire et les pratiques industrielles en matière de test de logiciels ?

L'évaluation a été menée sur une série de systèmes sous test (SUT) représentatifs, comprenant des implémentations en Python et C de services d'authentification et de gestion de données. Les résultats rapportés représentent la moyenne de plusieurs exécutions indépendantes avec des intervalles de confiance de 95%, garantissant la fiabilité des conclusions. Leurs implications sont discutées en profondeur, mettant en évidence la manière dont KIMVIWARE aborde les défis persistants de l'ingénierie logicielle moderne.
