let landingAuthMode = 'register';
let landingLang = localStorage.getItem('xt_lang') || 'fr';
let selectedBillingPlan = null;

const LANDING_COPY = {
    fr: {
        meta_title: 'XAUTERMINAL - Terminal macro et trading professionnel',
        nav_tools: 'Outils',
        nav_markets: 'Marchés',
        nav_pricing: 'Formules',
        nav_login: 'Connexion',
        nav_terminal: 'Ouvrir le terminal',
        nav_account: 'Mon compte',
        nav_support: 'Support',
        hero_kicker: 'TRADING TERMINAL',
        hero_copy: 'Un poste de travail macro pour suivre les news, le calendrier économique, les drivers de marché et tes charts dans une interface rapide, personnalisable et orientée décision.',
        hero_trial: "Démarrer l'essai 7 jours",
        hero_login: "J'ai déjà un compte",
        preview_volatility: 'Volatilité attendue',
        features_kicker: 'OUTILS',
        features_title: 'Tout ce qui compte avant une décision de marché.',
        feature_calendar_title: 'Calendrier économique intelligent',
        feature_calendar_copy: 'Événements classés par jour, impact, pays et données actual/forecast/previous avec lecture visuelle du résultat.',
        feature_news_title: 'News multi-source filtrées',
        feature_news_copy: 'Le feed priorise les informations récentes selon ton profil de marché: Fed, BoJ, inflation, géopolitique, indices ou crypto.',
        feature_workspace_title: 'Workspace personnalisable',
        feature_workspace_copy: 'Layouts sauvegardés, panels redimensionnables, alertes sonores, watchlist et symboles TradingView adaptés à ton trading.',
        feature_bias_copy: "Un tableau de lecture rapide pour comprendre les pressions macro dominantes avant d'entrer en position.",
        profiles_kicker: 'PROFILS DE MARCHÉ',
        profiles_title: "Un terminal qui s'adapte au marché que tu trades.",
        pricing_kicker: 'FORMULES',
        pricing_title: 'Teste le terminal, puis choisis le rythme qui te convient.',
        pricing_copy: "Chaque compte démarre avec 7 jours d'essai. Ensuite, l'accès reste simple: mensuel, annuel ou lifetime pour les premiers utilisateurs.",
        pricing_monthly_label: 'Mensuel',
        pricing_monthly_period: '/ mois',
        pricing_monthly_copy: 'Accès mensuel renouvelable, annulable pour stopper le prochain renouvellement.',
        pricing_yearly_label: 'Annuel',
        pricing_yearly_period: '/ an',
        pricing_yearly_copy: "Accès annuel avec un prix plus avantageux, engagé sur la période d'un an.",
        pricing_lifetime_label: 'Lifetime',
        pricing_lifetime_period: 'une fois',
        pricing_lifetime_copy: 'Un accès à vie pensé comme offre fondateur, limité tant que le produit se construit.',
        pricing_best_value: 'Meilleur choix',
        pricing_choose: 'Choisir cette formule',
        cta_title: 'Construis ton poste de décision macro.',
        cta_copy: 'Active ton essai gratuit et teste le terminal complet avec ton propre profil de marché.',
        cta_button: 'Créer mon compte',
        auth_register_kicker: 'CRÉATION DE COMPTE',
        auth_login_kicker: 'CONNEXION',
        auth_register_title: "Démarrer l'essai 7 jours",
        auth_login_title: 'Connexion au terminal',
        auth_register_copy: 'Crée ton compte pour ouvrir le terminal complet et sauvegarder ton workspace.',
        auth_login_copy: 'Connecte-toi pour reprendre ton workspace.',
        auth_reset_kicker: 'MOT DE PASSE',
        auth_reset_title: 'Réinitialiser ton mot de passe',
        auth_reset_copy: 'Entre ton email et nous t’enverrons un lien sécurisé pour choisir un nouveau mot de passe.',
        auth_register_submit: 'Créer mon compte',
        auth_login_submit: 'Se connecter',
        auth_reset_submit: 'Envoyer le lien',
        auth_register_switch: "J'ai déjà un compte",
        auth_login_switch: 'Créer un compte',
        auth_reset_switch: 'Retour à la connexion',
        auth_forgot: 'Mot de passe oublié ?',
        password_placeholder: 'Mot de passe (8 caractères min.)',
        auth_loading_login: 'Connexion...',
        auth_loading_register: 'Création du compte...',
        auth_loading_reset: 'Envoi du lien...',
        auth_reset_sent: 'Si un compte existe, un lien de réinitialisation vient d’être envoyé.',
        auth_no_access: 'Compte connecté, mais accès terminal indisponible.',
        auth_success: 'Accès valide. Ouverture du terminal...',
        billing_redirect: 'Redirection vers le paiement...',
        billing_error: 'Paiement indisponible',
        auth_existing_account: 'Compte déjà existant. Connecte-toi pour reprendre le paiement.',
        auth_error: 'Erreur compte',
        terms_title: 'Conditions générales d\'utilisation',
        terms_kicker: 'CGU',
        privacy_title: 'Politique de confidentialité',
        privacy_kicker: 'CONFIDENTIALITÉ',
        risk_title: 'Disclaimer trading et risques',
        risk_kicker: 'RISQUES',
        legal_general: 'Informations générales',
        legal_editor: 'Éditeur',
        legal_business: 'Entreprise',
        legal_status: 'Statut',
        legal_id: 'Identifiant',
        legal_vat: 'TVA intracommunautaire',
        legal_contact: 'Contact',
        legal_address: 'Adresse',
        legal_hosting: 'Hébergement',
        legal_contact_title: 'Contact',
        legal_contact_copy: 'Pour toute question relative aux conditions d\'utilisation, à la confidentialité ou aux risques liés au trading, vous pouvez nous contacter à',
        terms_mediation_title: 'Médiation de la consommation',
        terms_mediation_copy: 'Après une réclamation écrite préalable adressée à XAUTERMINAL restée sans solution satisfaisante, le consommateur peut saisir gratuitement le médiateur de la consommation compétent.',
        terms_mediation_name: 'Médiateur',
        terms_mediation_site: 'Site',
        terms_mediation_address: 'Adresse',
        terms_withdrawal_form_title: 'Formulaire type de rétractation',
        terms_withdrawal_form_copy: "Lorsque le droit de rétractation est applicable, l'utilisateur peut envoyer une demande claire par email à l'adresse de contact, en indiquant son nom, son email de compte, la formule concernée, la date de commande et la phrase: Je vous notifie par la présente ma rétractation du contrat portant sur le service XAUTERMINAL.",
        terms_section1_title: 'Objet du service',
        terms_section1: 'XAUTERMINAL propose un terminal web d\'information macro et marché permettant de consulter des news, un calendrier économique, des graphiques, des watchlists, des widgets de prix et des outils de lecture de contexte. Le service est fourni comme outil d\'aide à l\'organisation et à l\'analyse personnelle.',
        terms_section2_title: 'Accès au service',
        terms_section2: 'L\'accès complet peut être soumis à la création d\'un compte, à une période d\'essai, à un abonnement ou à une offre lifetime. L\'utilisateur s\'engage à fournir des informations exactes et à préserver la confidentialité de ses identifiants.',
        terms_section3_title: 'Essai gratuit et abonnements',
        terms_section3: 'Les formules mensuelle et annuelle peuvent inclure un essai gratuit de 7 jours. Selon la configuration Stripe, une carte bancaire peut être demandée au démarrage de l\'essai afin de préparer le renouvellement. À l\'issue de l\'essai, l\'abonnement choisi démarre automatiquement si le paiement est validé. L\'abonnement mensuel est souscrit pour une période d\'un mois renouvelable. L\'abonnement annuel est souscrit pour une période d\'un an renouvelable. L\'offre lifetime correspond à un paiement unique donnant accès au service tant que celui-ci est exploité.',
        terms_section4_title: 'Paiement',
        terms_section4: 'Les paiements sont traités par Stripe. XAUTERMINAL ne stocke pas les numéros de carte bancaire. Sauf obligation légale contraire, toute période d\'abonnement commencée et payée est due et non remboursable: un mois payé reste dû pour le mois en cours, une année payée reste due pour l\'année en cours. La résiliation met fin au renouvellement automatique à l\'échéance de la période en cours, sans remboursement prorata temporis.',
        terms_section5_title: 'Utilisation acceptable',
        terms_section5: 'L\'utilisateur s\'engage à ne pas perturber le service, contourner les restrictions d\'accès, partager un compte de manière abusive, extraire massivement les données ou utiliser le service à des fins illicites.',
        terms_section6_title: 'Disponibilité',
        terms_section6: 'Le service dépend de fournisseurs tiers, notamment hébergement, données de marché, flux d\'actualité, calendrier économique, graphiques et paiement. Des interruptions, retards, erreurs ou indisponibilités peuvent survenir.',
        terms_section7_title: 'Responsabilité',
        terms_section7: 'XAUTERMINAL ne garantit pas l\'exactitude, l\'exhaustivité, l\'actualité ou la continuité des données affichées. L\'utilisateur reste seul responsable de ses décisions, notamment financières, et de sa gestion du risque.',
        terms_section8_title: 'Rétractation',
        terms_section8: 'Lorsque la loi accorde un droit de rétractation, l\'utilisateur dispose en principe d\'un délai de 14 jours pour l\'exercer à compter de la conclusion du contrat. XAUTERMINAL étant un service numérique accessible immédiatement, l\'utilisateur demande expressément l\'exécution immédiate du service dès la souscription Stripe, y compris pendant l\'essai gratuit, et reconnaît que cette exécution immédiate peut entraîner la perte du droit de rétractation lorsque les conditions légales applicables sont réunies. Pendant l\'essai gratuit, l\'utilisateur peut annuler avant le premier paiement depuis Stripe.',
        terms_section9_title: 'Résiliation',
        terms_section9: 'L\'utilisateur peut demander la résiliation de son abonnement depuis son espace compte ou le portail Stripe. La résiliation d\'un abonnement mensuel ou annuel prend effet à la fin de la période de facturation en cours et n\'annule pas les sommes déjà dues pour cette période.',
        terms_section10_title: 'Modification du service',
        terms_section10: 'Les fonctionnalités, tarifs, offres, sources de données et conditions peuvent évoluer afin d\'améliorer le produit, corriger des erreurs ou tenir compte de contraintes techniques ou commerciales.',
        terms_section11_title: 'Archivage et preuve',
        terms_section11: "Les informations liées au compte, aux paiements, aux abonnements, aux confirmations email et à l'acceptation des conditions peuvent être conservées afin d'assurer la preuve de la relation contractuelle, gérer le support, prévenir la fraude et respecter les obligations légales.",
        terms_section12_title: 'Réclamation',
        terms_section12: "Pour toute réclamation, l'utilisateur doit contacter XAUTERMINAL par email en indiquant l'adresse de compte concernée, le problème rencontré et les justificatifs utiles. XAUTERMINAL s'efforce de répondre dans un délai raisonnable.",
        privacy_section1_title: 'Données collectées',
        privacy_section1: 'XAUTERMINAL peut collecter l\'adresse email, le mot de passe chiffré, les informations de profil renseignées volontairement comme prénom, nom et adresse, les préférences de terminal, l\'état d\'abonnement, les identifiants Stripe nécessaires au suivi du paiement et des données techniques liées à l\'utilisation du service.',
        privacy_section2_title: 'Finalités',
        privacy_section2: 'Ces données servent à créer et sécuriser le compte, gérer l\'accès au terminal, synchroniser les préférences, traiter les abonnements, améliorer le produit et assurer le support utilisateur.',
        privacy_section3_title: 'Paiements',
        privacy_section3: 'Les données de paiement sont traitées par Stripe. XAUTERMINAL conserve uniquement les références techniques utiles au suivi du compte, comme l\'identifiant client, l\'abonnement, le prix sélectionné ou le statut de paiement.',
        privacy_section4_title: 'Cookies et sessions',
        privacy_section4: 'Le service utilise un cookie de session afin de maintenir la connexion au compte. Des préférences peuvent également être conservées localement dans le navigateur pour personnaliser l\'expérience.',
        privacy_section5_title: 'Prestataires',
        privacy_section5: 'Le service peut s\'appuyer sur des prestataires techniques comme Render pour l\'hébergement, Stripe pour le paiement, Financial Modeling Prep, Yahoo Finance, TradingView ou des flux RSS tiers pour les données et l\'affichage.',
        privacy_section6_title: 'Durée de conservation',
        privacy_section6: 'Les données de compte sont conservées tant que le compte existe ou tant que cela est nécessaire pour fournir le service, respecter des obligations légales, gérer un litige ou assurer la sécurité.',
        privacy_section7_title: 'Droits utilisateur',
        privacy_section7: 'L\'utilisateur peut demander l\'accès, la correction ou la suppression de ses données en contactant l\'adresse indiquée sur cette page. Certaines données peuvent être conservées si une obligation légale ou technique l\'impose.',
        privacy_section8_title: 'Sécurité',
        privacy_section8: 'XAUTERMINAL applique des mesures raisonnables pour protéger les comptes et les données. Aucun système n\'étant infaillible, l\'utilisateur doit choisir un mot de passe robuste et éviter de le réutiliser.',
        privacy_section9_title: 'Responsable du traitement et bases légales',
        privacy_section9: "Le responsable du traitement est l'éditeur indiqué dans les mentions légales. Les traitements reposent selon les cas sur l'exécution du contrat, l'intérêt légitime de sécurisation et d'amélioration du service, le respect d'obligations légales ou le consentement lorsque celui-ci est requis.",
        privacy_section10_title: 'Droits RGPD et CNIL',
        privacy_section10: "L'utilisateur peut demander l'accès, la rectification, l'effacement, la limitation, l'opposition au traitement ou la portabilité de ses données lorsque ces droits sont applicables. Il peut également introduire une réclamation auprès de la CNIL.",
        privacy_section11_title: 'Transferts et prestataires hors UE',
        privacy_section11: "Certains prestataires techniques, de paiement, d'email, de données de marché ou d'affichage peuvent traiter des données hors Union européenne. Lorsque cela est nécessaire, XAUTERMINAL s'appuie sur les garanties proposées par ces prestataires, notamment leurs mécanismes contractuels et de conformité.",
        privacy_section12_title: 'Données obligatoires ou facultatives',
        privacy_section12: "L'email, le mot de passe et les informations de paiement nécessaires via Stripe sont requis pour créer un compte et fournir l'accès. Les informations de profil complémentaires sont facultatives, sauf lorsqu'elles sont nécessaires à la facturation, au support ou à une obligation légale.",
        risk_section1_title: 'Information uniquement',
        risk_section1: 'XAUTERMINAL fournit des informations de marché, des outils de visualisation, des classements, des alertes et des lectures de contexte. Le service ne constitue pas un conseil en investissement, une recommandation personnalisée, une gestion de portefeuille, ou une incitation à acheter ou vendre un instrument financier.',
        risk_section2_title: 'Risque de perte',
        risk_section2: 'Le trading, les CFD, le Forex, les cryptomonnaies, les actions, les indices, les matières premières et autres instruments financiers comportent un risque élevé de perte. Les performances passées ne préjugent pas des performances futures.',
        risk_section3_title: 'Données tierces',
        risk_section3: 'Les prix, news, calendriers économiques, impacts, prévisions, données actual/forecast/previous et graphiques peuvent provenir de fournisseurs tiers. Ces informations peuvent être retardées, erronées, incomplètes ou indisponibles.',
        risk_section4_title: 'Bias Desk',
        risk_section4: 'Le Bias Desk et les indicateurs associés sont des outils de lecture mécanique et contextuelle. Ils ne doivent pas être interprétés comme des signaux automatiques ou comme une garantie de résultat.',
        risk_section5_title: 'Responsabilité de l\'utilisateur',
        risk_section5: 'Chaque utilisateur doit effectuer ses propres vérifications, respecter son plan de trading, adapter la taille de ses positions et ne jamais engager de capitaux qu\'il ne peut pas se permettre de perdre.',
        risk_section6_title: 'Aucune garantie',
        risk_section6: 'XAUTERMINAL ne garantit aucun gain, aucune précision parfaite des données, aucune disponibilité continue et aucune adéquation du service à une situation financière particulière.',
    },
    en: {
        meta_title: 'XAUTERMINAL - Professional macro and trading terminal',
        nav_tools: 'Tools',
        nav_markets: 'Markets',
        nav_pricing: 'Plans',
        nav_login: 'Login',
        nav_terminal: 'Open terminal',
        nav_account: 'My account',
        nav_support: 'Support',
        hero_kicker: 'TRADING TERMINAL',
        hero_copy: 'A macro workstation to track news, the economic calendar, market drivers and your charts in a fast, customizable, decision-focused interface.',
        hero_trial: 'Start 7-day trial',
        hero_login: 'I already have an account',
        preview_volatility: 'Expected volatility',
        features_kicker: 'TOOLS',
        features_title: 'Everything that matters before a market decision.',
        feature_calendar_title: 'Smart economic calendar',
        feature_calendar_copy: 'Events organized by day, impact and country, with actual/forecast/previous data and visual result reading.',
        feature_news_title: 'Filtered multi-source news',
        feature_news_copy: 'The feed prioritizes recent information for your market profile: Fed, BoJ, inflation, geopolitics, indices or crypto.',
        feature_workspace_title: 'Customizable workspace',
        feature_workspace_copy: 'Saved layouts, resizable panels, sound alerts, watchlists and TradingView symbols adapted to your trading.',
        feature_bias_copy: 'A fast reading desk to understand dominant macro pressure before taking a trade.',
        profiles_kicker: 'MARKET PROFILES',
        profiles_title: 'A terminal that adapts to the market you trade.',
        pricing_kicker: 'PLANS',
        pricing_title: 'Try the terminal, then choose the rhythm that fits you.',
        pricing_copy: 'Every account starts with a 7-day trial. After that, access stays simple: monthly, yearly or lifetime for early users.',
        pricing_monthly_label: 'Monthly',
        pricing_monthly_period: '/ month',
        pricing_monthly_copy: 'Monthly renewable access, cancelable to stop the next renewal.',
        pricing_yearly_label: 'Yearly',
        pricing_yearly_period: '/ year',
        pricing_yearly_copy: 'Yearly access with a better price, committed for the one-year period.',
        pricing_lifetime_label: 'Lifetime',
        pricing_lifetime_period: 'one time',
        pricing_lifetime_copy: 'Lifetime access as a founder offer, limited while the product is still being built.',
        pricing_best_value: 'Best value',
        pricing_choose: 'Choose this plan',
        cta_title: 'Build your macro decision desk.',
        cta_copy: 'Start your free trial and test the full terminal with your own market profile.',
        cta_button: 'Create my account',
        auth_register_kicker: 'ACCOUNT CREATION',
        auth_login_kicker: 'LOGIN',
        auth_register_title: 'Start your 7-day trial',
        auth_login_title: 'Login to the terminal',
        auth_register_copy: 'Create your account to open the full terminal and save your workspace.',
        auth_login_copy: 'Login to resume your workspace.',
        auth_reset_kicker: 'PASSWORD',
        auth_reset_title: 'Reset your password',
        auth_reset_copy: 'Enter your email and we will send a secure link to choose a new password.',
        auth_register_submit: 'Create my account',
        auth_login_submit: 'Login',
        auth_reset_submit: 'Send link',
        auth_register_switch: 'I already have an account',
        auth_login_switch: 'Create an account',
        auth_reset_switch: 'Back to login',
        auth_forgot: 'Forgot password?',
        password_placeholder: 'Password (8 characters min.)',
        auth_loading_login: 'Logging in...',
        auth_loading_register: 'Creating account...',
        auth_loading_reset: 'Sending link...',
        auth_reset_sent: 'If an account exists, a reset link has been sent.',
        auth_no_access: 'Account connected, but terminal access is unavailable.',
        auth_success: 'Access valid. Opening terminal...',
        billing_redirect: 'Redirecting to payment...',
        billing_error: 'Payment unavailable',
        auth_existing_account: 'Account already exists. Log in to resume payment.',
        auth_error: 'Account error',
        terms_title: 'Terms and Conditions',
        terms_kicker: 'TERMS',
        privacy_title: 'Privacy Policy',
        privacy_kicker: 'PRIVACY',
        risk_title: 'Trading Disclaimer and Risks',
        risk_kicker: 'RISKS',
        legal_general: 'General Information',
        legal_editor: 'Editor',
        legal_business: 'Business',
        legal_status: 'Status',
        legal_id: 'Identifier',
        legal_vat: 'EU VAT ID',
        legal_contact: 'Contact',
        legal_address: 'Address',
        legal_hosting: 'Hosting',
        legal_contact_title: 'Contact',
        legal_contact_copy: 'For any questions regarding terms of use, privacy, or trading risks, please contact us at',
        terms_mediation_title: 'Consumer Mediation',
        terms_mediation_copy: 'After a prior written complaint sent to XAUTERMINAL that has not resulted in a satisfactory solution, consumers may contact the competent consumer mediator free of charge.',
        terms_mediation_name: 'Mediator',
        terms_mediation_site: 'Website',
        terms_mediation_address: 'Address',
        terms_withdrawal_form_title: 'Withdrawal Form Template',
        terms_withdrawal_form_copy: 'Where the withdrawal right applies, users may send a clear request by email to the contact address, stating their name, account email, selected plan, order date and the sentence: I hereby notify you of my withdrawal from the contract for the XAUTERMINAL service.',
        terms_section1_title: 'Service Purpose',
        terms_section1: 'XAUTERMINAL provides a web terminal for macro and market information, allowing users to view news, economic calendar, charts, watchlists, price widgets and context reading tools. The service is provided as a personal analysis and organization aid tool.',
        terms_section2_title: 'Service Access',
        terms_section2: 'Full access may require account creation, trial period, subscription or lifetime offer. Users agree to provide accurate information and keep their credentials confidential.',
        terms_section3_title: 'Free Trial and Subscriptions',
        terms_section3: 'Monthly and yearly plans may include a 7-day free trial. Depending on Stripe configuration, a card may be required at trial start to set up renewal. After the trial, the selected subscription starts automatically if payment is validated. The monthly subscription is entered into for a renewable one-month period. The yearly subscription is entered into for a renewable one-year period. The lifetime offer is a single payment giving access to the service while it exists.',
        terms_section4_title: 'Payment',
        terms_section4: 'Payments are processed by Stripe. XAUTERMINAL does not store card numbers. Unless legally required otherwise, any paid subscription period that has started is due and non-refundable: a paid month remains due for the current month, and a paid year remains due for the current year. Cancellation stops automatic renewal at the end of the current period, without prorated refund.',
        terms_section5_title: 'Acceptable Use',
        terms_section5: 'Users agree not to disrupt the service, bypass access restrictions, abusively share an account, mass extract data or use the service for unlawful purposes.',
        terms_section6_title: 'Availability',
        terms_section6: 'The service depends on third-party providers, including hosting, market data, news feeds, economic calendar, charts and payment. Interruptions, delays, errors or unavailability may occur.',
        terms_section7_title: 'Liability',
        terms_section7: 'XAUTERMINAL does not guarantee accuracy, completeness, timeliness or continuity of displayed data. Users are solely responsible for their decisions, including financial, and risk management.',
        terms_section8_title: 'Withdrawal Right',
        terms_section8: 'Where the law grants a withdrawal right, users generally have 14 days to exercise it from contract conclusion. Since XAUTERMINAL is a digital service made available immediately, the user expressly requests immediate performance from the Stripe subscription, including during the free trial, and acknowledges that this immediate performance may result in loss of the withdrawal right where applicable legal conditions are met. During the free trial, the user may cancel before the first payment through Stripe.',
        terms_section9_title: 'Cancellation',
        terms_section9: 'Users may cancel their subscription from their account area or the Stripe portal. Cancellation of a monthly or yearly subscription takes effect at the end of the current billing period and does not cancel amounts already due for that period.',
        terms_section10_title: 'Service Modification',
        terms_section10: 'Features, pricing, offers, data sources and conditions may change to improve the product, fix errors or address technical or commercial constraints.',
        terms_section11_title: 'Archiving and Evidence',
        terms_section11: 'Information related to accounts, payments, subscriptions, email confirmations and acceptance of terms may be retained to evidence the contractual relationship, manage support, prevent fraud and comply with legal obligations.',
        terms_section12_title: 'Complaints',
        terms_section12: 'For any complaint, users should contact XAUTERMINAL by email and provide the relevant account email, the issue encountered and useful supporting information. XAUTERMINAL will make reasonable efforts to respond within a reasonable timeframe.',
        privacy_section1_title: 'Data Collected',
        privacy_section1: 'XAUTERMINAL may collect email address, encrypted password, profile information voluntarily entered such as first name, last name and address, terminal preferences, subscription status, Stripe identifiers needed for payment tracking and technical data related to service usage.',
        privacy_section2_title: 'Purposes',
        privacy_section2: 'This data is used to create and secure accounts, manage terminal access, sync preferences, process subscriptions, improve the product and provide user support.',
        privacy_section3_title: 'Payments',
        privacy_section3: 'Payment data is processed by Stripe. XAUTERMINAL only keeps technical references useful for account tracking, such as customer ID, subscription, selected price or payment status.',
        privacy_section4_title: 'Cookies and Sessions',
        privacy_section4: 'The service uses session cookies to maintain account connection. Preferences may also be stored locally in the browser to customize experience.',
        privacy_section5_title: 'Service Providers',
        privacy_section5: 'The service may rely on technical providers like Render for hosting, Stripe for payment, Financial Modeling Prep, Yahoo Finance, TradingView or third-party RSS feeds for data and display.',
        privacy_section6_title: 'Data Retention',
        privacy_section6: 'Account data is retained as long as the account exists or as necessary to provide the service, meet legal obligations, manage disputes or ensure security.',
        privacy_section7_title: 'User Rights',
        privacy_section7: 'Users can request access, correction or deletion of their data by contacting the address listed on this page. Some data may be retained if required by law or technical necessity.',
        privacy_section8_title: 'Security',
        privacy_section8: 'XAUTERMINAL applies reasonable measures to protect accounts and data. Since no system is infallible, users should choose a strong password and avoid reuse.',
        privacy_section9_title: 'Controller and Legal Bases',
        privacy_section9: 'The data controller is the publisher listed in the legal notice. Processing is based, depending on the case, on contract performance, legitimate interest in securing and improving the service, compliance with legal obligations or consent where required.',
        privacy_section10_title: 'GDPR Rights and Supervisory Authority',
        privacy_section10: 'Users may request access, rectification, erasure, restriction, objection to processing or portability of their data where these rights apply. They may also lodge a complaint with the French data protection authority, the CNIL.',
        privacy_section11_title: 'Transfers and Non-EU Providers',
        privacy_section11: 'Some technical, payment, email, market data or display providers may process data outside the European Union. Where necessary, XAUTERMINAL relies on safeguards offered by these providers, including their contractual and compliance mechanisms.',
        privacy_section12_title: 'Required or Optional Data',
        privacy_section12: 'Email, password and payment information required through Stripe are needed to create an account and provide access. Additional profile information is optional unless required for billing, support or a legal obligation.',
        risk_section1_title: 'Information Only',
        risk_section1: 'XAUTERMINAL provides market information, visualization tools, rankings, alerts and context reading. The service is not investment advice, personalized recommendations, portfolio management, or encouragement to buy or sell any financial instrument.',
        risk_section2_title: 'Loss Risk',
        risk_section2: 'Trading, CFDs, Forex, cryptocurrencies, stocks, indices, commodities and other financial instruments carry high loss risk. Past performance does not guarantee future results.',
        risk_section3_title: 'Third-Party Data',
        risk_section3: 'Prices, news, economic calendars, impacts, forecasts, actual/previous data and charts may come from third parties. This information may be delayed, inaccurate, incomplete or unavailable.',
        risk_section4_title: 'Bias Desk',
        risk_section4: 'The Bias Desk and associated indicators are mechanical and contextual reading tools. They should not be interpreted as automatic signals or performance guarantees.',
        risk_section5_title: 'User Responsibility',
        risk_section5: 'Each user must perform their own verification, follow their trading plan, size positions appropriately and never commit capital they cannot afford to lose.',
        risk_section6_title: 'No Warranty',
        risk_section6: 'XAUTERMINAL makes no warranty of any gain, perfect data accuracy, continuous availability or suitability for any particular financial situation.',
    },
};

