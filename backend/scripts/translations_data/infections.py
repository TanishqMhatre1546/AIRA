"""Translations for Dengue Fever, Bacterial Skin Infections, and Urinary Tract Infection (UTI)."""

INFECTIONS_TRANSLATIONS: dict[str, tuple[str, str]] = {
    # === dengue_fever ===
    "Severe abdominal pain or tenderness": (
        "पेट में बहुत तेज दर्द या छूने पर अत्यधिक संवेदनशीलता",
        "पोटात तीव्र वेदना किंवा दाब दिल्यास असह्य दुखणे",
    ),
    "Persistent vomiting that does not stop": (
        "लगातार उल्टी होना जो रुक न रही हो",
        "सतत उलट्या होणे ज्या थांबत नाहीत",
    ),
    "Bleeding from any site: black or tarry stools, bleeding gums, nosebleed, blood in urine, or unusual bruising": (
        "किसी भी अंग से रक्तस्राव: काला मल, मसूड़ों से खून, नाक से खून, पेशाब में खून, या त्वचा पर असामान्य नीले निशान",
        "कोणत्याही भागातून रक्तस्त्राव: काळी विष्ठा, हिरड्यांमधून रक्त, नाकातून रक्त, लघवीतून रक्त, किंवा त्वचेवर असामान्य काळे-निळे डाग",
    ),
    "Fluid accumulation visible as swelling of the abdomen or difficulty breathing due to fluid around the lungs": (
        "द्रव जमा होना जो पेट की सूजन या फेफड़ों के चारों ओर तरल पदार्थ के कारण सांस लेने में कठिनाई के रूप में दिखे",
        "शरीरात पाणी साठणे जे पोटावर सूज किंवा फुफ्फुसाभोवती पाणी झाल्यामुळे श्वासाच्या त्रासाच्या स्वरूपात दिसते",
    ),
    "Liver enlargement (swollen or tender abdomen on the right side)": (
        "लिवर का बढ़ना (पेट के दाहिने हिस्से में सूजन या दर्द)",
        "यकृत (लिव्हर) वाढणे (पोटाच्या उजव्या बाजूला सूज किंवा दुखणे)",
    ),
    "Confusion, altered behaviour, or loss of consciousness": (
        "भ्रम, व्यवहार में असामान्य बदलाव, या बेहोशी",
        "गोंधळ, वर्तनातील अचानक बदल, किंवा बेशुद्धी",
    ),
    "Signs of shock: weak and rapid pulse, cold and clammy skin, extreme restlessness or sudden fatigue, low blood pressure": (
        "शॉक (सदमे) के लक्षण: कमजोर और तेज नब्ज, ठंडी और चिपचिपी त्वचा, अत्यधिक बेचैनी या अचानक थकान, कम रक्तचाप",
        "शॉकची (धक्क्याची) लक्षणे: अतिशय कमकुवत व जलद नाडी, थंड आणि चिकट त्वचा, प्रचंड अस्वस्थता किंवा अचानक थकवा, कमी रक्तदाब",
    ),
    "Decreased or no urine output for several hours": (
        "कई घंटों तक बहुत कम या बिल्कुल पेशाब न होना",
        "अनेक तास लघवीचे प्रमाण खूप कमी होणे किंवा अजिबात लघवी न होणे",
    ),
    "Sudden drop in fever combined with worsening of general condition, this is a dangerous phase in dengue": (
        "बुखार का अचानक उतरना और साथ ही सामान्य स्थिति का और बिगड़ जाना, यह डेंगू में एक खतरनाक चरण है",
        "ताप अचानक उतरणे आणि त्याच वेळी रुग्णाची प्रकृती अधिक खालावणे, हा डेंग्यूमधील अत्यंत धोक्याचा टप्पा आहे",
    ),
    "Rest completely, do not attempt to go to work or school": (
        "पूरी तरह आराम करें, काम या स्कूल जाने का प्रयास न करें",
        "पूर्ण विश्रांती घ्या, कामावर किंवा शाळेत जाण्याचा प्रयत्न करू नका",
    ),
    "Drink plenty of fluids: water, ORS, coconut water, fruit juices, soups, dengue causes significant fluid loss": (
        "प्रचुर मात्रा में तरल पदार्थ पिएं: पानी, ORS, नारियल पानी, फलों का रस, सूप, डेंगू से शरीर में पानी की भारी कमी होती है",
        "भरपूर प्रमाणात द्रवपदार्थ प्या: पाणी, ORS, नारळ पाणी, फळांचे रस, सूप, डेंग्यूमुळे शरीरातील पाण्याचे मोठे नुकसान होते",
    ),
    "Take paracetamol for fever only, do not take aspirin, ibuprofen, or other NSAIDs as these increase the risk of bleeding in dengue": (
        "बुखार के लिए केवल पैरासिटामोल लें, एस्पिरिन, इबुप्रोफेन या अन्य दर्द निवारक (NSAIDs) न लें क्योंकि ये डेंगू में रक्तस्राव का जोखिम बढ़ाते हैं",
        "तापासाठी फक्त पॅरासिटामॉल घ्या, अ‍ॅस्पिरिन, आयबुप्रोफेन किंवा इतर वेदनाशामक औषधे घेऊ नका कारण यामुळे डेंग्यूमध्ये रक्तस्त्रावाचा धोका वाढतो",
    ),
    "Apply a cold compress or sponge with lukewarm water for high fever": (
        "तेज बुखार के लिए गुनगुने पानी की पट्टी या स्पंज का प्रयोग करें",
        "तीव्र तापासाठी कोमट पाण्याच्या पट्ट्या कपाळावर ठेवा किंवा अंग पुसून घ्या",
    ),
    "Protect the patient from further mosquito bites to prevent spreading dengue to others, use mosquito nets and repellents": (
        "दूसरों में डेंगू फैलने से रोकने के लिए मरीज को मच्छरों के काटने से बचाएं, मच्छरदानी और विकर्षक (रेपेलेंट) का उपयोग करें",
        "इतरांना डेंग्यूचा संसर्ग पसरू नये म्हणून रुग्णाला डास चावण्यापासून वाचवा, मच्छरदाणी आणि डास प्रतिबंधक वापरा",
    ),
    "Daily monitoring is essential even at home: check if the person can drink fluids, passes urine, and has no new bleeding": (
        "घर पर भी दैनिक निगरानी आवश्यक है: जांचें कि क्या व्यक्ति तरल पदार्थ पी पा रहा है, पेशाब कर रहा है, और कहीं से नया रक्तस्राव तो नहीं है",
        "घरीसुद्धा दररोज लक्ष ठेवणे अत्यावश्यक आहे: रुग्ण पाणी पिऊ शकतो का, लघवी होते का आणि कुठूनही रक्तस्त्राव होत नाही ना हे तपासा",
    ),
    "Monitor closely for any warning sign listed above, if any appear, go to hospital immediately": (
        "ऊपर दिए गए किसी भी चेतावनी संकेत पर कड़ी निगरानी रखें, यदि कोई भी संकेत दिखे, तो तुरंत अस्पताल जाएं",
        "वर दिलेल्या कोणत्याही धोक्याच्या लक्षणावर बारीक लक्ष ठेवा, असे काही आढळल्यास तातडीने रुग्णालयात जा",
    ),
    "Do not self-medicate with any anti-inflammatory or blood-thinning medicines": (
        "किसी भी सूजन-रोधी या खून पतला करने वाली दवाओं से खुद का इलाज न करें",
        "कोणतीही सूज कमी करणारी किंवा रक्त पातळ करणारी औषधे स्वतःहून घेऊ नका",
    ),
    "Fever that persists beyond 2 to 3 days without improvement": (
        "बुखार जो 2 से 3 दिन से अधिक समय तक बिना किसी सुधार के बना रहे",
        "कोणत्याही सुधाराशिवाय 2 ते 3 दिवसांपेक्षा जास्त काळ टिकणारा ताप",
    ),
    "Fever with severe headache, pain behind the eyes, and body aches, especially in a dengue-prone area or after recent travel": (
        "तेज सिरदर्द, आँखों के पीछे दर्द और बदन दर्द के साथ बुखार, विशेषकर डेंगू प्रभावित क्षेत्र में या हालिया यात्रा के बाद",
        "तीव्र डोकेदुखी, डोळ्यांच्या मागे वेदना आणि अंगदुखीसह ताप, विशेषतः डेंग्यूची साथ असलेल्या भागात किंवा प्रवासानंतर",
    ),
    "Fever suddenly dropping but the person feeling worse, this is a critical phase requiring monitoring": (
        "बुखार अचानक कम होना लेकिन व्यक्ति का अधिक अस्वस्थ महसूस करना, यह निगरानी की आवश्यकता वाला एक गंभीर चरण है",
        "ताप अचानक कमी होणे पण रुग्णाला अधिक अशक्त किंवा आजारी वाटणे, ही देखरेखीची गरज असणारी धोक्याची वेळ आहे",
    ),
    "Fever with a skin rash": (
        "त्वचा पर चकत्तों के साथ बुखार होना",
        "त्वचेवर लाल पुरळ येण्यासह ताप असणे",
    ),
    "Any dengue fever in a child, elderly person, pregnant woman, or someone with diabetes, heart disease, or kidney disease, these groups are at higher risk of severe dengue": (
        "बच्चे, बुजुर्ग, गर्भवती महिला, या मधुमेह, हृदय रोग या गुर्दे की बीमारी वाले किसी व्यक्ति में डेंगू बुखार, ये गंभीर डेंगू के उच्च जोखिम में हैं",
        "लहान मुले, वृद्ध, गरोदर महिला, किंवा मधुमेह, हृदयरोग किंवा मूत्रपिंडाचा आजार असलेल्या व्यक्तीमधील डेंग्यू ताप, यांना गंभीर डेंग्यूचा मोठा धोका असतो",
    ),
    "Any warning sign listed above, severe abdominal pain, persistent vomiting, bleeding, signs of shock, confusion, no urine output": (
        "ऊपर सूचीबद्ध कोई भी चेतावनी संकेत, पेट में तेज दर्द, लगातार उल्टी, रक्तस्राव, शॉक के लक्षण, भ्रम, पेशाब न होना",
        "वर नमूद केलेले कोणतेही धोक्याचे लक्षण, पोटात तीव्र वेदना, सतत उलट्या, रक्तस्त्राव, शॉकची लक्षणे, गोंधळ, लघवी न होणे",
    ),
    "Dengue with suspected shock: cold extremities, restlessness, weak pulse": (
        "संदिग्ध शॉक के साथ डेंगू: हाथ-पैर ठंडे पड़ना, बेचैनी, कमजोर नब्ज",
        "संशयित शॉकसह डेंग्यू: हातपाय थंड पडणे, अस्वस्थता, अत्यंत कमकुवत नाडी",
    ),
    "Dengue with active bleeding from any site": (
        "किसी भी अंग से सक्रिय रक्तस्राव के साथ डेंगू",
        "कोणत्याही भागातून सक्रिय रक्तस्त्राव होणारा डेंग्यू",
    ),
    "Dengue with severe difficulty breathing": (
        "सांस लेने में गंभीर कठिनाई के साथ डेंगू",
        "श्वास घेण्यास प्रचंड त्रास होणारा डेंग्यू",
    ),
    "Dengue with impaired consciousness": (
        "चेतना या होश में कमी के साथ डेंगू",
        "शुद्ध हरपलेला किंवा बेशुद्धावस्थेतील डेंग्यू",
    ),
    "Dengue is a mosquito-borne viral fever. Suspect dengue if a person has fever and two or more of the following: nausea, vomiting, rash, muscle pain, headache, pain behind the eyes, joint pain, or unusual bleeding, especially if they live in or recently travelled to a dengue-prone area.": (
        "डेंगू मच्छरों से फैलने वाला वायरल बुखार है। डेंगू का संदेह करें यदि किसी व्यक्ति को बुखार हो और निम्नलिखित में से 2 या अधिक लक्षण हों: मतली, उल्टी, चकत्ते, मांसपेशियों में दर्द, सिरदर्द, आँखों के पीछे दर्द, जोड़ों का दर्द, या असामान्य रक्तस्राव।",
        "डेंग्यू हा डासांमुळे होणारा विषाणूजन्य ताप आहे. जर एखाद्या व्यक्तीला ताप असेल आणि खालीलपैकी 2 किंवा अधिक लक्षणे असतील तर डेंग्यूचा संशय घ्यावा: मळमळ, उलट्या, पुरळ, स्नायूदुखी, डोकेदुखी, डोळ्यांमागे दुखणे, सांधेदुखी किंवा असामान्य रक्तस्त्राव.",
    ),
    "Dengue must be managed under medical supervision with daily monitoring of blood counts and clinical status. Do not treat dengue at home beyond basic supportive care. The transition from mild to severe dengue can happen quickly.": (
        "डेंगू का प्रबंधन रक्त गणना और नैदानिक स्थिति की दैनिक निगरानी के साथ चिकित्सकीय देखरेख में किया जाना चाहिए। बुनियादी सहायक देखभाल के अलावा घर पर डेंगू का इलाज न करें। हल्के से गंभीर डेंगू में परिवर्तन तेजी से हो सकता है।",
        "डेंग्यूचे व्यवस्थापन रक्ताच्या तपासण्या आणि प्रकृतीवर दैनंदिन लक्ष ठेवून डॉक्टरांच्या देखरेखीखालीच केले पाहिजे. मूलभूत काळजीव्यतिरिक्त घरी डेंग्यूवर स्वतः उपचार करू नका. हलक्या डेंग्यूचे गंभीर डेंग्यूमध्ये रूपांतर वेगाने होऊ शकते.",
    ),

    # === bacterial_skin_infections ===
    "Fever above 100.4 degrees Fahrenheit": (
        "100.4 degrees Fahrenheit से अधिक बुखार होना",
        "100.4 degrees Fahrenheit पेक्षा जास्त ताप असणे",
    ),
    "Heart rate above 90 beats per minute": (
        "प्रति मिनट 90 धड़कनों से अधिक हृदय गति होना",
        "दर मिनिटास 90 पेक्षा जास्त हृदयाचे ठोके असणे",
    ),
    "Breathing rate above 24 breaths per minute": (
        "प्रति मिनट 24 से अधिक बार सांस लेना",
        "दर मिनिटास 24 पेक्षा जास्त वेळा श्वास घेणे",
    ),
    "Low blood pressure or signs of shock": (
        "कम रक्तचाप (लो BP) या शॉक के लक्षण",
        "कमी रक्तदाब (लो BP) किंवा शॉकची लक्षणे",
    ),
    "Severe pain in the skin followed by a sudden, deceptive absence of pain, this may indicate necrotising fasciitis, a life-threatening infection": (
        "त्वचा में असहनीय दर्द के बाद अचानक दर्द का समाप्त हो जाना, यह नेक्रोटाइजिंग फासिसाइटिस का संकेत हो सकता है, जो जानलेवा संक्रमण है",
        "त्वचेत प्रचंड वेदना झाल्यानंतर अचानक वेदना पूर्ण थांबणे, हे नेक्रोटायझिंग फॅसिटिसचे लक्षण असू शकते, जो जीवघेणा संसर्ग आहे",
    ),
    "Skin blistering, sloughing (peeling off), or tissue breakdown": (
        "त्वचा पर फफोले पड़ना, त्वचा का छिलना या ऊतकों का क्षय होना",
        "त्वचेवर फोड येणे, त्वचा निघून पडणे (सोलवटणे) किंवा ऊती खराब होणे",
    ),
    "Dark skin over an infected area": (
        "संक्रमित क्षेत्र के ऊपर त्वचा का काला पड़ना",
        "संसर्ग झालेल्या भागावरील त्वचा काळी पडणे",
    ),
    "Signs of blood poisoning (septicaemia): high fever, confusion, rapid deterioration": (
        "रक्त विषाक्तता (सेप्टिसीमिया) के संकेत: तेज बुखार, भ्रम, तेजी से स्थिति बिगड़ना",
        "रक्तातील संसर्गाची (सेप्टिसेमिया) लक्षणे: तीव्र ताप, गोंधळलेली मानसिक अवस्था, प्रकृतीत जलद बिघाड",
    ),
    "Very high white blood cell count (signs of sepsis)": (
        "श्वेत रक्त कोशिकाओं (WBC) की अत्यधिक संख्या (सेप्सिस का संकेत)",
        "पांढऱ्या रक्तपेशींचे (WBC) प्रमाण खूप जास्त असणे (सेप्सिसचे लक्षण)",
    ),
    "Skin that appears tender and warm before it starts to peel": (
        "त्वचा जो छिलने से पहले संवेदनशील, दर्दनाक और गर्म महसूस होती है",
        "त्वचा सोलवटण्यापूर्वी दुखरी आणि गरम जाणवणे",
    ),
    "For small wounds or minor folliculitis, keep the area clean and dry": (
        "छोटे घावों या हल्के फॉलिकुलिटिस के लिए प्रभावित क्षेत्र को साफ और सूखा रखें",
        "लहान जखमा किंवा किरकोळ फोडांसाठी तो भाग स्वच्छ आणि कोरडा ठेवा",
    ),
    "Maintain good skin hygiene and wash hands regularly": (
        "त्वचा की अच्छी स्वच्छता बनाए रखें और नियमित रूप से हाथ धोएं",
        "त्वचेची चांगली स्वच्छता राखा आणि नियमितपणे हात धुवा",
    ),
    "Wash clothes and towels separately in hot water and dry them in sunlight": (
        "कपड़े और तौलिये गर्म पानी में अलग से धोएं और उन्हें धूप में सुखाएं",
        "कपडे आणि टॉवेल गरम पाण्यात वेगळे धुवा आणि उन्हात वाळवा",
    ),
    "Avoid sharing towels, clothes, or personal items with others": (
        "दूसरों के साथ तौलिया, कपड़े या व्यक्तिगत वस्तुएं साझा करने से बचें",
        "इतरांसोबत टॉवेल, कपडे किंवा वैयक्तिक वस्तू वापरणे टाळा",
    ),
    "Avoid applying oil on affected skin": (
        "प्रभावित त्वचा पर तेल लगाने से बचें",
        "संसर्ग झालेल्या त्वचेवर तेल लावणे टाळा",
    ),
    "Eat adequate nutritious food to support healing": (
        "घाव भरने में सहायता के लिए पर्याप्त पौष्टिक भोजन करें",
        "त्वचा बरी होण्यास मदत होण्यासाठी पुरेसा पौष्टिक आहार घ्या",
    ),
    "Do not squeeze, pick, or burst a boil or abscess, this can spread the infection": (
        "किसी फोड़े या फुंसी को दबाएं, फोड़ें या खरोंचें नहीं, इससे संक्रमण फैल सकता है",
        "कोणताही फोड किंवा गळू दाबू नका किंवा फोडू नका, यामुळे संसर्ग पसरू शकतो",
    ),
    "A boil, abscess, or skin swelling that is growing larger, becoming more painful, or not improving": (
        "एक फोड़ा, फुंसी या त्वचा की सूजन जो बड़ी हो रही हो, अधिक दर्दनाक हो, या सुधर न रही हो",
        "फोड, गळू किंवा सूज जी आकाराने वाढत आहे, अधिक दुखत आहे किंवा बरी होत नाही",
    ),
    "Redness spreading outward from a wound or infection site": (
        "घाव या संक्रमण स्थल से बाहर की ओर लालिमा का फैलना",
        "जखमेपासून किंवा संसर्गाच्या भागापासून लालसरपणा बाहेर पसरणे",
    ),
    "Fever with general feeling of being very unwell": (
        "तेज अस्वस्थता की सामान्य भावना के साथ बुखार होना",
        "खूप आजारी वाटण्याच्या भावनेसोबत ताप असणे",
    ),
    "Impetigo (wet yellow-brown crusts over inflamed skin) that is widespread or not improving": (
        "इम्पेटिगो (सूजी हुई त्वचा पर गीली पीली-भूरी पपड़ी) जो व्यापक हो या ठीक न हो रही हो",
        "इम्पेटिगो (सुजलेल्या त्वचेवर पिवळसर-तपकिरी खपल्या) जो खूप पसरला आहे किंवा बरा होत नाही",
    ),
    "A thick black crust with an underlying sore (ecthyma)": (
        "नीचे घाव के साथ एक मोटी काली पपड़ी (एक्थिमा)",
        "खाली जखम असणारी जाड काळी खपली (एक्थिमा)",
    ),
    "A large abscess or carbuncle that requires drainage": (
        "एक बड़ा फोड़ा या कार्बंकल जिसे मवाद निकालने (ड्रेनेज) की आवश्यकता हो",
        "मोठे गळू किंवा कार्बंकल ज्यातून शस्त्रक्रियेने पू काढण्याची गरज असते",
    ),
    "Skin infection in a person with diabetes, skin infections tend to be more severe in diabetic patients": (
        "मधुमेह से पीड़ित व्यक्ति में त्वचा का संक्रमण, ऐसे मरीजों में त्वचा संक्रमण अधिक गंभीर हो सकता है",
        "मधुमेह असलेल्या व्यक्तीमध्ये त्वचेचा संसर्ग, मधुमेही रुग्णांमध्ये त्वचेचे संसर्ग अधिक गंभीर होतात",
    ),
    "A skin infection in someone who is immunocompromised (on steroids, chemotherapy, or with HIV)": (
        "कमजोर प्रतिरक्षा वाले व्यक्ति (स्टेरॉयड, कीमोथेरेपी या एचआईवी) में त्वचा संक्रमण",
        "कमी प्रतिकारशक्ती असलेल्या व्यक्तीमध्ये (स्टेरॉईड्स, केमोथेरपी किंवा एचआयव्ही) त्वचेचा संसर्ग",
    ),
    "Recurrent boils or folliculitis in multiple family members": (
        "परिवार के कई सदस्यों में बार-बार फोड़े या फॉलिकुलिटिस होना",
        "कुटुंबातील अनेक व्यक्तींमध्ये वारंवार फोड किंवा गळू येणे",
    ),
    "Infection affecting the lower limbs with redness, pain, and swelling (cellulitis)": (
        "पैरों को प्रभावित करने वाला संक्रमण जिसमें लालिमा, दर्द और सूजन हो (सेल्युलाइटिस)",
        "पायांना होणारा संसर्ग ज्यामध्ये लालसरपणा, वेदना आणि सूज असते (सेल्युलायटिस)",
    ),
    "No improvement after 2 to 3 days of treatment": (
        "2 से 3 दिन के उपचार के बाद भी कोई सुधार न होना",
        "2 ते 3 दिवसांच्या उपचारानंतरही काही सुधारणा न होणे",
    ),
    "Any skin infection with mild fever": (
        "हल्के बुखार के साथ त्वचा का कोई भी संक्रमण",
        "हलक्या तापासह त्वचेचा कोणताही संसर्ग असणे",
    ),
    "Severe pain followed by sudden relief, possible necrotising fasciitis": (
        "असहनीय दर्द के बाद अचानक राहत मिलना, यह संभावित नेक्रोटाइजिंग फासिसाइटिस है",
        "प्रचंड वेदनेनंतर अचानक आराम वाटणे, संशयित नेक्रोटायझिंग फॅसिटिस असू शकते",
    ),
    "Widespread peeling or scaling of skin across the body": (
        "पूरे शरीर की त्वचा का व्यापक रूप से छिलना या पपड़ी बनना",
        "संपूर्ण शरीरावरील त्वचा मोठ्या प्रमाणावर सोलवटणे किंवा पापुद्रे निघणे",
    ),
    "Signs of dehydration": (
        "निर्जलीकरण (शरीर में पानी की कमी) के लक्षण",
        "डिहायड्रेशन (शरीरातील पाणी कमी होणे) ची लक्षणे",
    ),
    "Dark discoloration of the overlying skin": (
        "प्रभावित क्षेत्र के ऊपर की त्वचा का काला पड़ना",
        "वरच्या त्वचेचा रंग काळा पडणे",
    ),
    "Widespread skin peeling or blistering": (
        "त्वचा का व्यापक रूप से छिलना या फफोले पड़ना",
        "मोठ्या प्रमाणावर त्वचा सोलवटणे किंवा फोड येणे",
    ),
    "Any red flag sign listed above, fever, fast heartbeat, fast breathing, low blood pressure": (
        "ऊपर सूचीबद्ध कोई भी गंभीर संकेत, बुखार, तेज दिल की धड़कन, तेज सांस, कम रक्तचाप",
        "वर नमूद केलेले कोणतेही धोक्याचे लक्षण, ताप, जलद हृदयाचे ठोके, जलद श्वास, कमी रक्तदाब",
    ),
    "Impetigo": (
        "इम्पेटिगो (त्वचा पर पपड़ीदार संक्रमण)",
        "इम्पेटिगो (खपल्या धरणारा त्वचारोग)",
    ),
    "Folliculitis": (
        "फॉलिकुलिटिस (बालों की जड़ों का संक्रमण)",
        "फॉलिक्युलायटिस (केसांच्या मुळांचा संसर्ग)",
    ),
    "Furuncle (boil)": (
        "फुरुनकल (फोड़ा / बालतोड़)",
        "फुरुनकल (बाळतोड / गळू)",
    ),
    "Carbuncle": (
        "कार्बंकल (बड़ा फोड़ा)",
        "कार्बंकल (मोठे पूचे गळू)",
    ),
    "Cutaneous abscess": (
        "त्वचा का फोड़ा (एब्सेस)",
        "त्वचेतील गळू (अ‍ॅब्सेस)",
    ),
    "Erysipelas": (
        "एरसिपेलस (त्वचा की तीव्र लाल सूजन)",
        "इरिसिपेलस (त्वचेचा तीव्र लालसर संसर्ग)",
    ),
    "Cellulitis": (
        "सेल्युलाइटिस (त्वचा की भीतरी परतों का संक्रमण)",
        "सेल्युलायटिस (त्वचेच्या खोल थरांचा संसर्ग)",
    ),
    "Ecthyma": (
        "एक्थिमा (गहरा घाव और पपड़ी)",
        "एक्थिमा (खोलवर जखम आणि काळी खपली)",
    ),
    "Staphylococcal scalded skin syndrome": (
        "स्टैफिलोकोकल स्कैल्डेड स्किन सिंड्रोम",
        "स्टॅफिलोकोकल स्केल्डेड स्किन सिंड्रोम",
    ),

    # === urinary_tract_infection ===
    "Fever above 100 degrees Fahrenheit along with urinary symptoms": (
        "पेशाब के लक्षणों के साथ 100 degrees Fahrenheit से अधिक बुखार होना",
        "लघवीच्या त्रासासोबत 100 degrees Fahrenheit पेक्षा जास्त ताप असणे",
    ),
    "Chills and rigors (shaking with cold)": (
        "कंपकंपी और तेज ठंड लगना",
        "थंडी वाजून येणे आणि हुडहुडी भरणे",
    ),
    "Pain or tenderness in the flank (the side of the back, just below the ribs), this may indicate a kidney infection": (
        "कमर के एक तरफ (पसलियों के ठीक नीचे पीठ की तरफ) दर्द, यह गुर्दे के संक्रमण का संकेत हो सकता है",
        "कुशीत किंवा बरगड्यांच्या खाली पाठीच्या बाजूला वेदना, हे मूत्रपिंडाच्या संसर्गाचे लक्षण असू शकते",
    ),
    "Fast heart rate (tachycardia)": (
        "दिल की धड़कन तेज होना (टैचीकार्डिया)",
        "हृदयाचे ठोके जलद पडणे (टॅकीकार्डिया)",
    ),
    "Fast breathing (tachypnoea)": (
        "तेज गति से सांस चलना (टैकिप्निया)",
        "श्वासोच्छ्वास जलद होणे (टॅकिप्निया)",
    ),
    "Low blood pressure (hypotension)": (
        "कम रक्तचाप (लो BP)",
        "कमी रक्तदाब (हायपोटेन्शन / लो BP)",
    ),
    "Confusion or altered mental state (obtundation)": (
        "भ्रम या मानसिक स्थिति में बदलाव (अचेतनता)",
        "गोंधळलेली अवस्था किंवा मानसिक स्थितीत बदल",
    ),
    "Signs of sepsis: high fever, fast heart rate, very unwell appearance, confusion": (
        "सेप्सिस के संकेत: तेज बुखार, तेज दिल की धड़कन, अत्यधिक अस्वस्थता, भ्रम",
        "सेप्सिसची लक्षणे: तीव्र ताप, जलद नाडी, अत्यंत आजारी वाटणे, गोंधळ",
    ),
    "Drink plenty of water and fluids to flush out the urinary tract": (
        "मूत्र मार्ग को साफ रखने के लिए प्रचुर मात्रा में पानी और तरल पदार्थ पिएं",
        "मूत्रमार्ग स्वच्छ राहण्यासाठी भरपूर पाणी आणि द्रवपदार्थ प्या",
    ),
    "Urinate soon after sexual intercourse to help prevent UTIs": (
        "यूटीआई से बचाव के लिए संभोग के तुरंत बाद पेशाब करें",
        "संसर्ग टाळण्यासाठी समागमानंतर लगेच लघवी करा",
    ),
    "Wipe from front to back after using the toilet (for women) to avoid introducing bacteria": (
        "शौचालय के बाद (महिलाओं के लिए) आगे से पीछे की ओर पोंछें ताकि बैक्टीरिया न फैलें",
        "शौचालयानंतर (महिलांसाठी) पुढून मागे पुसावे जेणेकरून जंतूंचा संसर्ग होणार नाही",
    ),
    "Empty your bladder fully each time you urinate": (
        "पेशाब करते समय हर बार मूत्राशय को पूरी तरह खाली करें",
        "लघवी करताना प्रत्येक वेळी मूत्राशय पूर्णपणे रिकामे करा",
    ),
    "Avoid holding urine for long periods": (
        "लंबे समय तक पेशाब रोकने से बचें",
        "दीर्घकाळ लघवी रोखून ठेवणे टाळा",
    ),
    "Paracetamol can be taken for pain relief while waiting to see a doctor": (
        "डॉक्टर को दिखाने तक दर्द से राहत के लिए पैरासिटामोल लिया जा सकता है",
        "डॉक्टरांकडे जाईपर्यंत वेदना कमी करण्यासाठी पॅरासिटामॉल घेता येऊ शकते",
    ),
    "Do not delay seeking a doctor. UTIs require antibiotic treatment prescribed by a doctor and should not be managed with home remedies alone": (
        "डॉक्टर से मिलने में देरी न करें। यूटीआई के लिए डॉक्टर द्वारा निर्धारित एंटीबायोटिक उपचार आवश्यक है, इसे केवल घरेलू नुस्खों से ठीक न करें",
        "डॉक्टरांचा सल्ला घेण्यास उशीर करू नका. युटीआयसाठी डॉक्टरांनी दिलेले अँटीबायोटिक्स आवश्यक असतात, केवळ घरगुती उपायांवर अवलंबून राहू नका",
    ),
    "Burning or pain when urinating": (
        "पेशाब करते समय जलन या दर्द होना",
        "लघवी करताना जळजळ किंवा वेदना होणे",
    ),
    "Frequent urge to urinate even when little urine passes": (
        "बहुत कम पेशाब आने पर भी बार-बार पेशाब की इच्छा होना",
        "थोड्याशा लघवीसाठीही वारंवार लघवीची तीव्र भावना होणे",
    ),
    "Feeling of urgency, needing to rush to the toilet": (
        "अचानक तेज पेशाब महसूस होना और शौचालय की ओर भागना पड़ना",
        "लघवीची घाई होणे आणि तात्काळ शौचालयात जावे लागणे",
    ),
    "Pain or pressure in the lower abdomen or pelvis": (
        "पेट के निचले हिस्से या पेडू में दर्द या दबाव",
        "ओटीपोटात किंवा कमरेच्या खालच्या भागात वेदना किंवा दाब जाणवणे",
    ),
    "Cloudy, dark, or foul-smelling urine": (
        "धुंधला, गहरा या दुर्गंधयुक्त पेशाब आना",
        "ढगाळ, गडद रंगाची किंवा दुर्गंधीयुक्त लघवी येणे",
    ),
    "Blood in the urine": (
        "पेशाब में खून आना",
        "लघवीतून रक्त येणे",
    ),
    "Urinary symptoms in a pregnant woman. UTI in pregnancy requires prompt treatment": (
        "गर्भवती महिला में मूत्र लक्षण। गर्भावस्था में यूटीआई का तुरंत इलाज आवश्यक है",
        "गरोदर महिलांमध्ये लघवीची लक्षणे. गर्भधारणेतील युटीआयवर तातडीने उपचार आवश्यक आहेत",
    ),
    "Urinary symptoms in a person with diabetes, kidney disease, or a known urinary tract abnormality, these are high-risk groups": (
        "मधुमेह, गुर्दे की बीमारी, या मूत्र मार्ग की विकृति वाले व्यक्ति में पेशाब के लक्षण, ये उच्च जोखिम वाले समूह हैं",
        "मधुमेह, मूत्रपिंडाचा आजार किंवा मूत्रमार्गाची विकृती असलेल्या व्यक्तीमध्ये लघवीची लक्षणे, हे उच्च जोखीम गट आहेत",
    ),
    "Recent urological procedure or surgery with new urinary symptoms": (
        "हालिया यूरोलॉजिकल प्रक्रिया या सर्जरी के बाद नए मूत्र लक्षण दिखाई देना",
        "अलीकडेच झालेल्या युरॉलॉजिकल तपासणी किंवा शस्त्रक्रियेनंतर लघवीची नवीन लक्षणे दिसणे",
    ),
    "Symptoms not improving after a full course of prescribed antibiotics": (
        "निर्धारित एंटीबायोटिक्स का पूरा कोर्स करने के बाद भी लक्षणों में सुधार न होना",
        "दिलेल्या अँटीबायोटिक्सचा पूर्ण कोर्स संपल्यानंतरही लक्षणांमध्ये सुधारणा न होणे",
    ),
    "Recurrent UTIs (more than 2 in 6 months or 3 in a year)": (
        "बार-बार यूटीआई होना (6 महीने में 2 से अधिक या 1 वर्ष में 3 से अधिक)",
        "वारंवार युटीआय होणे (6 महिन्यांत 2 पेक्षा जास्त किंवा 1 वर्षात 3 पेक्षा जास्त)",
    ),
    "UTI in a person with known kidney stones or urinary tract obstruction": (
        "गुर्दे की पथरी या मूत्र मार्ग में रुकावट वाले व्यक्ति में यूटीआई",
        "मूत्रपिंडातील खडा (मुतखडा) किंवा मूत्रमार्गात अडथळा असलेल्या व्यक्तीमध्ये युटीआय",
    ),
    "Any red flag sign is present, fever, chills, flank pain, fast heartbeat, low blood pressure": (
        "कोई भी गंभीर लक्षण मौजूद होना, बुखार, ठंड लगना, कमर दर्द, तेज दिल की धड़कन, कम रक्तचाप",
        "कोणतेही धोक्याचे लक्षण असणे, ताप, थंडी वाजणे, कुशीत दुखणे, जलद नाडी, कमी रक्तदाब",
    ),
    "Signs of kidney infection (pyelonephritis): fever, flank pain, very unwell": (
        "गुर्दे के संक्रमण (पायलोनेफ्राइटिस) के संकेत: बुखार, कमर के पार्श्व भाग में दर्द, अत्यधिक अस्वस्थता",
        "मूत्रपिंडाच्या संसर्गाची (पायलोनेफ्रायटिस) लक्षणे: ताप, कुशीत तीव्र वेदना, अत्यंत आजारी वाटणे",
    ),
    "UTI in pregnancy that is complicated or not responding to first treatment": (
        "गर्भावस्था में जटिल यूटीआई या जो शुरुआती उपचार से ठीक न हो रहा हो",
        "गर्भधारणेतील गुंतागुंतीचा युटीआय किंवा पहिल्या उपचाराने बरा न होणारा युटीआय",
    ),
    "Prostatitis: UTI symptoms combined with pelvic pain or a tender prostate in men": (
        "प्रोस्टेटाइटिस: पुरुषों में पेल्विक दर्द या संवेदनशील प्रोस्टेट के साथ यूटीआई के लक्षण",
        "प्रोस्टेटायटिस: पुरुषांमध्ये ओटीपोटात दुखणे किंवा प्रोस्टेट ग्रंथीतील त्रासासह युटीआयची लक्षणे",
    ),
    "Recurrent UTI requiring investigation (cystoscopy or urodynamics)": (
        "बार-बार होने वाला यूटीआई जिसके लिए विशेष जांच की आवश्यकता हो",
        "वारंवार होणारा युटीआय ज्यासाठी सखोल तपासणीची गरज असते",
    ),
    "Uncomplicated UTI (bladder infection)": (
        "साधारण यूटीआई (मूत्राशय का संक्रमण)",
        "अगुंतागुंतीचा युटीआय (मूत्राशयाचा संसर्ग)",
    ),
    "Complicated UTI / Pyelonephritis (kidney infection)": (
        "जटिल यूटीआई / पायलोनेफ्राइटिस (गुर्दे का संक्रमण)",
        "गुंतागुंतीचा युटीआय / पायलोनेफ्रायटिस (मूत्रपिंडाचा संसर्ग)",
    ),
    "Recurrent UTI": (
        "बार-बार होने वाला यूटीआई",
        "वारंवार होणारा युटीआय",
    ),
    "Pregnant women": (
        "गर्भवती महिलाएं",
        "गरोदर महिला",
    ),
    "People who are immunocompromised": (
        "कमजोर प्रतिरक्षा प्रणाली वाले व्यक्ति",
        "कमी प्रतिकारशक्ती असलेल्या व्यक्ती",
    ),
    "People with diabetes": (
        "मधुमेह से पीड़ित लोग",
        "मधुमेह असलेले लोक",
    ),
    "People with kidney stones": (
        "गुर्दे की पथरी वाले लोग",
        "मुतखडा असलेले लोक",
    ),
    "People with chronic kidney disease": (
        "क्रोनिक किडनी रोग (गुर्दे की पुरानी बीमारी) वाले लोग",
        "मूत्रपिंडाचा जुनाट आजार असलेले लोक",
    ),
    "People with urinary tract obstruction or anatomical abnormality": (
        "मूत्र मार्ग में रुकावट या संरचनात्मक असामान्यता वाले लोग",
        "मूत्रमार्गात अडथळा किंवा शारीरिक विकृती असलेले लोक",
    ),
    "People who have recently had a urological procedure": (
        "वे लोग जिनकी हाल ही में कोई यूरोलॉजिकल प्रक्रिया हुई हो",
        "ज्यांच्यावर अलीकडेच मूत्रमार्गाची तपासणी किंवा शस्त्रक्रिया झाली आहे असे लोक",
    ),
}
