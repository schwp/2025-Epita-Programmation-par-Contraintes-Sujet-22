# Projet Programmation par Contraintes

## Introduction

Ce projet a pour but de vous permettre d'appliquer concrètement les méthodes et outils vus en cours sur les problématiques de recherche (Search), de programmation par contraintes (CSP), et de raisonnement logique avancé (SAT/SMT). Vous serez amenés à résoudre des problèmes réels ou réalistes à l'aide de ces techniques en développant un projet complet, depuis la modélisation jusqu'à la solution opérationnelle.


## Modalités du projet

### Livrables

Chaque groupe devra forker ce dépôt  Git et déposer son travail dans un répertoire dédié du dépôt. Ce répertoire contiendra :

- Le code source complet, opérationnel, documenté et maintenable (en Python, C#, C++, ou autre).
- Le matériel complémentaire utilisé pour le projet (datasets, scripts auxiliaires, etc.).
- Les slides utilisés lors de la présentation finale.
- Un notebook explicatif détaillant les étapes du projet, les choix de modélisation, les expérimentations et les résultats obtenus.

Les livraisons se feront via des **pull requests**, qui devront être régulièrement mises à jour durant toute la durée du projet de sorte que l'enseignant puisse suivre l'avancement et éventuellement apporter des retours et de sorte que tous les élèves aient pu prendre connaissance des travaux des autres groupes avant la soutenance avec évaluation collégiale.

### Présentation

- Présentation orale finale avec support visuel (slides).
- Démonstration de la solution opérationnelle devant la classe.

### Évaluation

- Évaluation collégiale : chaque élève évaluera les autres groupes en complément de l’évaluation réalisée par l’enseignant.
- Critères : clarté, originalité, robustesse de la solution, qualité du code, pertinence des choix méthodologiques et organisation.

## Utilisation des LLMs

### Outils à disposition

Pour faciliter la réalisation du projet, vous aurez accès à plusieurs ressources avancées :

- **Plateforme Open-WebUI** : intégrant des modèles d'intelligence artificielle d'OpenAI et locaux très performants, ainsi que des plugins spécifiques et une base de connaissances complète alimentée par la bibliographie du cours (indexée via ChromaDB, taper # en conversation pour invoquer les KB).
- **Clés d'API OpenAI et locales** : mise à votre disposition pour exploiter pleinement les capacités des modèles GPT dans vos développements.
- **Notebook Agentique** : un notebook interactif permettant d'automatiser la création ou la finalisation de vos propres notebooks, facilitant ainsi la structuration et l'amélioration de vos solutions.

### Combinaison LLM et CSP

Vous avez également la possibilité d'intégrer les Large Language Models (LLMs) directement dans votre projet CSP afin d'en étendre significativement les capacités, via :

- Une utilisation directe des LLM pour assister la conception ou la résolution de CSP complexes.
- Le recours au "function calling" : fournir à un LLM un accès direct à votre CSP, permettant ainsi au modèle de piloter la résolution du problème de manière plus flexible et intuitive. Le notebook agentique fourni constitue un exemple pratique et efficace de cette méthodologie légère mais puissante. La normalisation en cours des MCPs constitue également un excellent exemple d'application de cette approche (vous développez un MCP utilisant la PrCon dans le cadre de votre projet).

## Sujet sélectionné : 22. Allocation de ressources dans le cloud (VM scheduling)  

**Description :** Dans le cloud computing, on reçoit un ensemble de demandes (machines virtuelles à lancer, tâches à exécuter) et on doit les placer sur des serveurs physiques disponibles. Ce problème comporte des contraintes de capacité (chaque serveur a une RAM, CPU limités), de performance (certaines applications nécessitent d’être sur le même rack, ou au contraire réparties), et souvent des objectifs de coût ou d’équilibrage de charge. On peut formuler cela en CSP : variables = instances ou tâches à placer, domaines = choix de serveurs, contraintes = ne pas dépasser les capacités par serveur, respecter les affinités ou anti-affinités, etc. ([](https://gvpress.com/journals/IJHIT/vol6_no6/30.pdf#:~:text=allocation%20model%3A%20constraint%20programming%20based,is%20modeled%20as%20a%20constraint)). Ce problème est complexe car il combine **satisfaction de contraintes** (trouver un placement valide) et optimisation (minimiser le coût ou l’énergie).  

**Intérêt de l’approche CSP :** La programmation par contraintes offre un cadre souple pour exprimer les diverses politiques d’allocation (contrainte de colocalisation, de redondance, respect des SLA, etc.) et trouver un placement satisfaisant. Des travaux ont montré qu’on peut modéliser l’allocation de machines virtuelles comme un problème de satisfaction de contraintes, puis utiliser un solveur CP pour trouver une solution respectant QoS et coûts ([](https://gvpress.com/journals/IJHIT/vol6_no6/30.pdf#:~:text=resources%28CPU%2C%20RAM%29,an%20economics%20based%20cloud%20computing)) ([](https://gvpress.com/journals/IJHIT/vol6_no6/30.pdf#:~:text=allocation%20model%3A%20constraint%20programming%20based,is%20modeled%20as%20a%20constraint)). L’approche CSP facilite l’ajout de nouvelles contraintes (par exemple, réserver certaines VM sur des serveurs alimentés par énergies renouvelables) sans changer fondamentalement l’algorithme. De plus, grâce aux techniques de filtrage et de propagation, un solveur peut drastiquement réduire l’espace de recherche en éliminant d’office les affectations impossibles (serveur surchargé, combinaison incompatible, etc.). Ceci permet d’aborder des instances plus dynamiques ou complexes que ne pourraient le faire des heuristiques figées, tout en garantissant le respect strict des contraintes critiques (disponibilité, sécurité).  

**Références :** *Zhang et al.*, **Virtual Cloud Resource Allocation model (VCRA-CP)** ([](https://gvpress.com/journals/IJHIT/vol6_no6/30.pdf#:~:text=allocation%20model%3A%20constraint%20programming%20based,is%20modeled%20as%20a%20constraint)) – formalise l’allocation de VMs comme un CSP/optimisation, en montrant son efficacité pour concilier QoS et coûts. *Van et al.* – travaux cités par Zhang où la sélection de machines virtuelles pour des applications est convertie en problème de satisfaction de contraintes pour obtenir un ordonnancement optimal ([](https://gvpress.com/journals/IJHIT/vol6_no6/30.pdf#:~:text=resources%28CPU%2C%20RAM%29,an%20economics%20based%20cloud%20computing)). *Microsoft Learn – Product configuration constraints* – illustre l’utilisation de contraintes (d’expression ou table) pour contrôler les choix de configuration de produits ou ressources dans un configurateur cloud ([foohardt/or-tools-product-configurator - GitHub](https://github.com/foohardt/or-tools-product-configurator#:~:text=foohardt%2For,to%20configure%20a%20product)) (analogie avec VM placement).  

## Authors
Joric HANTZBERG\
Maxime RUFF\
Pierre SCHWEITZER