const SEO_COPY = {
    fr: {
        proof_news: 'News multi-source',
        proof_calendar: 'Calendrier macro',
        proof_profiles: 'Profils XAU, Forex, Indices, Crypto',
        feature_bias_title: 'Bias desk et drivers',
        resources_kicker: 'RESSOURCES',
        resources_title: "Comprendre le contexte avant d'ouvrir le terminal.",
        resources_intro: 'Accède rapidement aux guides, aux pages XAU/USD et aux explications macro pour mieux comprendre ce que le terminal rassemble.',
        resources_cta: 'Voir toutes les ressources',
        guides_cta: 'Voir les guides trading',
        nav_pulse: 'Market Pulse',
        pulse_kicker: 'MARKET PULSE',
        pulse_title: "Une lecture rapide de ce qui compte aujourd'hui.",
        pulse_intro: "Market Pulse transforme les news, le calendrier, les drivers macro et les actifs surveillés en briefing lisible avant d'ouvrir le terminal.",
        pulse_cta: 'Voir Market Pulse',
        pulse_trial: 'Tester le terminal',
        pulse_context_label: 'Contexte macro',
        pulse_context_value: 'Risque élevé avant données US',
        pulse_context_copy: 'Le terminal met en évidence les séances où le calendrier, le dollar, les taux ou les news peuvent changer la lecture du marché.',
        pulse_xau_copy: 'Or sensible à DXY, US10Y et inflation.',
        pulse_dxy_value: 'À surveiller',
        pulse_dxy_copy: 'Pression dollar et rendements US.',
        pulse_calendar_label: 'Calendrier',
        pulse_calendar_copy: 'Publication à fort impact avant session US.',
        pulse_page_title: 'Market Pulse - Analyse marché du jour',
        pulse_page_description: 'Market Pulse XAUTERMINAL synthétise le contexte macro, les actifs à surveiller, les news importantes et le calendrier économique avant une session de trading.',
        pulse_page_kicker: 'MARKET PULSE',
        pulse_page_h1: "Le briefing de marché avant d'ouvrir le terminal",
        pulse_page_intro: "Market Pulse rassemble la lecture macro essentielle: calendrier du jour, news qui comptent, actifs à surveiller, niveau de risque et biais de contexte. L'objectif est simple: savoir où regarder avant de prendre une décision.",
        pulse_page_trial: 'Tester XAUTERMINAL',
        pulse_board_today: "AUJOURD'HUI",
        pulse_board_risk: 'Risque élevé',
        pulse_board_score: 'Contexte actif avant données US',
        pulse_board_dxy: 'Fort',
        pulse_board_yields: 'Pression',
        pulse_board_news_label: 'News',
        pulse_live_updated: 'Mis à jour',
        pulse_live_news_kicker: 'NEWS LIVE',
        pulse_live_news_title: 'Titres importants récents',
        pulse_live_calendar_kicker: 'CALENDRIER',
        pulse_live_calendar_title: 'Événements à venir',
        pulse_drivers_kicker: 'DRIVERS PUBLICS',
        pulse_drivers_title: 'Ce qui influence le contexte',
        pulse_page_card_calendar_title: 'Calendrier à risque',
        pulse_page_card_calendar_copy: "Repère les publications qui peuvent changer la volatilité: CPI, PCE, NFP, FOMC, PMI ou discours de banques centrales.",
        pulse_page_card_news_title: 'News qui comptent',
        pulse_page_card_news_copy: 'Filtre les titres qui influencent vraiment le dollar, les taux, le sentiment de risque ou les actifs de ta watchlist.',
        pulse_page_card_drivers_title: 'Drivers macro',
        pulse_page_card_drivers_copy: "Compare DXY, US10Y, inflation, Fed, stress géopolitique et momentum pour comprendre ce qui domine la séance.",
        pulse_page_card_watchlist_title: 'Radar actifs',
        pulse_page_card_watchlist_copy: 'Prépare les marchés à surveiller avant de passer au graphique: XAU/USD, Forex, indices, DXY, taux et crypto.',
        pulse_workflow_kicker: 'ROUTINE',
        pulse_workflow_title: 'Une routine en quatre lectures',
        pulse_workflow_copy: "Les meilleurs terminaux ne montrent pas seulement des données: ils aident à décider quelles données méritent ton attention. Market Pulse sert de première couche avant le charting.",
        pulse_step1_title: 'Calendrier',
        pulse_step1_copy: 'Repérer les horaires à risque et les publications capables de déplacer le dollar, les taux ou les indices.',
        pulse_step2_title: 'News',
        pulse_step2_copy: 'Filtrer les titres vraiment liés au thème dominant de la séance.',
        pulse_step3_title: 'Drivers',
        pulse_step3_copy: 'Comparer dollar, rendements, sentiment de risque et momentum du prix.',
        pulse_step4_title: 'Plan',
        pulse_step4_copy: 'Passer au terminal avec une watchlist claire, pas avec dix onglets ouverts au hasard.',
        pulse_assets_kicker: 'RADAR MARCHÉS',
        pulse_assets_title: 'Les marchés qui méritent une lecture dédiée',
        pulse_asset_gold: 'Or et macro US',
        pulse_asset_eurusd: 'Dollar et BCE',
        pulse_asset_gbpjpy: 'Volatilité FX',
        pulse_asset_nasdaq: 'Taux et risk-on',
        pulse_asset_dxy: 'Force dollar',
        pulse_asset_us10y: 'Rendements US',
        pulse_final_title: 'Pourquoi ajouter Market Pulse à XAUTERMINAL ?',
        pulse_final_copy: "Parce que le vrai problème d'un trader n'est pas seulement de trouver des données, mais de les hiérarchiser. Market Pulse donne une porte d'entrée claire avant le terminal complet, les graphiques et le Bias Desk.",
        resources_deep_kicker: 'LECTURES UTILES',
        resources_deep_title: 'Approfondir les pages liées au terminal.',
        learning_guides_kicker: 'GUIDES',
        learning_guides_title: 'Guides trading XAU/USD, macro et Bias Desk',
        learning_guides_copy: 'Construis une routine de marché claire autour du dollar, des taux US, des news et du Bias Desk.',
        learning_open_guides: 'Ouvrir les guides',
        learning_xau_kicker: 'XAU/USD',
        learning_macro_kicker: 'MACRO',
        learning_read_page: 'Lire la page',
        nav_resources: 'Ressources',
        nav_guides: 'Guides',
        resource_terminal_title: 'Terminal XAU/USD',
        resource_terminal_copy: "Pourquoi l'or demande une lecture croisée du dollar, des taux US, de la Fed, de l'inflation et du momentum.",
        resource_calendar_title: "Calendrier économique pour l'or",
        resource_calendar_copy: 'Les publications à surveiller sur XAU/USD: CPI, PCE, NFP, FOMC, discours Fed et statistiques US.',
        resource_news_title: 'News Forex et or',
        resource_news_copy: "Comment filtrer les headlines utiles pour comprendre les mouvements du dollar, des rendements et de l'or.",
        resource_guide_title: "Guide macro pour trader l'or",
        resource_guide_copy: 'Une lecture pédagogique des principaux drivers macro: DXY, US10Y, inflation, Fed et stress de marché.',
        trust_kicker: 'CONFIANCE',
        trust_title: "Un terminal d'analyse, pas une promesse magique.",
        trust_copy: "XAUTERMINAL est conçu pour organiser ta lecture du marché avant une décision. Le service reste transparent sur ses limites, son paiement et la gestion du risque.",
        trust_is_title: "Ce que c'est",
        trust_is_copy: 'Un espace pour centraliser news, calendrier, graphiques, watchlist, drivers macro et Bias Desk dans une même routine.',
        trust_not_title: "Ce que ce n'est pas",
        trust_not_copy: 'Pas un robot de trading, pas un vendeur de signaux garantis, pas un conseil financier personnalisé.',
        trust_payment_title: 'Paiement clair',
        trust_payment_copy: "Stripe gère l'essai, les paiements, les factures et les abonnements. XAUTERMINAL ne stocke pas les numéros de carte.",
        trust_control_title: 'Contrôle utilisateur',
        trust_control_copy: 'Depuis Mon compte, tu peux suivre ton accès, gérer ton profil, ton abonnement et contacter le support si besoin.',
        resource_terminal_short: 'XAU/USD',
        resource_calendar_short: 'Calendrier or',
        resource_news_short: 'News forex',
        resource_guide_short: 'Guide macro',
        pricing_point_trial: 'Essai gratuit 7 jours',
        pricing_point_monthly: 'Renouvellement mensuel',
        pricing_point_cancel: 'Résiliation à échéance depuis Stripe',
        pricing_point_yearly_saving: 'Environ 2 mois offerts',
        pricing_point_full_access: 'Accès complet au terminal',
        pricing_point_one_time: 'Paiement unique',
        pricing_point_lifetime: 'Accès lifetime au terminal',
        pricing_point_founder: 'Offre fondateur limitée',
        pricing_note_title: 'Essai et paiement sécurisé',
        pricing_note_copy: "Pour les abonnements mensuel et annuel, Stripe peut demander une carte afin d'activer l'essai gratuit de 7 jours et préparer le renouvellement. Aucun débit d'abonnement n'est prévu avant la fin de l'essai. Après facturation, la période mensuelle ou annuelle commencée est due et non remboursable, sauf obligation légale contraire. La résiliation stoppe le renouvellement suivant.",
        faq_trial_title: 'Que se passe-t-il après les 7 jours ?',
        faq_trial_copy: "L'abonnement choisi démarre automatiquement si le paiement est validé par Stripe. Tu peux annuler pendant l'essai depuis Stripe avant le premier débit. Après facturation, la période en cours reste due.",
        legal_confirm_subscription: "En continuant vers Stripe, tu acceptes les CGU, la politique de confidentialité et les conditions d'abonnement. Tu demandes l'accès immédiat au service numérique XAUTERMINAL dès la souscription Stripe, y compris pendant l'essai gratuit de 7 jours, et tu reconnais que cette exécution immédiate peut entraîner la perte du droit de rétractation lorsque les conditions légales sont réunies. L'abonnement se renouvelle automatiquement après l'essai sauf résiliation avant échéance. Continuer ?",
        legal_confirm_lifetime: "En continuant vers Stripe, tu acceptes les CGU, la politique de confidentialité et les conditions de l'offre lifetime. Tu demandes l'accès immédiat au service numérique XAUTERMINAL dès le paiement et tu reconnais que cette exécution immédiate peut entraîner la perte du droit de rétractation lorsque les conditions légales sont réunies. L'offre lifetime est un paiement unique, non remboursable sauf obligation légale contraire. Continuer ?",
        faq_signals_title: 'Le terminal donne-t-il des signaux ?',
        faq_signals_copy: "Non. XAUTERMINAL est un outil d'aide à la décision: news, calendrier, drivers, bias et charting. Il ne remplace pas ta stratégie ni ta gestion du risque.",
        faq_markets_title: 'Puis-je changer de marché ?',
        faq_markets_copy: 'Oui. Les profils XAU/USD, Forex, indices et crypto adaptent le calendrier, le flux news, le Bias Desk et la watchlist.',
        faq_payments_title: 'Mes paiements sont-ils sécurisés ?',
        faq_payments_copy: 'Les paiements et abonnements sont traités par Stripe. XAUTERMINAL ne stocke pas les numéros de carte bancaire.',
        footer_tagline: "Terminal macro et trading professionnel. Outil d'information, pas un conseil financier.",
        footer_trial: "Démarrer l'essai",
        footer_product: 'Produit',
        footer_learn: 'Apprendre',
        footer_markets: 'Marchés et données',
        footer_account: 'Compte',
        footer_legal: 'Légal',
        footer_dxy_rates: 'DXY et taux US',
        footer_bias_desk: 'Bias Desk',
        footer_subscriptions: 'Abonnements',
        footer_contact: 'Contact',
        footer_risk: "Le trading comporte un risque de perte. XAUTERMINAL fournit des informations de marché et des outils d'organisation, sans conseil financier personnalisé.",
        risk_footer_link: 'Disclaimer trading',
        resources_page_title: 'Ressources trading macro, XAU/USD et calendrier économique',
        resources_page_description: "Guides XAUTERMINAL pour comprendre XAU/USD, le calendrier économique de l'or, les news Forex et les principaux drivers macro.",
        resources_page_h1: 'Ressources trading macro, XAU/USD et calendrier économique',
        resources_page_intro: "Ces pages expliquent les concepts réellement liés à XAUTERMINAL: lecture macro de l'or, événements économiques, news Forex et organisation d'une routine de marché. Elles servent à comprendre le produit avant de l'utiliser dans le terminal.",
        resources_page_read: 'Lire',
        guides_page_title: 'Guides trading XAU/USD, macro et Bias Desk',
        guides_page_description: 'Guides XAUTERMINAL pour préparer une session XAU/USD, comprendre DXY, les taux US, les news macro et utiliser un Bias Desk.',
        guides_page_kicker: 'GUIDES TRADING',
        guides_page_h1: 'Guides trading XAU/USD, macro et Bias Desk',
        guides_page_intro: 'Ces guides servent à construire une routine claire autour du terminal: préparer une session, lire DXY et les taux US, filtrer les news et utiliser le Bias Desk sans le confondre avec un signal automatique.',
        guides_page_next_title: 'Utiliser les guides avec le terminal',
        guides_page_next_copy: 'Commence par comprendre la routine, puis ouvre le terminal pour vérifier le calendrier, les news, le graphique et les drivers en conditions réelles.',
        guides_page_trial: 'Tester XAUTERMINAL',
        guides_page_resources: 'Voir toutes les ressources',
        resources_panel_kicker: 'HUB PUBLIC',
        resources_panel_title: "Comprendre avant d'agir",
        resources_panel_copy: "Chaque page relie une notion de marché à l'usage concret du terminal: news, calendrier, drivers et graphique.",
        guides_panel_kicker: 'ROUTINE',
        guides_panel_title: 'Passer du bruit au plan',
        guides_panel_copy: "Les guides sont pensés comme des points d'entrée rapides avant d'ouvrir le terminal et d'observer les drivers réels.",
        article_panel_kicker: 'À LIRE AVEC',
        article_panel_copy: 'Utilise cette ressource avec le calendrier, les news, les graphiques et le Bias Desk pour garder une lecture de marché structurée.',
        article_summary: 'Sommaire',
        article_related: 'Liens utiles',
        seo_continue_title: 'Continuer avec XAUTERMINAL',
        seo_continue_copy: "Ces ressources sont pensées pour être utilisées ensemble: contexte macro, calendrier économique, news filtrées et charting. Pour tester l'espace complet, reviens sur la landing et démarre l'essai depuis le parcours officiel.",
        seo_faq_kicker: 'FAQ',
        seo_faq_title: 'Questions fréquentes',
        support_title: 'Support XAUTERMINAL',
        support_description: 'Aide XAUTERMINAL pour les comptes, codes email, paiements Stripe, abonnements, accès au terminal et sécurité.',
        support_kicker: 'SUPPORT',
        support_h1: 'Aide et support XAUTERMINAL',
        support_intro: 'Retrouve les réponses aux situations les plus fréquentes: validation email, accès au terminal, paiement Stripe, abonnement, mot de passe et sécurité du compte.',
        support_action_account: 'Ouvrir mon compte',
        support_action_plans: 'Voir les formules',
        support_action_password: 'Réinitialiser mon mot de passe',
        support_card_code_title: "Je n'ai pas reçu mon code",
        support_card_code_copy: "Vérifie les spams, promotions et l'orthographe de ton email. Tu peux te reconnecter avec le même email: XAUTERMINAL renverra un nouveau code si le compte n'est pas encore confirmé.",
        support_card_paid_title: "J'ai payé mais je n'ai pas accès",
        support_card_paid_copy: "Reconnecte-toi puis ouvre Mon compte. Si le retour Stripe a été interrompu, le site tente de resynchroniser l'accès. Si le blocage continue, contacte le support avec ton email de compte.",
        support_card_password_title: 'Mot de passe oublié',
        support_card_password_copy: "Utilise la page de réinitialisation pour recevoir un lien sécurisé. Le lien expire automatiquement et ne doit jamais être partagé.",
        support_card_subscription_title: 'Gérer mon abonnement',
        support_card_subscription_copy: "Depuis Mon compte, utilise le bouton Stripe pour gérer ton moyen de paiement, ton abonnement ou tes factures. XAUTERMINAL ne stocke pas les numéros de carte.",
        support_card_terminal_title: "Accès au terminal",
        support_card_terminal_copy: "Le terminal complet est réservé aux comptes confirmés avec un essai ou abonnement actif. Si ton compte est confirmé mais sans formule Stripe, choisis une formule depuis la landing ou Mon compte.",
        support_card_security_title: 'Sécurité du compte',
        support_card_security_copy: "Utilise un mot de passe unique, garde ton email accessible et évite de partager ton compte. En cas de doute, change ton mot de passe depuis l'espace compte.",
        support_process_title: 'Avant de contacter le support',
        support_process_1: 'Vérifie que ton email est bien confirmé avec le dernier code reçu.',
        support_process_2: 'Si tu as payé, reconnecte-toi puis ouvre ton espace Mon compte pour relancer la synchronisation automatique.',
        support_process_3: "Si l'accès reste bloqué, contacte le support avec ton email de compte et, si possible, l'heure du paiement Stripe.",
        support_contact_title: 'Contacter XAUTERMINAL',
        support_contact_copy: 'Pour une demande compte, paiement ou accès terminal, écris-nous à',
        seo_terminal_xauusd_title: "Terminal XAU/USD pour suivre l'or, le dollar et les taux",
        seo_terminal_xauusd_description: "Comprendre comment XAUTERMINAL aide à suivre XAU/USD avec charting, news macro, calendrier économique, DXY, taux US et drivers de marché.",
        seo_terminal_xauusd_kicker: 'XAU/USD',
        seo_terminal_xauusd_h1: "Terminal XAU/USD: suivre l'or avec une lecture macro claire",
        seo_terminal_xauusd_intro: "XAU/USD réagit souvent à plusieurs forces en même temps: dollar américain, taux US, inflation, discours de la Fed, stress géopolitique et momentum court terme. XAUTERMINAL rassemble ces informations dans une interface pensée pour préparer une décision, pas pour remplacer une stratégie.",
        seo_terminal_xauusd_section1_title: 'Pourquoi XAU/USD demande une lecture multi-facteurs',
        seo_terminal_xauusd_section1_copy: "L'or peut monter parce que le dollar baisse, parce que les rendements réels se détendent, parce qu'un risque géopolitique soutient la demande refuge ou simplement parce que le momentum technique domine la séance. Regarder uniquement le graphique peut donc laisser une partie importante du contexte de côté.",
        seo_terminal_xauusd_section2_title: "Ce que le terminal centralise pour l'or",
        seo_terminal_xauusd_section2_copy: "Le profil XAU/USD regroupe le charting TradingView, les news liées à la Fed, au dollar, aux taux, à l'inflation et à la géopolitique, le calendrier économique US, une watchlist orientée or et un Bias Desk qui synthétise les drivers principaux.",
        seo_terminal_xauusd_section3_title: 'Comment utiliser cette page dans une routine',
        seo_terminal_xauusd_section3_copy: "Avant une session, vérifie les événements US à venir, lis les news prioritaires, observe DXY et US10Y, puis compare ce contexte avec le mouvement de XAU/USD. L'objectif est d'éviter d'entrer sans savoir quel facteur domine le marché.",
        seo_terminal_xauusd_section4_title: 'Limite importante',
        seo_terminal_xauusd_section4_copy: 'Le terminal ne fournit pas de conseil financier ni de signal garanti. Il sert à structurer l’information et à gagner du temps dans l’analyse. La décision, le risque et la gestion de position restent sous ta responsabilité.',
        seo_terminal_xauusd_section5_title: 'Routine simple avant une session XAU/USD',
        seo_terminal_xauusd_section5_copy: "Une routine efficace commence par les événements macro du jour, puis les thèmes dominants: inflation, Fed, dollar, rendements, risque géopolitique et sentiment global. Ensuite seulement, le graphique permet de vérifier si le prix confirme ou contredit ce contexte.",
        seo_terminal_xauusd_section6_title: 'Pourquoi XAUTERMINAL existe',
        seo_terminal_xauusd_section6_copy: "L'objectif n'est pas d'ajouter un écran de plus, mais de réduire les allers-retours entre calendrier, news, watchlist, graphique et notes de contexte. Une lecture plus organisée aide à éviter les décisions prises uniquement sous pression ou sur une seule information.",
        seo_terminal_xauusd_faq1_question: 'XAUTERMINAL est-il seulement fait pour XAU/USD ?',
        seo_terminal_xauusd_faq1_answer: 'Non. XAU/USD est le marché central du projet, mais le terminal propose aussi des profils Forex, indices et crypto pour adapter les news, la watchlist et le contexte.',
        seo_terminal_xauusd_faq2_question: 'Le terminal remplace-t-il une stratégie de trading ?',
        seo_terminal_xauusd_faq2_answer: "Non. Il sert à organiser l'information et à préparer une décision. La stratégie, le timing, le risque et l'exécution restent sous la responsabilité de l'utilisateur.",
        seo_terminal_xauusd_link1: "Démarrer l'essai XAUTERMINAL",
        seo_terminal_xauusd_link2: "Lire le calendrier économique pour l'or",
        seo_terminal_xauusd_link3: "Comprendre la lecture macro de l'or",
        seo_calendrier_or_title: "Calendrier économique pour trader l'or: CPI, NFP, Fed et taux US",
        seo_calendrier_or_description: "Guide pratique pour lire le calendrier économique quand on suit l'or et XAU/USD: inflation, NFP, Fed, taux US, dollar et volatilité.",
        seo_calendrier_or_kicker: 'CALENDRIER ÉCONOMIQUE',
        seo_calendrier_or_h1: "Calendrier économique pour l'or: les événements à surveiller sur XAU/USD",
        seo_calendrier_or_intro: "Sur XAU/USD, certaines statistiques peuvent changer brutalement la lecture du marché. L'inflation, l'emploi américain, les décisions de la Fed et les publications liées à la croissance influencent le dollar, les taux et donc l'or.",
        seo_calendrier_or_section1_title: 'Les publications qui comptent le plus',
        seo_calendrier_or_section1_copy: "Les traders sur l'or surveillent notamment le CPI, le PCE, les NFP, le chômage, les ventes au détail, les PMI, les décisions FOMC et les discours de membres de la Fed. Ces événements peuvent modifier les anticipations de taux et déclencher une forte volatilité.",
        seo_calendrier_or_section2_title: 'Actual, forecast, previous: quoi comparer ?',
        seo_calendrier_or_section2_copy: "Une publication se lit rarement seule. Il faut comparer le chiffre publié au consensus et au chiffre précédent. Un résultat supérieur aux attentes peut soutenir le dollar ou les taux selon le contexte, ce qui peut peser sur l'or. L'inverse peut soutenir XAU/USD.",
        seo_calendrier_or_section3_title: 'Pourquoi le timing est important',
        seo_calendrier_or_section3_copy: 'Les minutes avant et après une publication importante sont souvent instables. Le terminal met en avant les événements à fort impact et les blocs de release pour éviter de découvrir trop tard qu’une statistique majeure arrive.',
        seo_calendrier_or_section4_title: 'Utiliser le calendrier avec le reste du contexte',
        seo_calendrier_or_section4_copy: "Un calendrier seul ne suffit pas. Il faut le croiser avec les news, DXY, US10Y, le niveau de volatilité et le comportement du prix. C'est cette combinaison que XAUTERMINAL cherche à rendre plus lisible.",
        seo_calendrier_or_section5_title: 'Préparer les annonces plutôt que les subir',
        seo_calendrier_or_section5_copy: "L'intérêt d'un calendrier n'est pas seulement de connaître l'heure d'une annonce. Il permet de décider à l'avance si l'on évite une zone de volatilité, si l'on attend la réaction du marché ou si l'on adapte son plan de risque.",
        seo_calendrier_or_section6_title: 'Les annonces ne se lisent pas toutes pareil',
        seo_calendrier_or_section6_copy: "Une même surprise peut avoir un effet différent selon le contexte. Un CPI supérieur aux attentes ne produit pas toujours la même réaction si le marché anticipe déjà une Fed restrictive ou si le dollar est en correction depuis plusieurs séances.",
        seo_calendrier_or_faq1_question: "Quels événements économiques influencent le plus l'or ?",
        seo_calendrier_or_faq1_answer: "Les publications américaines comme CPI, PCE, NFP, chômage, PMI, ventes au détail, décisions FOMC et discours de la Fed sont souvent centrales car elles influencent le dollar et les taux.",
        seo_calendrier_or_faq2_question: 'Faut-il trader pendant les annonces ?',
        seo_calendrier_or_faq2_answer: "Pas nécessairement. Beaucoup de traders préfèrent attendre que la volatilité initiale se calme. Le calendrier sert d'abord à connaître le risque événementiel avant de prendre une décision.",
        seo_calendrier_or_link1: 'Tester le terminal complet',
        seo_calendrier_or_link2: 'Suivre XAU/USD dans le terminal',
        seo_calendrier_or_link3: "Comprendre les news macro pour l'or",
        seo_news_forex_or_title: "News Forex et or: filtrer les informations utiles pour XAU/USD",
        seo_news_forex_or_description: "Comment filtrer les news forex, dollar, Fed, inflation, géopolitique et taux US pour mieux comprendre les mouvements de l'or et de XAU/USD.",
        seo_news_forex_or_kicker: 'NEWS MACRO',
        seo_news_forex_or_h1: 'News Forex et or: filtrer le bruit pour comprendre XAU/USD',
        seo_news_forex_or_intro: "Les news de marché arrivent vite et dans tous les sens. Pour l'or, l'enjeu n'est pas de tout lire, mais d'identifier ce qui peut réellement changer le dollar, les taux, l'appétit pour le risque ou la demande refuge.",
        seo_news_forex_or_section1_title: 'Les familles de news à prioriser',
        seo_news_forex_or_section1_copy: "Pour XAU/USD, les catégories les plus utiles sont souvent la Fed, l'inflation, l'emploi américain, les rendements obligataires, le dollar, la géopolitique, les banques centrales et les surprises de données macro.",
        seo_news_forex_or_section2_title: 'Pourquoi une news peut être importante sans bouger le marché',
        seo_news_forex_or_section2_copy: 'Une information peut être vraie mais déjà intégrée par les prix. Le terminal aide à distinguer les news récentes, les sujets officiels, les informations répétées par plusieurs sources et les éléments potentiellement market moving.',
        seo_news_forex_or_section3_title: 'Croiser les news avec DXY et US10Y',
        seo_news_forex_or_section3_copy: "Une news hawkish sur la Fed peut soutenir le dollar et les rendements, ce qui met souvent l'or sous pression. Une news dovish ou un stress géopolitique peut produire l'effet inverse. La watchlist permet de vérifier rapidement cette cohérence.",
        seo_news_forex_or_section4_title: 'Créer une routine plus calme',
        seo_news_forex_or_section4_copy: "L'objectif n'est pas de réagir à chaque headline. Une bonne routine consiste à lire les priorités, repérer le thème dominant, vérifier si le prix confirme, puis attendre un setup compatible avec son propre plan.",
        seo_news_forex_or_section5_title: 'Différencier information et décision',
        seo_news_forex_or_section5_copy: "Une headline peut expliquer un mouvement sans offrir une opportunité exploitable. XAUTERMINAL aide à classer l'information, mais la décision doit venir d'un plan cohérent entre contexte, prix, risque et horizon de temps.",
        seo_news_forex_or_section6_title: 'Pourquoi le bruit coûte cher',
        seo_news_forex_or_section6_copy: 'Trop de sources ouvertes en même temps peuvent pousser à surinterpréter chaque variation. Un flux mieux organisé permet de se concentrer sur les thèmes réellement capables de modifier le dollar, les taux ou la demande refuge.',
        seo_news_forex_or_faq1_question: 'Quelles news suivre pour XAU/USD ?',
        seo_news_forex_or_faq1_answer: "Les news liées à la Fed, à l'inflation, à l'emploi américain, au dollar, aux rendements obligataires, à la géopolitique et au sentiment de risque sont souvent les plus utiles.",
        seo_news_forex_or_faq2_question: "Une news importante fait-elle toujours bouger l'or ?",
        seo_news_forex_or_faq2_answer: "Non. Si l'information est déjà intégrée par les prix ou si un autre thème domine le marché, la réaction peut être faible, retardée ou opposée à l'intuition initiale.",
        seo_news_forex_or_link1: 'Essayer XAUTERMINAL',
        seo_news_forex_or_link2: 'Comparer avec le calendrier économique',
        seo_news_forex_or_link3: 'Construire une lecture macro',
        seo_guide_trading_or_macro_title: "Guide macro pour trader l'or: dollar, taux, inflation et Fed",
        seo_guide_trading_or_macro_description: "Guide pédagogique pour comprendre les principaux drivers macro de l'or: DXY, taux US, inflation, Fed, stress de marché et momentum.",
        seo_guide_trading_or_macro_kicker: 'GUIDE MACRO',
        seo_guide_trading_or_macro_h1: "Guide macro pour trader l'or: dollar, taux, inflation et Fed",
        seo_guide_trading_or_macro_intro: "Trader l'or sans contexte macro peut devenir confus: le même mouvement de prix peut venir d'un dollar faible, d'une baisse des rendements, d'une surprise d'inflation ou d'un stress de marché. Ce guide résume les drivers à suivre avant d'utiliser le terminal.",
        seo_guide_trading_or_macro_section1_title: 'Dollar américain et or',
        seo_guide_trading_or_macro_section1_copy: "XAU/USD est coté en dollars. Quand le dollar se renforce fortement, l'or peut devenir plus difficile à acheter pour les autres devises, ce qui pèse souvent sur le prix. Quand le dollar se détend, XAU/USD peut respirer davantage.",
        seo_guide_trading_or_macro_section2_title: 'Taux US et rendement réel',
        seo_guide_trading_or_macro_section2_copy: "L'or ne verse pas de rendement. Quand les taux et les rendements réels montent, les actifs rémunérés deviennent plus attractifs. Quand ils baissent, l'or peut redevenir plus compétitif, surtout si l'inflation ou le risque restent présents.",
        seo_guide_trading_or_macro_section3_title: 'Fed, inflation et emploi',
        seo_guide_trading_or_macro_section3_copy: "La Fed influence les anticipations de taux. Les chiffres d'inflation et d'emploi modifient ces anticipations. C'est pour cela que CPI, PCE, NFP et FOMC sont souvent des moments clés pour XAU/USD.",
        seo_guide_trading_or_macro_section4_title: 'Momentum et confirmation',
        seo_guide_trading_or_macro_section4_copy: 'Le contexte macro donne une direction probable, mais le prix doit confirmer. Le Bias Desk et les drivers du terminal servent à organiser cette lecture: macro, momentum, risque événementiel et watchlist.',
        seo_guide_trading_or_macro_section5_title: "Construire un scénario plutôt qu'une prédiction",
        seo_guide_trading_or_macro_section5_copy: "Une lecture macro utile ne cherche pas à deviner parfaitement le futur. Elle prépare plusieurs scénarios: dollar fort, détente des taux, surprise inflation, stress de marché ou absence de catalyseur clair.",
        seo_guide_trading_or_macro_section6_title: 'Relier macro et exécution',
        seo_guide_trading_or_macro_section6_copy: "Le contexte aide à savoir où concentrer son attention, mais il ne suffit pas pour entrer en position. L'exécution demande un plan, un niveau d'invalidation, une taille adaptée et une acceptation claire du risque.",
        seo_guide_trading_or_macro_faq1_question: "Quels sont les grands drivers macro de l'or ?",
        seo_guide_trading_or_macro_faq1_answer: "Les plus importants sont souvent le dollar américain, les taux US, les rendements réels, l'inflation, la Fed, la géopolitique, le stress de marché et le momentum du prix.",
        seo_guide_trading_or_macro_faq2_question: "La macro suffit-elle pour trader l'or ?",
        seo_guide_trading_or_macro_faq2_answer: 'Non. La macro donne un cadre de lecture, mais le prix, la volatilité, la liquidité, le timing et la gestion du risque restent indispensables.',
        seo_guide_trading_or_macro_link1: 'Tester XAUTERMINAL',
        seo_guide_trading_or_macro_link2: "Voir l'approche XAU/USD",
        seo_guide_trading_or_macro_link3: 'Lire les news macro utiles',
        seo_routine_trading_xauusd_title: 'Routine trading XAU/USD: préparer une session avec méthode',
        seo_routine_trading_xauusd_description: 'Méthode concrète pour préparer une session XAU/USD avec calendrier économique, news macro, DXY, taux US, Bias Desk et niveaux de risque.',
        seo_routine_trading_xauusd_kicker: 'ROUTINE XAU/USD',
        seo_routine_trading_xauusd_h1: 'Routine trading XAU/USD: préparer une session sans se disperser',
        seo_routine_trading_xauusd_intro: "Une routine de marché sert à réduire le bruit avant d'ouvrir un graphique. Sur XAU/USD, l'objectif est de comprendre le thème dominant de la séance: dollar, taux, inflation, Fed, stress de marché ou simple momentum technique.",
        seo_routine_trading_xauusd_section1_title: 'Commencer par le calendrier',
        seo_routine_trading_xauusd_section1_copy: "Avant de regarder le prix, vérifie les annonces à venir: CPI, PCE, NFP, chômage, PMI, ventes au détail, FOMC et discours de la Fed. Une statistique majeure peut rendre un setup propre beaucoup moins lisible quelques minutes plus tard.",
        seo_routine_trading_xauusd_section2_title: 'Identifier le thème macro du jour',
        seo_routine_trading_xauusd_section2_copy: 'Lis les news prioritaires et cherche le fil conducteur: Fed plus restrictive, dollar sous pression, rendements en hausse, stress géopolitique ou absence de catalyseur clair. Une séance sans thème dominant demande souvent plus de patience.',
        seo_routine_trading_xauusd_section3_title: 'Comparer XAU/USD avec DXY et US10Y',
        seo_routine_trading_xauusd_section3_copy: "Si l'or monte pendant que DXY et les taux baissent, le mouvement est plus cohérent. Si les signaux divergent, il vaut mieux éviter de conclure trop vite. Le but est de savoir si le prix est porté ou contrarié par ses drivers principaux.",
        seo_routine_trading_xauusd_section4_title: 'Utiliser le Bias Desk comme synthèse',
        seo_routine_trading_xauusd_section4_copy: "Le Bias Desk n'est pas un signal automatique. Il aide à regrouper momentum, macro, risk tone et risque événementiel. S'il affiche WAIT, cela peut simplement signifier que les conditions ne sont pas assez alignées.",
        seo_routine_trading_xauusd_section5_title: 'Finir par le plan de risque',
        seo_routine_trading_xauusd_section5_copy: "Une fois le contexte compris, le graphique sert à définir le timing, l'invalidation et la taille. La meilleure lecture macro ne protège pas d'une mauvaise exécution ou d'un risque trop grand.",
        seo_routine_trading_xauusd_faq1_question: 'Combien de temps doit durer une routine XAU/USD ?',
        seo_routine_trading_xauusd_faq1_answer: "Une routine utile peut durer quelques minutes si elle est structurée: calendrier, news, DXY, US10Y, Bias Desk puis graphique. L'important est la régularité, pas la durée.",
        seo_routine_trading_xauusd_faq2_question: 'Faut-il suivre toutes les news avant de trader ?',
        seo_routine_trading_xauusd_faq2_answer: 'Non. Il faut surtout repérer les thèmes capables de changer le dollar, les taux, la demande refuge ou la volatilité. Lire trop de sources peut créer plus de confusion que de clarté.',
        seo_routine_trading_xauusd_link1: 'Tester le terminal complet',
        seo_routine_trading_xauusd_link2: 'Lire le calendrier économique',
        seo_routine_trading_xauusd_link3: 'Filtrer les news macro',
        seo_dxy_taux_or_title: 'DXY, taux US et or: comprendre les relations avec XAU/USD',
        seo_dxy_taux_or_description: "Guide XAUTERMINAL pour comprendre comment le dollar, les rendements US, la Fed et le sentiment de risque influencent l'or et XAU/USD.",
        seo_dxy_taux_or_kicker: 'DXY ET TAUX US',
        seo_dxy_taux_or_h1: 'DXY, taux US et or: comprendre les relations avec XAU/USD',
        seo_dxy_taux_or_intro: "L'or ne bouge pas dans le vide. Même quand le graphique semble clair, XAU/USD reste influencé par le dollar américain, les rendements obligataires, les anticipations de taux et le niveau de stress de marché.",
        seo_dxy_taux_or_section1_title: 'Pourquoi le dollar compte autant',
        seo_dxy_taux_or_section1_copy: "XAU/USD est coté en dollars. Un dollar fort peut rendre l'or plus cher pour les acheteurs hors dollar et peser sur le prix. Un dollar plus faible peut au contraire soutenir le métal, surtout si les autres facteurs ne s'y opposent pas.",
        seo_dxy_taux_or_section2_title: 'Le rôle des taux US',
        seo_dxy_taux_or_section2_copy: "L'or ne verse pas de rendement. Quand les rendements US montent, les actifs rémunérés deviennent plus compétitifs. Quand ils baissent, l'or peut retrouver de l'attrait, notamment si le marché anticipe une Fed moins restrictive.",
        seo_dxy_taux_or_section3_title: 'Quand DXY et taux ne racontent pas la même histoire',
        seo_dxy_taux_or_section3_copy: "Il arrive que le dollar monte alors que les taux baissent, ou l'inverse. Dans ce cas, la lecture devient moins directe. Le trader doit chercher quel driver domine réellement le mouvement de XAU/USD.",
        seo_dxy_taux_or_section4_title: 'Ajouter le sentiment de risque',
        seo_dxy_taux_or_section4_copy: "En période de stress, l'or peut être soutenu même si certains drivers semblent défavorables. À l'inverse, une séance très risk-on peut réduire la demande refuge. C'est pour cela qu'une lecture multi-facteurs est nécessaire.",
        seo_dxy_taux_or_section5_title: 'Comment XAUTERMINAL organise cette lecture',
        seo_dxy_taux_or_section5_copy: "Le terminal regroupe DXY, US10Y, news macro, calendrier économique et Bias Desk. L'idée est de vérifier rapidement si les mouvements se confirment ou se contredisent avant de prendre une décision.",
        seo_dxy_taux_or_faq1_question: 'XAU/USD baisse-t-il toujours quand DXY monte ?',
        seo_dxy_taux_or_faq1_answer: "Non. C'est une relation fréquente mais pas mécanique. Les taux, la Fed, le risque géopolitique et le momentum peuvent modifier ou retarder la réaction.",
        seo_dxy_taux_or_faq2_question: 'Les taux US sont-ils plus importants que le dollar ?',
        seo_dxy_taux_or_faq2_answer: "Cela dépend du contexte. Certaines séances sont dominées par le dollar, d'autres par les rendements, la Fed ou le sentiment de risque. L'intérêt est de comparer ces forces ensemble.",
        seo_dxy_taux_or_link1: "Voir l'approche XAU/USD",
        seo_dxy_taux_or_link2: 'Lire le guide macro',
        seo_dxy_taux_or_link3: 'Essayer XAUTERMINAL',
        seo_bias_desk_title: 'Bias Desk trading: lire les drivers sans confondre outil et signal',
        seo_bias_desk_description: 'Comprendre comment utiliser un Bias Desk pour organiser les drivers de marché sans transformer une synthèse macro en signal de trading automatique.',
        seo_bias_desk_kicker: 'BIAS DESK',
        seo_bias_desk_h1: 'Bias Desk trading: lire les drivers sans confondre outil et signal',
        seo_bias_desk_intro: "Un Bias Desk sert à résumer une lecture de marché: momentum, macro, risque événementiel, sentiment et drivers principaux. Il ne remplace pas une stratégie, mais il peut aider à éviter les décisions prises sur une seule information.",
        seo_bias_desk_section1_title: "Ce qu'un bias veut dire",
        seo_bias_desk_section1_copy: "Un bias est une orientation de contexte, pas une certitude. Bullish signifie que plusieurs éléments soutiennent plutôt la hausse. Bearish signifie que les pressions baissières dominent. Neutral ou WAIT indique souvent un manque d'alignement.",
        seo_bias_desk_section2_title: 'Pourquoi les drivers sont plus utiles que le score seul',
        seo_bias_desk_section2_copy: "Le score donne une synthèse rapide, mais les raisons sont plus importantes. Un trader doit savoir si le bias vient du dollar, des taux, du momentum, d'une news ou d'un risque événementiel.",
        seo_bias_desk_section3_title: 'Lire le risque événementiel',
        seo_bias_desk_section3_copy: "Un contexte favorable peut devenir dangereux juste avant une annonce majeure. Si le calendrier indique un risque élevé, la bonne décision peut être d'attendre, même si le reste du marché semble aligné.",
        seo_bias_desk_section4_title: 'Utiliser le bias avec le graphique',
        seo_bias_desk_section4_copy: "Le graphique reste indispensable pour le timing. Le bias aide à préparer le scénario; le prix aide à décider si ce scénario mérite d'être exécuté, invalidé ou simplement observé.",
        seo_bias_desk_section5_title: "Les limites d'une synthèse automatique",
        seo_bias_desk_section5_copy: "Aucun outil ne peut comprendre parfaitement chaque nuance de marché. Le Bias Desk doit être traité comme une aide à la lecture, avec une vérification humaine et une gestion du risque indépendante.",
        seo_bias_desk_faq1_question: "Le Bias Desk donne-t-il des signaux d'achat ou de vente ?",
        seo_bias_desk_faq1_answer: "Non. Il organise les drivers de marché. La décision d'entrer, sortir ou rester à l'écart doit venir de ta stratégie, de ton timing et de ta gestion du risque.",
        seo_bias_desk_faq2_question: 'Pourquoi le Bias Desk affiche parfois WAIT ?',
        seo_bias_desk_faq2_answer: 'WAIT apparaît quand les drivers sont mixtes, quand la confiance est insuffisante ou quand un risque événementiel rend la lecture trop instable.',
        seo_bias_desk_link1: 'Voir le terminal XAU/USD',
        seo_bias_desk_link2: 'Construire une routine',
        seo_bias_desk_link3: 'Lire le disclaimer trading',
    },
    en: {
        proof_news: 'Multi-source news',
        proof_calendar: 'Macro calendar',
        proof_profiles: 'XAU, Forex, Indices, Crypto profiles',
        feature_bias_title: 'Bias desk and drivers',
        resources_kicker: 'RESOURCES',
        resources_title: 'Understand the context before opening the terminal.',
        resources_intro: 'Quickly access guides, XAU/USD pages and macro explanations to better understand what the terminal brings together.',
        resources_cta: 'View all resources',
        guides_cta: 'View trading guides',
        nav_pulse: 'Market Pulse',
        pulse_kicker: 'MARKET PULSE',
        pulse_title: 'A fast read of what matters today.',
        pulse_intro: 'Market Pulse turns news, calendar events, macro drivers and watched assets into a readable briefing before opening the terminal.',
        pulse_cta: 'View Market Pulse',
        pulse_trial: 'Try the terminal',
        pulse_context_label: 'Macro context',
        pulse_context_value: 'Elevated risk before US data',
        pulse_context_copy: 'The terminal highlights sessions where the calendar, dollar, yields or news can change the market read.',
        pulse_xau_copy: 'Gold sensitive to DXY, US10Y and inflation.',
        pulse_dxy_value: 'Watch',
        pulse_dxy_copy: 'Dollar pressure and US yields.',
        pulse_calendar_label: 'Calendar',
        pulse_calendar_copy: 'High-impact release before the US session.',
        pulse_page_title: 'Market Pulse - Daily market analysis',
        pulse_page_description: 'XAUTERMINAL Market Pulse summarizes macro context, assets to watch, important news and the economic calendar before a trading session.',
        pulse_page_kicker: 'MARKET PULSE',
        pulse_page_h1: 'The market briefing before opening the terminal',
        pulse_page_intro: 'Market Pulse gathers the essential macro read: today’s calendar, news that matter, assets to watch, risk level and context bias. The goal is simple: know where to look before making a decision.',
        pulse_page_trial: 'Try XAUTERMINAL',
        pulse_board_today: 'TODAY',
        pulse_board_risk: 'Elevated risk',
        pulse_board_score: 'Active context before US data',
        pulse_board_dxy: 'Strong',
        pulse_board_yields: 'Pressure',
        pulse_board_news_label: 'News',
        pulse_live_updated: 'Updated',
        pulse_live_news_kicker: 'LIVE NEWS',
        pulse_live_news_title: 'Recent important headlines',
        pulse_live_calendar_kicker: 'CALENDAR',
        pulse_live_calendar_title: 'Upcoming events',
        pulse_drivers_kicker: 'PUBLIC DRIVERS',
        pulse_drivers_title: 'What influences the context',
        pulse_page_card_calendar_title: 'Risk calendar',
        pulse_page_card_calendar_copy: 'Spot releases that can change volatility: CPI, PCE, NFP, FOMC, PMI or central bank speeches.',
        pulse_page_card_news_title: 'News that matter',
        pulse_page_card_news_copy: 'Filter headlines that truly influence the dollar, yields, risk sentiment or the assets in your watchlist.',
        pulse_page_card_drivers_title: 'Macro drivers',
        pulse_page_card_drivers_copy: 'Compare DXY, US10Y, inflation, the Fed, geopolitical stress and momentum to understand what dominates the session.',
        pulse_page_card_watchlist_title: 'Asset radar',
        pulse_page_card_watchlist_copy: 'Prepare markets to watch before moving to the chart: XAU/USD, Forex, indices, DXY, yields and crypto.',
        pulse_workflow_kicker: 'ROUTINE',
        pulse_workflow_title: 'A four-step market routine',
        pulse_workflow_copy: 'The best terminals do not only display data: they help decide which data deserves your attention. Market Pulse is the first layer before charting.',
        pulse_step1_title: 'Calendar',
        pulse_step1_copy: 'Identify risky times and releases able to move the dollar, yields or indices.',
        pulse_step2_title: 'News',
        pulse_step2_copy: 'Filter headlines directly tied to the dominant session theme.',
        pulse_step3_title: 'Drivers',
        pulse_step3_copy: 'Compare the dollar, yields, risk sentiment and price momentum.',
        pulse_step4_title: 'Plan',
        pulse_step4_copy: 'Open the terminal with a clear watchlist, not ten random tabs.',
        pulse_assets_kicker: 'MARKET RADAR',
        pulse_assets_title: 'Markets that deserve a dedicated read',
        pulse_asset_gold: 'Gold and US macro',
        pulse_asset_eurusd: 'Dollar and ECB',
        pulse_asset_gbpjpy: 'FX volatility',
        pulse_asset_nasdaq: 'Yields and risk-on',
        pulse_asset_dxy: 'Dollar strength',
        pulse_asset_us10y: 'US yields',
        pulse_final_title: 'Why add Market Pulse to XAUTERMINAL?',
        pulse_final_copy: 'Because the real problem for a trader is not only finding data, but ranking it. Market Pulse gives a clear entry point before the full terminal, charts and Bias Desk.',
        resources_deep_kicker: 'USEFUL READING',
        resources_deep_title: 'Explore the pages connected to the terminal.',
        learning_guides_kicker: 'GUIDES',
        learning_guides_title: 'XAU/USD, macro and Bias Desk trading guides',
        learning_guides_copy: 'Build a clear market routine around the dollar, US yields, news and the Bias Desk.',
        learning_open_guides: 'Open guides',
        learning_xau_kicker: 'XAU/USD',
        learning_macro_kicker: 'MACRO',
        learning_read_page: 'Read page',
        nav_resources: 'Resources',
        nav_guides: 'Guides',
        resource_terminal_title: 'XAU/USD terminal',
        resource_terminal_copy: 'Why gold requires a combined reading of the dollar, US yields, the Fed, inflation and momentum.',
        resource_calendar_title: 'Economic calendar for gold',
        resource_calendar_copy: 'The releases to watch on XAU/USD: CPI, PCE, NFP, FOMC, Fed speeches and US data.',
        resource_news_title: 'Forex and gold news',
        resource_news_copy: 'How to filter useful headlines to understand moves in the dollar, yields and gold.',
        resource_guide_title: 'Macro guide for trading gold',
        resource_guide_copy: 'An educational read of the main macro drivers: DXY, US10Y, inflation, Fed and market stress.',
        trust_kicker: 'TRUST',
        trust_title: 'An analysis terminal, not a magic promise.',
        trust_copy: 'XAUTERMINAL is designed to organize your market read before a decision. The service stays transparent about its limits, payment and risk management.',
        trust_is_title: 'What it is',
        trust_is_copy: 'A workspace to centralize news, calendar, charts, watchlist, macro drivers and Bias Desk in one routine.',
        trust_not_title: 'What it is not',
        trust_not_copy: 'Not a trading robot, not a guaranteed signal seller, not personalized financial advice.',
        trust_payment_title: 'Clear payment',
        trust_payment_copy: 'Stripe handles trials, payments, invoices and subscriptions. XAUTERMINAL does not store card numbers.',
        trust_control_title: 'User control',
        trust_control_copy: 'From My account, you can track access, manage your profile, subscription and contact support if needed.',
        resource_terminal_short: 'XAU/USD',
        resource_calendar_short: 'Gold calendar',
        resource_news_short: 'Forex news',
        resource_guide_short: 'Macro guide',
        pricing_point_trial: '7-day free trial',
        pricing_point_monthly: 'Monthly renewal',
        pricing_point_cancel: 'Cancel at period end through Stripe',
        pricing_point_yearly_saving: 'About 2 months included',
        pricing_point_full_access: 'Full terminal access',
        pricing_point_one_time: 'One-time payment',
        pricing_point_lifetime: 'Lifetime terminal access',
        pricing_point_founder: 'Limited founder offer',
        pricing_note_title: 'Secure trial and payment',
        pricing_note_copy: 'For monthly and yearly subscriptions, Stripe may ask for a card to activate the 7-day free trial and prepare renewal. No subscription charge is expected before the trial ends. After billing, the started monthly or yearly period is due and non-refundable unless legally required otherwise. Cancellation stops the next renewal.',
        faq_trial_title: 'What happens after 7 days?',
        faq_trial_copy: 'The selected subscription starts automatically if payment is validated by Stripe. You can cancel during the trial through Stripe before the first charge. After billing, the current period remains due.',
        legal_confirm_subscription: 'By continuing to Stripe, you accept the Terms, Privacy Policy and subscription conditions. You request immediate access to the XAUTERMINAL digital service from the Stripe subscription, including during the 7-day free trial, and acknowledge that this immediate performance may result in loss of the withdrawal right where legal conditions are met. The subscription renews automatically after the trial unless canceled before renewal. Continue?',
        legal_confirm_lifetime: 'By continuing to Stripe, you accept the Terms, Privacy Policy and lifetime offer conditions. You request immediate access to the XAUTERMINAL digital service from payment and acknowledge that this immediate performance may result in loss of the withdrawal right where legal conditions are met. The lifetime offer is a one-time payment, non-refundable unless legally required otherwise. Continue?',
        faq_signals_title: 'Does the terminal provide signals?',
        faq_signals_copy: 'No. XAUTERMINAL is a decision-support tool: news, calendar, drivers, bias and charting. It does not replace your strategy or risk management.',
        faq_markets_title: 'Can I switch markets?',
        faq_markets_copy: 'Yes. XAU/USD, Forex, indices and crypto profiles adapt the calendar, news feed, Bias Desk and watchlist.',
        faq_payments_title: 'Are my payments secure?',
        faq_payments_copy: 'Payments and subscriptions are processed by Stripe. XAUTERMINAL does not store card numbers.',
        footer_tagline: 'Professional macro and trading terminal. Information tool, not financial advice.',
        footer_trial: 'Start trial',
        footer_product: 'Product',
        footer_learn: 'Learn',
        footer_markets: 'Markets and data',
        footer_account: 'Account',
        footer_legal: 'Legal',
        footer_dxy_rates: 'DXY and US yields',
        footer_bias_desk: 'Bias Desk',
        footer_subscriptions: 'Subscriptions',
        footer_contact: 'Contact',
        footer_risk: 'Trading involves risk of loss. XAUTERMINAL provides market information and organization tools, without personalized financial advice.',
        risk_footer_link: 'Trading disclaimer',
        resources_page_title: 'Macro trading, XAU/USD and economic calendar resources',
        resources_page_description: 'XAUTERMINAL guides to understand XAU/USD, the gold economic calendar, Forex news and the main macro drivers.',
        resources_page_h1: 'Macro trading, XAU/USD and economic calendar resources',
        resources_page_intro: 'These pages explain concepts directly connected to XAUTERMINAL: gold macro reading, economic events, Forex news and market routine organization. They help you understand the product before using it in the terminal.',
        resources_page_read: 'Read',
        guides_page_title: 'XAU/USD, macro and Bias Desk trading guides',
        guides_page_description: 'XAUTERMINAL guides to prepare an XAU/USD session, understand DXY, US yields, macro news and how to use a Bias Desk.',
        guides_page_kicker: 'TRADING GUIDES',
        guides_page_h1: 'XAU/USD, macro and Bias Desk trading guides',
        guides_page_intro: 'These guides help build a clear routine around the terminal: prepare a session, read DXY and US yields, filter news and use the Bias Desk without mistaking it for an automatic signal.',
        guides_page_next_title: 'Use the guides with the terminal',
        guides_page_next_copy: 'Start by understanding the routine, then open the terminal to check the calendar, news, chart and drivers in real conditions.',
        guides_page_trial: 'Try XAUTERMINAL',
        guides_page_resources: 'View all resources',
        resources_panel_kicker: 'PUBLIC HUB',
        resources_panel_title: 'Understand before acting',
        resources_panel_copy: 'Each page connects a market concept to practical terminal usage: news, calendar, drivers and chart.',
        guides_panel_kicker: 'ROUTINE',
        guides_panel_title: 'Turn noise into a plan',
        guides_panel_copy: 'The guides are quick entry points before opening the terminal and observing the real drivers.',
        article_panel_kicker: 'READ WITH',
        article_panel_copy: 'Use this resource with the calendar, news, charts and Bias Desk to keep a structured market read.',
        article_summary: 'Summary',
        article_related: 'Useful links',
        seo_continue_title: 'Continue with XAUTERMINAL',
        seo_continue_copy: 'These resources are designed to work together: macro context, economic calendar, filtered news and charting. To test the complete workspace, return to the landing page and start the trial through the official flow.',
        seo_faq_kicker: 'FAQ',
        seo_faq_title: 'Frequently asked questions',
        support_title: 'XAUTERMINAL Support',
        support_description: 'XAUTERMINAL help for accounts, email codes, Stripe payments, subscriptions, terminal access and account security.',
        support_kicker: 'SUPPORT',
        support_h1: 'XAUTERMINAL help and support',
        support_intro: 'Find answers to the most common situations: email validation, terminal access, Stripe payment, subscription, password and account security.',
        support_action_account: 'Open my account',
        support_action_plans: 'View plans',
        support_action_password: 'Reset my password',
        support_card_code_title: 'I did not receive my code',
        support_card_code_copy: 'Check spam, promotions and the spelling of your email. You can log in again with the same email: XAUTERMINAL will send a new code if the account is not confirmed yet.',
        support_card_paid_title: 'I paid but cannot access',
        support_card_paid_copy: 'Log in again and open My account. If the Stripe return was interrupted, the site tries to resync access. If it remains blocked, contact support with your account email.',
        support_card_password_title: 'Forgot password',
        support_card_password_copy: 'Use the reset page to receive a secure link. The link expires automatically and should never be shared.',
        support_card_subscription_title: 'Manage my subscription',
        support_card_subscription_copy: 'From My account, use the Stripe button to manage your payment method, subscription or invoices. XAUTERMINAL does not store card numbers.',
        support_card_terminal_title: 'Terminal access',
        support_card_terminal_copy: 'The full terminal is reserved for confirmed accounts with an active trial or subscription. If your account is confirmed but has no Stripe plan, choose a plan from the landing page or My account.',
        support_card_security_title: 'Account security',
        support_card_security_copy: 'Use a unique password, keep access to your email and avoid sharing your account. If in doubt, change your password from the account area.',
        support_process_title: 'Before contacting support',
        support_process_1: 'Check that your email is confirmed with the latest code received.',
        support_process_2: 'If you paid, log in again and open My account to trigger automatic synchronization.',
        support_process_3: 'If access remains blocked, contact support with your account email and, if possible, the Stripe payment time.',
        support_contact_title: 'Contact XAUTERMINAL',
        support_contact_copy: 'For account, payment or terminal access requests, write to us at',
        seo_terminal_xauusd_title: 'XAU/USD terminal for tracking gold, the dollar and yields',
        seo_terminal_xauusd_description: 'Understand how XAUTERMINAL helps track XAU/USD with charting, macro news, economic calendar, DXY, US yields and market drivers.',
        seo_terminal_xauusd_kicker: 'XAU/USD',
        seo_terminal_xauusd_h1: 'XAU/USD terminal: track gold with a clear macro read',
        seo_terminal_xauusd_intro: 'XAU/USD often reacts to several forces at once: the US dollar, US yields, inflation, Fed communication, geopolitical stress and short-term momentum. XAUTERMINAL brings these inputs together in an interface built to prepare a decision, not replace a strategy.',
        seo_terminal_xauusd_section1_title: 'Why XAU/USD needs a multi-factor read',
        seo_terminal_xauusd_section1_copy: 'Gold can rise because the dollar is falling, because real yields are easing, because geopolitical risk supports safe-haven demand or simply because technical momentum dominates the session. Looking only at the chart can leave out an important part of the context.',
        seo_terminal_xauusd_section2_title: 'What the terminal centralizes for gold',
        seo_terminal_xauusd_section2_copy: 'The XAU/USD profile brings together TradingView charting, news linked to the Fed, the dollar, yields, inflation and geopolitics, the US economic calendar, a gold-focused watchlist and a Bias Desk that summarizes the main drivers.',
        seo_terminal_xauusd_section3_title: 'How to use this page in a routine',
        seo_terminal_xauusd_section3_copy: 'Before a session, check upcoming US events, read priority news, watch DXY and US10Y, then compare that context with the XAU/USD move. The goal is to avoid entering without knowing which factor is dominating the market.',
        seo_terminal_xauusd_section4_title: 'Important limitation',
        seo_terminal_xauusd_section4_copy: 'The terminal does not provide financial advice or guaranteed signals. It helps structure information and save time in analysis. The decision, risk and position management remain your responsibility.',
        seo_terminal_xauusd_section5_title: 'A simple routine before an XAU/USD session',
        seo_terminal_xauusd_section5_copy: 'An effective routine starts with the macro events of the day, then the dominant themes: inflation, Fed, dollar, yields, geopolitical risk and global sentiment. Only then does the chart help check whether price confirms or contradicts that context.',
        seo_terminal_xauusd_section6_title: 'Why XAUTERMINAL exists',
        seo_terminal_xauusd_section6_copy: 'The goal is not to add another screen, but to reduce switching between calendar, news, watchlist, chart and context notes. A more organized read helps avoid decisions made under pressure or from one isolated input.',
        seo_terminal_xauusd_faq1_question: 'Is XAUTERMINAL only built for XAU/USD?',
        seo_terminal_xauusd_faq1_answer: 'No. XAU/USD is the central market of the project, but the terminal also offers Forex, indices and crypto profiles to adapt news, watchlists and context.',
        seo_terminal_xauusd_faq2_question: 'Does the terminal replace a trading strategy?',
        seo_terminal_xauusd_faq2_answer: 'No. It helps organize information and prepare a decision. Strategy, timing, risk and execution remain the responsibility of the user.',
        seo_terminal_xauusd_link1: 'Start the XAUTERMINAL trial',
        seo_terminal_xauusd_link2: 'Read the economic calendar for gold',
        seo_terminal_xauusd_link3: 'Understand the macro read for gold',
        seo_calendrier_or_title: 'Economic calendar for trading gold: CPI, NFP, Fed and US yields',
        seo_calendrier_or_description: 'Practical guide to reading the economic calendar when following gold and XAU/USD: inflation, NFP, Fed, US yields, dollar and volatility.',
        seo_calendrier_or_kicker: 'ECONOMIC CALENDAR',
        seo_calendrier_or_h1: 'Economic calendar for gold: events to watch on XAU/USD',
        seo_calendrier_or_intro: 'On XAU/USD, some data releases can sharply change the market read. Inflation, US employment, Fed decisions and growth-related releases influence the dollar, yields and therefore gold.',
        seo_calendrier_or_section1_title: 'The releases that matter most',
        seo_calendrier_or_section1_copy: 'Gold traders often watch CPI, PCE, NFP, unemployment, retail sales, PMI, FOMC decisions and Fed member speeches. These events can shift rate expectations and trigger strong volatility.',
        seo_calendrier_or_section2_title: 'Actual, forecast, previous: what should you compare?',
        seo_calendrier_or_section2_copy: 'A release is rarely read in isolation. You need to compare the published number with consensus and the previous number. A stronger-than-expected result can support the dollar or yields depending on context, which can weigh on gold. The opposite can support XAU/USD.',
        seo_calendrier_or_section3_title: 'Why timing matters',
        seo_calendrier_or_section3_copy: 'The minutes before and after an important release are often unstable. The terminal highlights high-impact events and release blocks so you do not discover too late that a major statistic is coming.',
        seo_calendrier_or_section4_title: 'Use the calendar with the broader context',
        seo_calendrier_or_section4_copy: 'A calendar alone is not enough. It must be crossed with news, DXY, US10Y, volatility and price behavior. This combination is what XAUTERMINAL tries to make easier to read.',
        seo_calendrier_or_section5_title: 'Prepare for releases instead of suffering them',
        seo_calendrier_or_section5_copy: 'The value of a calendar is not only knowing the time of a release. It helps decide in advance whether to avoid a volatility window, wait for the market reaction or adapt the risk plan.',
        seo_calendrier_or_section6_title: 'Releases are not all read the same way',
        seo_calendrier_or_section6_copy: 'The same surprise can have a different effect depending on context. A stronger-than-expected CPI does not always produce the same reaction if markets already expect a restrictive Fed or if the dollar has been correcting for several sessions.',
        seo_calendrier_or_faq1_question: 'Which economic events influence gold the most?',
        seo_calendrier_or_faq1_answer: 'US releases such as CPI, PCE, NFP, unemployment, PMI, retail sales, FOMC decisions and Fed speeches are often central because they influence the dollar and yields.',
        seo_calendrier_or_faq2_question: 'Should you trade during releases?',
        seo_calendrier_or_faq2_answer: 'Not necessarily. Many traders prefer to wait until the initial volatility calms down. The calendar is first used to understand event risk before making a decision.',
        seo_calendrier_or_link1: 'Try the full terminal',
        seo_calendrier_or_link2: 'Follow XAU/USD in the terminal',
        seo_calendrier_or_link3: 'Understand macro news for gold',
        seo_news_forex_or_title: 'Forex and gold news: filter useful information for XAU/USD',
        seo_news_forex_or_description: 'How to filter Forex, dollar, Fed, inflation, geopolitics and US yield news to better understand gold and XAU/USD moves.',
        seo_news_forex_or_kicker: 'MACRO NEWS',
        seo_news_forex_or_h1: 'Forex and gold news: filter the noise to understand XAU/USD',
        seo_news_forex_or_intro: 'Market news arrives fast and from every direction. For gold, the point is not to read everything, but to identify what can truly change the dollar, yields, risk appetite or safe-haven demand.',
        seo_news_forex_or_section1_title: 'News categories to prioritize',
        seo_news_forex_or_section1_copy: 'For XAU/USD, the most useful categories are often the Fed, inflation, US employment, bond yields, the dollar, geopolitics, central banks and macro data surprises.',
        seo_news_forex_or_section2_title: 'Why news can matter without moving the market',
        seo_news_forex_or_section2_copy: 'Information can be true but already priced in. The terminal helps distinguish recent news, official topics, information repeated by several sources and items that may be market moving.',
        seo_news_forex_or_section3_title: 'Cross-check news with DXY and US10Y',
        seo_news_forex_or_section3_copy: 'A hawkish Fed headline can support the dollar and yields, often pressuring gold. A dovish headline or geopolitical stress can do the opposite. The watchlist helps check this consistency quickly.',
        seo_news_forex_or_section4_title: 'Build a calmer routine',
        seo_news_forex_or_section4_copy: 'The goal is not to react to every headline. A good routine is to read priorities, identify the dominant theme, check whether price confirms it, then wait for a setup that fits your own plan.',
        seo_news_forex_or_section5_title: 'Separate information from decision',
        seo_news_forex_or_section5_copy: 'A headline can explain a move without offering a usable opportunity. XAUTERMINAL helps classify information, but the decision must come from a coherent plan combining context, price, risk and time horizon.',
        seo_news_forex_or_section6_title: 'Why noise is expensive',
        seo_news_forex_or_section6_copy: 'Too many open sources can lead to overinterpreting each variation. A better organized feed helps focus on themes truly capable of changing the dollar, yields or safe-haven demand.',
        seo_news_forex_or_faq1_question: 'Which news should you follow for XAU/USD?',
        seo_news_forex_or_faq1_answer: 'News linked to the Fed, inflation, US employment, the dollar, bond yields, geopolitics and risk sentiment is often the most useful.',
        seo_news_forex_or_faq2_question: 'Does important news always move gold?',
        seo_news_forex_or_faq2_answer: 'No. If the information is already priced in or if another theme dominates the market, the reaction can be weak, delayed or opposite to the initial intuition.',
        seo_news_forex_or_link1: 'Try XAUTERMINAL',
        seo_news_forex_or_link2: 'Compare with the economic calendar',
        seo_news_forex_or_link3: 'Build a macro read',
        seo_guide_trading_or_macro_title: 'Macro guide for trading gold: dollar, yields, inflation and Fed',
        seo_guide_trading_or_macro_description: 'Educational guide to understand the main macro drivers of gold: DXY, US yields, inflation, Fed, market stress and momentum.',
        seo_guide_trading_or_macro_kicker: 'MACRO GUIDE',
        seo_guide_trading_or_macro_h1: 'Macro guide for trading gold: dollar, yields, inflation and Fed',
        seo_guide_trading_or_macro_intro: 'Trading gold without macro context can become confusing: the same price move can come from a weaker dollar, lower yields, an inflation surprise or market stress. This guide summarizes the drivers to watch before using the terminal.',
        seo_guide_trading_or_macro_section1_title: 'US dollar and gold',
        seo_guide_trading_or_macro_section1_copy: 'XAU/USD is quoted in dollars. When the dollar strengthens sharply, gold can become harder to buy for other currencies, which often weighs on price. When the dollar eases, XAU/USD can breathe more easily.',
        seo_guide_trading_or_macro_section2_title: 'US yields and real yield',
        seo_guide_trading_or_macro_section2_copy: 'Gold does not pay yield. When rates and real yields rise, yield-bearing assets become more attractive. When they fall, gold can become more competitive, especially if inflation or risk remain present.',
        seo_guide_trading_or_macro_section3_title: 'Fed, inflation and employment',
        seo_guide_trading_or_macro_section3_copy: 'The Fed influences rate expectations. Inflation and employment figures shift those expectations. That is why CPI, PCE, NFP and FOMC are often key moments for XAU/USD.',
        seo_guide_trading_or_macro_section4_title: 'Momentum and confirmation',
        seo_guide_trading_or_macro_section4_copy: 'Macro context gives a likely direction, but price must confirm. The terminal Bias Desk and drivers help organize this read: macro, momentum, event risk and watchlist.',
        seo_guide_trading_or_macro_section5_title: 'Build a scenario rather than a prediction',
        seo_guide_trading_or_macro_section5_copy: 'A useful macro read does not try to perfectly guess the future. It prepares several scenarios: strong dollar, easing yields, inflation surprise, market stress or no clear catalyst.',
        seo_guide_trading_or_macro_section6_title: 'Connect macro and execution',
        seo_guide_trading_or_macro_section6_copy: 'Context helps decide where to focus attention, but it is not enough to enter a position. Execution requires a plan, an invalidation level, appropriate sizing and clear acceptance of risk.',
        seo_guide_trading_or_macro_faq1_question: 'What are the main macro drivers of gold?',
        seo_guide_trading_or_macro_faq1_answer: 'The most important are often the US dollar, US yields, real yields, inflation, the Fed, geopolitics, market stress and price momentum.',
        seo_guide_trading_or_macro_faq2_question: 'Is macro enough to trade gold?',
        seo_guide_trading_or_macro_faq2_answer: 'No. Macro gives a reading framework, but price, volatility, liquidity, timing and risk management remain essential.',
        seo_guide_trading_or_macro_link1: 'Try XAUTERMINAL',
        seo_guide_trading_or_macro_link2: 'View the XAU/USD approach',
        seo_guide_trading_or_macro_link3: 'Read useful macro news',
        seo_routine_trading_xauusd_title: 'XAU/USD trading routine: prepare a session methodically',
        seo_routine_trading_xauusd_description: 'A concrete method to prepare an XAU/USD session with economic calendar, macro news, DXY, US yields, Bias Desk and risk levels.',
        seo_routine_trading_xauusd_kicker: 'XAU/USD ROUTINE',
        seo_routine_trading_xauusd_h1: 'XAU/USD trading routine: prepare a session without scattering attention',
        seo_routine_trading_xauusd_intro: 'A market routine helps reduce noise before opening a chart. On XAU/USD, the goal is to understand the dominant theme of the session: dollar, yields, inflation, Fed, market stress or simple technical momentum.',
        seo_routine_trading_xauusd_section1_title: 'Start with the calendar',
        seo_routine_trading_xauusd_section1_copy: 'Before looking at price, check upcoming releases: CPI, PCE, NFP, unemployment, PMI, retail sales, FOMC and Fed speeches. A major statistic can make a clean setup much harder to read minutes later.',
        seo_routine_trading_xauusd_section2_title: 'Identify the macro theme of the day',
        seo_routine_trading_xauusd_section2_copy: 'Read priority news and look for the thread: restrictive Fed, dollar pressure, rising yields, geopolitical stress or no clear catalyst. A session without a dominant theme often requires more patience.',
        seo_routine_trading_xauusd_section3_title: 'Compare XAU/USD with DXY and US10Y',
        seo_routine_trading_xauusd_section3_copy: 'If gold rises while DXY and yields fall, the move is more coherent. If signals diverge, avoid concluding too fast. The goal is to know whether price is supported or challenged by its main drivers.',
        seo_routine_trading_xauusd_section4_title: 'Use the Bias Desk as a synthesis',
        seo_routine_trading_xauusd_section4_copy: 'The Bias Desk is not an automatic signal. It groups momentum, macro, risk tone and event risk. If it displays WAIT, it may simply mean conditions are not aligned enough.',
        seo_routine_trading_xauusd_section5_title: 'Finish with the risk plan',
        seo_routine_trading_xauusd_section5_copy: 'Once the context is clear, the chart helps define timing, invalidation and size. The best macro read does not protect against poor execution or excessive risk.',
        seo_routine_trading_xauusd_faq1_question: 'How long should an XAU/USD routine take?',
        seo_routine_trading_xauusd_faq1_answer: 'A useful routine can take only a few minutes if structured: calendar, news, DXY, US10Y, Bias Desk, then chart. Consistency matters more than duration.',
        seo_routine_trading_xauusd_faq2_question: 'Should you follow every news item before trading?',
        seo_routine_trading_xauusd_faq2_answer: 'No. You mainly need to identify themes that can change the dollar, yields, safe-haven demand or volatility. Reading too many sources can create more confusion than clarity.',
        seo_routine_trading_xauusd_link1: 'Try the full terminal',
        seo_routine_trading_xauusd_link2: 'Read the economic calendar',
        seo_routine_trading_xauusd_link3: 'Filter macro news',
        seo_dxy_taux_or_title: 'DXY, US yields and gold: understand the relationship with XAU/USD',
        seo_dxy_taux_or_description: 'XAUTERMINAL guide to understand how the dollar, US yields, the Fed and risk sentiment influence gold and XAU/USD.',
        seo_dxy_taux_or_kicker: 'DXY AND US YIELDS',
        seo_dxy_taux_or_h1: 'DXY, US yields and gold: understand the relationship with XAU/USD',
        seo_dxy_taux_or_intro: 'Gold does not move in isolation. Even when the chart looks clear, XAU/USD remains influenced by the US dollar, bond yields, rate expectations and the level of market stress.',
        seo_dxy_taux_or_section1_title: 'Why the dollar matters so much',
        seo_dxy_taux_or_section1_copy: 'XAU/USD is quoted in dollars. A strong dollar can make gold more expensive for non-dollar buyers and weigh on price. A weaker dollar can support the metal, especially if other factors do not oppose it.',
        seo_dxy_taux_or_section2_title: 'The role of US yields',
        seo_dxy_taux_or_section2_copy: 'Gold does not pay yield. When US yields rise, yield-bearing assets become more competitive. When they fall, gold can regain appeal, especially if the market expects a less restrictive Fed.',
        seo_dxy_taux_or_section3_title: 'When DXY and yields tell different stories',
        seo_dxy_taux_or_section3_copy: 'Sometimes the dollar rises while yields fall, or the opposite. The read becomes less direct. The trader must identify which driver is truly dominating the XAU/USD move.',
        seo_dxy_taux_or_section4_title: 'Add risk sentiment',
        seo_dxy_taux_or_section4_copy: 'During stress, gold can be supported even if some drivers seem unfavorable. Conversely, a strong risk-on session can reduce safe-haven demand. This is why a multi-factor read is needed.',
        seo_dxy_taux_or_section5_title: 'How XAUTERMINAL organizes this read',
        seo_dxy_taux_or_section5_copy: 'The terminal brings together DXY, US10Y, macro news, economic calendar and Bias Desk. The idea is to quickly check whether moves confirm or contradict each other before making a decision.',
        seo_dxy_taux_or_faq1_question: 'Does XAU/USD always fall when DXY rises?',
        seo_dxy_taux_or_faq1_answer: 'No. It is a frequent relationship but not a mechanical one. Yields, the Fed, geopolitical risk and momentum can change or delay the reaction.',
        seo_dxy_taux_or_faq2_question: 'Are US yields more important than the dollar?',
        seo_dxy_taux_or_faq2_answer: 'It depends on the context. Some sessions are dominated by the dollar, others by yields, the Fed or risk sentiment. The point is to compare these forces together.',
        seo_dxy_taux_or_link1: 'View the XAU/USD approach',
        seo_dxy_taux_or_link2: 'Read the macro guide',
        seo_dxy_taux_or_link3: 'Try XAUTERMINAL',
        seo_bias_desk_title: 'Trading Bias Desk: read drivers without confusing tool and signal',
        seo_bias_desk_description: 'Understand how to use a Bias Desk to organize market drivers without turning a macro synthesis into an automatic trading signal.',
        seo_bias_desk_kicker: 'BIAS DESK',
        seo_bias_desk_h1: 'Trading Bias Desk: read drivers without confusing tool and signal',
        seo_bias_desk_intro: 'A Bias Desk summarizes a market read: momentum, macro, event risk, sentiment and main drivers. It does not replace a strategy, but it can help avoid decisions based on one isolated input.',
        seo_bias_desk_section1_title: 'What a bias means',
        seo_bias_desk_section1_copy: 'A bias is a context orientation, not certainty. Bullish means several elements support upside. Bearish means downside pressures dominate. Neutral or WAIT often indicates a lack of alignment.',
        seo_bias_desk_section2_title: 'Why drivers matter more than the score alone',
        seo_bias_desk_section2_copy: 'The score gives a quick synthesis, but the reasons matter more. A trader should know whether the bias comes from the dollar, yields, momentum, news or event risk.',
        seo_bias_desk_section3_title: 'Read event risk',
        seo_bias_desk_section3_copy: 'A favorable context can become dangerous just before a major release. If the calendar shows elevated risk, the right decision may be to wait, even if the rest of the market seems aligned.',
        seo_bias_desk_section4_title: 'Use the bias with the chart',
        seo_bias_desk_section4_copy: 'The chart remains essential for timing. The bias helps prepare the scenario; price helps decide whether that scenario deserves execution, invalidation or simple observation.',
        seo_bias_desk_section5_title: 'The limits of automatic synthesis',
        seo_bias_desk_section5_copy: 'No tool can perfectly understand every market nuance. The Bias Desk should be treated as a reading aid, with human verification and independent risk management.',
        seo_bias_desk_faq1_question: 'Does the Bias Desk give buy or sell signals?',
        seo_bias_desk_faq1_answer: 'No. It organizes market drivers. The decision to enter, exit or stay aside must come from your strategy, timing and risk management.',
        seo_bias_desk_faq2_question: 'Why does the Bias Desk sometimes show WAIT?',
        seo_bias_desk_faq2_answer: 'WAIT appears when drivers are mixed, confidence is insufficient or event risk makes the read too unstable.',
        seo_bias_desk_link1: 'View the XAU/USD terminal',
        seo_bias_desk_link2: 'Build a routine',
        seo_bias_desk_link3: 'Read the trading disclaimer',
    },
};

Object.keys(SEO_COPY).forEach((lang) => {
    LANDING_COPY[lang] = { ...LANDING_COPY[lang], ...SEO_COPY[lang] };
});

function t(key) {
    return LANDING_COPY[landingLang]?.[key] || LANDING_COPY.fr[key] || key;
}

function legalConfirmMessage(plan) {
    return t(plan === 'lifetime' ? 'legal_confirm_lifetime' : 'legal_confirm_subscription');
}

function applyLandingLanguage() {
    document.documentElement.lang = landingLang;
    document.querySelectorAll('[data-i18n]').forEach((el) => {
        el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
        el.placeholder = t(el.dataset.i18nPlaceholder);
    });
    document.querySelectorAll('[data-i18n-content]').forEach((el) => {
        el.setAttribute('content', t(el.dataset.i18nContent));
    });

    const title = document.querySelector('title[data-i18n]');
    if (title) {
        const titleKey = title.dataset.i18n || 'meta_title';
        const translatedTitle = t(titleKey);
        title.textContent = titleKey === 'meta_title' || /xauterminal/i.test(translatedTitle)
            ? translatedTitle
            : `${translatedTitle} - XAUTERMINAL`;
    }

    const toggle = document.querySelector('[data-lang-toggle]');
    if (toggle) toggle.textContent = landingLang === 'fr' ? 'EN' : 'FR';

    setLandingAuthMode(landingAuthMode);
}

function setLandingMessage(message = '', tone = '') {
    const el = document.getElementById('landing-auth-message');
    if (!el) return;
    el.textContent = message;
    el.className = `landing-auth-message${tone ? ` ${tone}` : ''}`;
}

function setLandingEmail(email = '') {
    const emailEl = document.getElementById('landing-auth-email');
    if (emailEl) emailEl.value = email;
}

function setLandingAuthMode(mode) {
    landingAuthMode = mode === 'login' ? 'login' : mode === 'confirm' ? 'confirm' : mode === 'reset' ? 'reset' : 'register';

    const kicker = document.getElementById('landing-auth-kicker');
    const title = document.getElementById('landing-auth-title');
    const copy = document.getElementById('landing-auth-copy');
    const submit = document.getElementById('landing-auth-submit');
    const switchBtn = document.getElementById('landing-auth-switch');
    const forgotBtn = document.getElementById('landing-auth-forgot');
    const password = document.getElementById('landing-auth-password');
    const codeInput = document.getElementById('landing-auth-code');

    if (kicker) kicker.textContent = landingAuthMode === 'login' ? t('auth_login_kicker') : landingAuthMode === 'confirm' ? 'Confirmation email' : landingAuthMode === 'reset' ? t('auth_reset_kicker') : t('auth_register_kicker');
    if (title) title.textContent = landingAuthMode === 'login' ? t('auth_login_title') : landingAuthMode === 'confirm' ? 'Confirme ton adresse email' : landingAuthMode === 'reset' ? t('auth_reset_title') : t('auth_register_title');
    if (copy) copy.textContent = landingAuthMode === 'login'
        ? t('auth_login_copy')
        : landingAuthMode === 'confirm'
        ? 'Saisis le code de confirmation recu par email pour activer ton essai.'
        : landingAuthMode === 'reset'
        ? t('auth_reset_copy')
        : t('auth_register_copy');
    if (submit) submit.textContent = landingAuthMode === 'login' ? t('auth_login_submit') : landingAuthMode === 'confirm' ? 'Valider le code' : landingAuthMode === 'reset' ? t('auth_reset_submit') : t('auth_register_submit');
    if (switchBtn) switchBtn.textContent = landingAuthMode === 'login' ? t('auth_login_switch') : landingAuthMode === 'reset' ? t('auth_reset_switch') : t('auth_register_switch');
    if (forgotBtn) {
        forgotBtn.textContent = t('auth_forgot');
        forgotBtn.hidden = landingAuthMode !== 'login';
    }
    if (password) {
        password.style.display = landingAuthMode === 'confirm' || landingAuthMode === 'reset' ? 'none' : '';
        password.required = landingAuthMode !== 'confirm' && landingAuthMode !== 'reset';
        password.autocomplete = landingAuthMode === 'login' ? 'current-password' : 'new-password';
    }
    if (codeInput) {
        codeInput.style.display = landingAuthMode === 'confirm' ? '' : 'none';
        codeInput.required = landingAuthMode === 'confirm';
    }
}

function openLandingAuth(mode = 'register') {
    const modal = document.getElementById('landing-auth');
    const email = document.getElementById('landing-auth-email');
    if (!modal) return;

    setLandingAuthMode(mode);
    setLandingMessage('');
    modal.classList.remove('hidden');
    window.setTimeout(() => email?.focus(), 30);
}

function closeLandingAuth() {
    const modal = document.getElementById('landing-auth');
    if (modal) modal.classList.add('hidden');
}

function showLandingAccountState(showTerminal = false) {
    const terminalLink = document.getElementById('landing-terminal-link');
    const loginBtn = document.querySelector('.landing-login');
    if (terminalLink && showTerminal) terminalLink.classList.remove('hidden');
    if (loginBtn) {
        loginBtn.textContent = t('nav_account');
        loginBtn.dataset.i18n = 'nav_account';
        loginBtn.dataset.authMode = 'account';
        loginBtn.dataset.accountLink = 'true';
    }
}

async function fetchLandingAccount() {
    try {
        const response = await fetch('/api/account/me', { cache: 'no-store' });
        const payload = await response.json();
        if (payload.authenticated) {
            showLandingAccountState(!!payload.account?.has_access);
        }
    } catch (error) {
        console.error(error);
    }
}

async function submitLandingAuth(event) {
    event.preventDefault();

    const emailEl = document.getElementById('landing-auth-email');
    const passwordEl = document.getElementById('landing-auth-password');
    if (!emailEl || !passwordEl) return;

    const email = emailEl.value.trim().toLowerCase();
    const password = passwordEl.value;
    if (!email || (landingAuthMode !== 'confirm' && landingAuthMode !== 'reset' && !password)) return;

    try {
        setLandingMessage(landingAuthMode === 'login' ? t('auth_loading_login') : landingAuthMode === 'confirm' ? 'Confirmation du code...' : landingAuthMode === 'reset' ? t('auth_loading_reset') : t('auth_loading_register'));
        if (landingAuthMode === 'reset') {
            const response = await fetch('/api/account/password-reset/request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.detail || t('auth_error'));
            setLandingMessage(payload.message || t('auth_reset_sent'), 'ok');
            return;
        }

        const body = { email, password };
        const endpoint = landingAuthMode === 'confirm' ? 'confirm-email' : landingAuthMode;
        if (landingAuthMode === 'confirm') {
            const codeEl = document.getElementById('landing-auth-code');
            body.code = codeEl ? codeEl.value.trim() : '';
        }
        const response = await fetch(`/api/account/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const payload = await response.json();
        if (!response.ok) {
            if (response.status === 409 && landingAuthMode === 'register') {
                setLandingAuthMode('login');
                setLandingMessage(payload.detail || t('auth_existing_account'), 'err');
                return;
            }
            throw new Error(payload.detail || 'Action impossible');
        }

        if (landingAuthMode === 'register' && payload.pending) {
            setLandingAuthMode('confirm');
            setLandingMessage('Code envoye. Saisis le code depuis ton email.', 'ok');
            return;
        }

        if (landingAuthMode === 'login' && payload.pending) {
            setLandingAuthMode('confirm');
            setLandingMessage('Code envoye. Saisis le code depuis ton email.', 'ok');
            return;
        }

        if (selectedBillingPlan) {
            await startBillingCheckout(selectedBillingPlan);
            return;
        }

        showLandingAccountState(!!payload.account?.has_access);

        if (!payload.account?.has_access) {
            if (payload.account?.email_confirmed) {
                setLandingMessage('Ton email est confirme. Choisis une formule Stripe pour demarrer ton essai.', 'ok');
                return;
            }
            setLandingMessage(t('auth_no_access'), 'err');
            return;
        }

        setLandingMessage(t('auth_success'), 'ok');
        showLandingAccountState(true);
        window.setTimeout(() => {
            closeLandingAuth();
            setLandingMessage('');
        }, 500);
    } catch (error) {
        setLandingMessage(error.message || t('auth_error'), 'err');
    }
}

async function startBillingCheckout(plan) {
    if (!window.confirm(legalConfirmMessage(plan))) {
        setLandingMessage('');
        return;
    }
    try {
        setLandingMessage(t('billing_redirect'));
        const response = await fetch('/api/billing/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plan, accepted_terms: true, immediate_access_acknowledged: true }),
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.detail || t('billing_error'));
        }
        window.location.href = payload.url;
    } catch (error) {
        setLandingMessage(error.message || t('billing_error'), 'err');
    }
}

async function handleBillingPlan(plan) {
    selectedBillingPlan = plan;
    try {
        const response = await fetch('/api/account/me', { cache: 'no-store' });
        const payload = await response.json();
        if (payload.authenticated) {
            if (payload.account && !payload.account.email_confirmed) {
                openLandingAuth('confirm');
                setLandingEmail(payload.account.email || '');
                setLandingMessage('Confirme ton email avec le code recu avant de choisir une formule.', 'err');
                return;
            }
            await startBillingCheckout(plan);
            return;
        }
    } catch (error) {
        console.error(error);
    }
    openLandingAuth('register');
}

function bindLanding() {
    document.querySelectorAll('[data-pricing-scroll]').forEach((button) => {
        button.addEventListener('click', () => {
            selectedBillingPlan = null;
            document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    document.querySelectorAll('[data-auth-mode]').forEach((button) => {
        button.addEventListener('click', () => {
            if (button.dataset.accountLink === 'true' || button.dataset.authMode === 'account') {
                window.location.href = '/account';
                return;
            }
            selectedBillingPlan = null;
            openLandingAuth(button.dataset.authMode);
        });
    });

    document.querySelectorAll('[data-billing-plan]').forEach((button) => {
        button.addEventListener('click', () => handleBillingPlan(button.dataset.billingPlan));
    });

    const langToggle = document.querySelector('[data-lang-toggle]');
    if (langToggle) {
        langToggle.addEventListener('click', () => {
            landingLang = landingLang === 'fr' ? 'en' : 'fr';
            localStorage.setItem('xt_lang', landingLang);
            applyLandingLanguage();
        });
    }

    const close = document.getElementById('landing-auth-close');
    if (close) close.addEventListener('click', closeLandingAuth);

    const switchBtn = document.getElementById('landing-auth-switch');
    if (switchBtn) {
        switchBtn.addEventListener('click', () => {
            setLandingAuthMode(landingAuthMode === 'login' ? 'register' : 'login');
            setLandingMessage('');
        });
    }

    const forgotBtn = document.getElementById('landing-auth-forgot');
    if (forgotBtn) {
        forgotBtn.addEventListener('click', () => {
            setLandingAuthMode('reset');
            setLandingMessage('');
        });
    }

    const form = document.getElementById('landing-auth-form');
    if (form) form.addEventListener('submit', submitLandingAuth);

    const modal = document.getElementById('landing-auth');
    if (modal) {
        modal.addEventListener('click', (event) => {
            if (event.target === modal) closeLandingAuth();
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    applyLandingLanguage();
    bindLanding();
    fetchLandingAccount();
});
